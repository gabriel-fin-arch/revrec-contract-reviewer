"""Assessment: extraction in, review out. Deterministic, no model involved."""

from __future__ import annotations

from revrec_contract_reviewer.assess.checks import run_checks
from revrec_contract_reviewer.assess.judgments import raise_flags
from revrec_contract_reviewer.models.extraction import ContractExtraction
from revrec_contract_reviewer.models.review import ContractReview

__all__ = ["assess", "raise_flags", "run_checks"]


def assess(extraction: ContractExtraction) -> ContractReview:
    return ContractReview(
        extraction=extraction,
        checks=run_checks(extraction),
        flags=raise_flags(extraction),
    )
