"""What a model run would cost, worked out before anyone makes it.

No API call: the token counts are estimated from character counts, at
CHARS_PER_TOKEN, which errs high for English prose and JSON. Input is what
every call sends, the instructions and the output schema plus one contract.
Output has a floor and a ceiling. The floor is the claims alone, sized from
the rules run of the same set, with no thinking at all. The ceiling is
max_tokens, which no call can pass, so it holds whatever the model thinks.
Both bounds price the input as uncached, though from the second call on the
instructions come from the cache at a fraction of the price.

A count with `messages.count_tokens` would be exact for the input, and it
is an API call: it waits for approval like any other.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from revrec_contract_reviewer.evaluate.runs import SavedRun
from revrec_contract_reviewer.extract import llm
from revrec_contract_reviewer.extract.metering import MILLION, PRICES, PRICES_AS_OF
from revrec_contract_reviewer.extract.schema import WireExtraction
from revrec_contract_reviewer.ingest import load_contract
from revrec_contract_reviewer.segment import segmented

CHARS_PER_TOKEN = 3


@dataclass(frozen=True)
class Estimate:
    model: str
    contracts: int
    input_tokens: int
    output_floor_tokens: int
    output_ceiling_tokens: int
    cost_floor_usd: Decimal
    cost_ceiling_usd: Decimal

    def lines(self, label: str) -> list[str]:
        return [
            f"Estimate for {self.model} on the {label} ({self.contracts} contracts), without calling the API:",
            f"  input   about {self.input_tokens:,} tokens: instructions, schema and contract text, "
            f"at {CHARS_PER_TOKEN} characters a token",
            f"  output  {self.output_floor_tokens:,} to {self.output_ceiling_tokens:,} tokens: the claims alone, "
            f"up to max_tokens ({llm.MAX_TOKENS:,}) on every call",
            f"  cost    USD {self.cost_floor_usd:.2f} to {self.cost_ceiling_usd:.2f} at the prices of {PRICES_AS_OF}",
        ]


def _tokens(characters: int) -> int:
    return -(-characters // CHARS_PER_TOKEN)


def estimate_run(corpus_dir: Path, model: str, rules_claims: Path | None = None) -> Estimate:
    """Bounds on the tokens and cost of one model run over the PDFs in corpus_dir."""
    price = PRICES.get(model)
    if price is None:
        raise ValueError(f"no published price for {model} in extract/metering.py")

    fixed = len(llm.SYSTEM) + len(json.dumps(WireExtraction.model_json_schema()))
    paths = sorted(corpus_dir.glob("*.pdf"))
    if not paths:
        raise FileNotFoundError(f"no PDFs in {corpus_dir}")
    input_tokens = 0
    for path in paths:
        document = segmented(load_contract(path))
        prompt = llm.USER_TEMPLATE.format(doc_id=document.doc_id, body=llm._with_page_markers(document))
        input_tokens += _tokens(fixed + len(prompt))

    floor = 0
    if rules_claims is not None and rules_claims.is_file():
        run = SavedRun.model_validate_json(rules_claims.read_text(encoding="utf-8"))
        floor = sum(_tokens(len(contract.claims.model_dump_json())) for contract in run.contracts)
    ceiling = len(paths) * llm.MAX_TOKENS

    def cost(output_tokens: int) -> Decimal:
        return (input_tokens * price.input + output_tokens * price.output) / MILLION

    return Estimate(
        model=model,
        contracts=len(paths),
        input_tokens=input_tokens,
        output_floor_tokens=floor,
        output_ceiling_tokens=ceiling,
        cost_floor_usd=cost(floor),
        cost_ceiling_usd=cost(ceiling),
    )
