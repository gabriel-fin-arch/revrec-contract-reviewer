"""The shape of a synthetic contract, plus the ground truth that goes with it.

Every spec carries a `truth` block. That is what makes the eval harness possible:
the generator knows the answer because it wrote the question. It is also the
harness's main limitation, and docs/evaluation.md says so plainly -- a corpus
this clean measures whether the extractor reads the fields it was pointed at, not
whether it survives a badly scanned 60-page master agreement with a rider taped
to the back.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from revrec_contract_reviewer.models.extraction import AgreementType, ObligationKind
from revrec_contract_reviewer.models.judgment import JudgmentType


@dataclass(frozen=True)
class FeeTable:
    columns: list[str]
    rows: list[list[str]]


@dataclass(frozen=True)
class Section:
    number: str
    heading: str
    paragraphs: list[str]
    table: FeeTable | None = None
    page_break_before: bool = False


@dataclass(frozen=True)
class TruthObligation:
    kind: ObligationKind
    stated_price: Decimal | None


@dataclass(frozen=True)
class ContractTruth:
    """What the contract actually says, as authored.

    `None` means the document genuinely doesn't state it -- so a `None` here is
    scored as correct when the extractor reports the field absent or ambiguous,
    and wrong when it invents a value. Silence is an answer worth grading.
    """

    customer: str
    supplier: str
    agreement_type: AgreementType
    currency: str
    effective_date: date | None
    stated_term_months: int | None
    termination_for_convenience: bool | None
    termination_notice_days: int | None
    net_days: int | None
    total_fixed_consideration: Decimal | None
    obligations: tuple[TruthObligation, ...] = ()
    judgments: tuple[JudgmentType, ...] = ()


@dataclass(frozen=True)
class ContractSpec:
    doc_id: str
    title: str
    subtitle: str
    supplier: str
    customer: str
    preamble: str
    sections: list[Section]
    signature_block: str
    truth: ContractTruth
    commentary: str = field(
        default="",
        metadata={"note": "Why this contract is in the corpus. Ends up in corpus/README.md, not in the PDF."},
    )
