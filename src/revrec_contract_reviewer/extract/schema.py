"""The wire format both extractors produce.

Not the domain model. Deliberately.

The domain model in `models/extraction.py` carries resolved citations, parsed
Decimals and dates, and an invariant that an extracted field must have evidence.
None of that can be produced by an extractor, because the extractor is the thing
being checked -- letting it build a Citation directly would be letting it mark
its own homework.

So an extractor's whole vocabulary is the `Claim` below: a value written as a
string, and the words in the document it came from. Grounding turns claims into
domain fields, and only grounding can. The offline rule-based extractor speaks
exactly the same wire format and goes through exactly the same gate, so "the
rules extractor doesn't have to cite anything" is not a shortcut available to it.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from revrec_contract_reviewer.models.extraction import ObligationKind, VariableConsiderationKind


class Claim(BaseModel):
    """A proposed fact and the text it was read from."""

    value: str = Field(
        description=(
            "The value as a plain string. Dates as YYYY-MM-DD, money as digits only with no currency symbol or "
            "thousands separator, booleans as true or false, durations as a whole number of months or days."
        )
    )
    quotes: list[str] = Field(
        description=(
            "Verbatim text from the contract supporting this value. Copy the words exactly as they appear, "
            "including any line breaks. Do not paraphrase, summarise, or join text from separate clauses into "
            "one quote."
        )
    )
    conflicting: bool = Field(
        default=False,
        description=(
            "True when the contract states this in more than one place and the statements disagree. Quote every "
            "conflicting passage and set the value to whichever reading appears to govern."
        ),
    )
    note: str | None = Field(
        default=None,
        description="Only when something needs saying -- most often what the conflict is between.",
    )


class WireObligation(BaseModel):
    label: str = Field(description="The promise as the contract names it.")
    kind: ObligationKind
    quotes: list[str] = Field(
        description=(
            "Verbatim text establishing that this promise exists. Required: an obligation whose existence "
            "cannot be pointed at in the document is dropped."
        )
    )
    stated_price: Claim | None = None
    list_price: Claim | None = Field(
        default=None,
        description="Undiscounted or list rate, only where the document prints one for this item.",
    )
    duration_months: Claim | None = None
    recognition: Claim | None = Field(
        default=None,
        description=(
            "over_time, point_in_time, or undetermined, based on what the contract says about how control "
            "passes. Use undetermined when it says nothing -- do not infer from the product name."
        ),
    )
    integration_language: Claim | None = Field(
        default=None,
        description=(
            "Wording indicating this promise significantly customises, is integrated with, or is highly "
            "interdependent with another. Omit unless the contract actually says something to that effect."
        ),
    )


class WireVariableConsideration(BaseModel):
    kind: VariableConsiderationKind
    description: str
    quotes: list[str] = Field(description="Verbatim text establishing this term.")
    cap: Claim | None = Field(default=None, description="Stated ceiling, where the contract sets one.")
    estimable_from_contract: bool = Field(
        default=False,
        description=(
            "True only if the contract itself fixes both the amount and the event that triggers it. False "
            "whenever the amount depends on something outside the document, such as usage or volumes."
        ),
    )


class WireExtraction(BaseModel):
    """Everything an extractor is allowed to say about a contract."""

    agreement_type: Claim | None = None
    customer: Claim | None = None
    supplier: Claim | None = None
    amends: Claim | None = Field(default=None, description="For an amendment, the agreement being modified.")
    currency: Claim | None = Field(default=None, description="ISO code, e.g. USD.")
    total_fixed_consideration: Claim | None = Field(
        default=None,
        description="Total fixed fees stated in the document. Exclude anything variable.",
    )

    effective_date: Claim | None = None
    stated_term_months: Claim | None = Field(
        default=None,
        description="Duration the document states, whether or not it looks enforceable.",
    )
    auto_renews: Claim | None = None
    termination_for_convenience: Claim | None = Field(
        default=None,
        description="Whether either party may terminate without cause. Mark conflicting if clauses disagree.",
    )
    termination_notice_days: Claim | None = None
    termination_compensation: Claim | None = Field(
        default=None,
        description="What a terminating party owes, quoted rather than characterised.",
    )

    net_days: Claim | None = None
    billing_frequency: Claim | None = None
    upfront_fee: Claim | None = None
    upfront_fee_refundable: Claim | None = None
    payment_spread_months: Claim | None = Field(
        default=None,
        description=(
            "Where the contract sets out an instalment schedule, the number of months from the first payment to "
            "the last. Omit when fees are simply invoiced in advance on normal net terms."
        ),
    )

    renewal_term_months: Claim | None = None
    renewal_price: Claim | None = None
    renewal_described_as_discounted: Claim | None = Field(
        default=None,
        description="Whether the document itself frames the renewal price as a discount.",
    )

    third_party_components: Claim | None = Field(
        default=None,
        description="Language about goods or services supplied by an unaffiliated third party.",
    )

    obligations: list[WireObligation] = []
    variable_consideration: list[WireVariableConsideration] = []
