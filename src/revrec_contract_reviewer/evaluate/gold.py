"""The gold set.

Derived from the corpus specs, because the generator knows the answer -- it
wrote the question. That is legitimate for a synthetic corpus and it is also the
harness's main limitation, which docs/evaluation.md states rather than buries.

It is written to `evals/gold/` as JSON and committed rather than computed on the
fly. Two reasons. A gold set that regenerates itself from the same code being
evaluated can drift silently: change how a spec is authored and the "truth"
moves with it, and every score stays flat while the thing being measured
changes underneath. And a committed JSON file can be read in a pull request by
someone who doesn't want to read Python.

`null` means the contract genuinely does not state it. Those entries are scored:
inventing a value where the document is silent is a failure with its own name.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from revrec_contract_reviewer.corpus.library import CORPUS
from revrec_contract_reviewer.corpus.spec import ContractSpec
from revrec_contract_reviewer.fileio import write_lf

# The scalar fields the harness scores. Kept as an explicit list rather than
# introspected off the model: adding a field to the extraction should not
# silently change what the published accuracy number means.
#
# TODO: billing_frequency, the renewal terms and per-obligation duration show up
# in the memo but aren't in here, so their accuracy rests on a handful of unit
# tests instead of being measured across the corpus. Adding them means adding
# them to ContractTruth for all twelve, which is an afternoon of careful reading
# I haven't done yet.
SCORED_FIELDS = (
    "customer",
    "supplier",
    "agreement_type",
    "currency",
    "effective_date",
    "stated_term_months",
    "termination_for_convenience",
    "termination_notice_days",
    "net_days",
    "total_fixed_consideration",
)


class GoldObligation(BaseModel):
    kind: str
    stated_price: str | None


class GoldRecord(BaseModel):
    doc_id: str
    fields: dict[str, Any]
    obligations: list[GoldObligation]
    judgments: list[str]


def _record_for(spec: ContractSpec) -> GoldRecord:
    truth = spec.truth
    return GoldRecord(
        doc_id=spec.doc_id,
        fields={
            "customer": truth.customer,
            "supplier": truth.supplier,
            "agreement_type": truth.agreement_type.value,
            "currency": truth.currency,
            "effective_date": truth.effective_date.isoformat() if truth.effective_date else None,
            "stated_term_months": truth.stated_term_months,
            "termination_for_convenience": truth.termination_for_convenience,
            "termination_notice_days": truth.termination_notice_days,
            "net_days": truth.net_days,
            "total_fixed_consideration": (
                str(truth.total_fixed_consideration) if truth.total_fixed_consideration is not None else None
            ),
        },
        obligations=[
            GoldObligation(
                kind=obligation.kind.value,
                stated_price=str(obligation.stated_price) if obligation.stated_price is not None else None,
            )
            for obligation in truth.obligations
        ],
        judgments=sorted(judgment.value for judgment in truth.judgments),
    )


def build_gold() -> list[GoldRecord]:
    return [_record_for(spec) for spec in CORPUS]


def write_gold(out_dir: Path) -> list[Path]:
    """Write one JSON file per contract."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for record in build_gold():
        target = write_lf(
            out_dir / f"{record.doc_id}.json",
            json.dumps(record.model_dump(), indent=2, ensure_ascii=False) + "\n",
        )
        written.append(target)
    return written


def load_gold(gold_dir: Path) -> dict[str, GoldRecord]:
    """Read the committed gold set from disk.

    Reads the files rather than calling build_gold() so that the harness scores
    against what is in the repository, not against what the current code would
    generate. If someone edits a spec and forgets to refresh the gold set, that
    should show up as a failing score, not as a silent redefinition of correct.
    """
    records = {}
    for path in sorted(gold_dir.glob("*.json")):
        record = GoldRecord.model_validate_json(path.read_text(encoding="utf-8"))
        records[record.doc_id] = record
    if not records:
        raise FileNotFoundError(f"no gold records in {gold_dir}; run `revrec build-gold` first")
    return records
