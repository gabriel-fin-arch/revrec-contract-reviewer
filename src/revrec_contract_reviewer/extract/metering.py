"""What a model call cost, how long it took, and the prices it was costed at.

A published model number needs more than the model's name: the effort it ran
at, the tokens it used, what that cost and how long it took. The extractor
records one CallRecord per call, the eval harness keeps them with the saved
run, and `revrec estimate` uses the same prices to say what a run would cost
before anyone makes it.

Prices are Anthropic's published first-party rates in US dollars per million
tokens, as the pricing page stated them on PRICES_AS_OF. They change; a run
records the date of the prices it was costed at, and a model missing from the
table is costed as unknown rather than guessed.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from pydantic import BaseModel

PRICES_AS_OF = "2026-10-18"
PRICES_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing"


@dataclass(frozen=True)
class Price:
    """US dollars per million tokens."""

    input: Decimal
    cache_write: Decimal  # five-minute cache, which is what the extractor's cache_control asks for
    cache_read: Decimal
    output: Decimal


PRICES: dict[str, Price] = {
    "claude-opus-5-5": Price(Decimal("4"), Decimal("5"), Decimal("0.20"), Decimal("20")),
    "claude-opus-5": Price(Decimal("5"), Decimal("6.25"), Decimal("0.50"), Decimal("25")),
}

MILLION = Decimal(1_000_000)


def cost_usd(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_creation_input_tokens: int = 0,
    cache_read_input_tokens: int = 0,
) -> Decimal | None:
    """The cost of one call at PRICES, or None for a model the table doesn't have.

    `input_tokens` is the uncached input only, as the API reports it; cache
    writes and reads are priced separately. Thinking is billed as output and
    is already in `output_tokens`.
    """
    price = PRICES.get(model)
    if price is None:
        return None
    total = (
        input_tokens * price.input
        + cache_creation_input_tokens * price.cache_write
        + cache_read_input_tokens * price.cache_read
        + output_tokens * price.output
    )
    return (total / MILLION).quantize(Decimal("0.000001"))


class CallRecord(BaseModel):
    """One model call, as the API reported it."""

    model: str
    effort: str
    stop_reason: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    seconds: float
    cost_usd: Decimal | None = None
    prices_as_of: str = PRICES_AS_OF

    @classmethod
    def from_response(cls, response: object, model: str, effort: str, seconds: float) -> CallRecord:
        usage = getattr(response, "usage", None)

        def tokens(name: str) -> int:
            return int(getattr(usage, name, 0) or 0)

        input_tokens = tokens("input_tokens")
        output_tokens = tokens("output_tokens")
        cache_written = tokens("cache_creation_input_tokens")
        cache_read = tokens("cache_read_input_tokens")
        return cls(
            model=model,
            effort=effort,
            stop_reason=getattr(response, "stop_reason", None),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_creation_input_tokens=cache_written,
            cache_read_input_tokens=cache_read,
            seconds=round(seconds, 3),
            cost_usd=(
                cost_usd(model, input_tokens, output_tokens, cache_written, cache_read) if usage is not None else None
            ),
        )
