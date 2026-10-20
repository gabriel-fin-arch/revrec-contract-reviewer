"""The reviewer worklist as a workbook: every open item in a run, one row each.

A revenue team works its open items in a spreadsheet, not in twelve HTML
memos. This puts every judgment and every failed check from a run on one
sheet, in the order the index puts the contracts, with the words each item
was raised on, their clause and page, and blank columns for the reviewer's
conclusion. Files that could not be read come first, as they do in the
index. A second sheet lists every contract, open items or not, so a clean
one is visibly clean rather than missing.

Nothing here is decided. The workbook is where the reviewer writes the
decision down.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

from revrec_contract_reviewer.models.citation import Citation
from revrec_contract_reviewer.models.review import ContractReview
from revrec_contract_reviewer.report.memo import attention_order

WORKLIST_COLUMNS = (
    "contract",
    "kind",
    "step",
    "item",
    "question or result",
    "raised by",
    "evidence",
    "affects",
    "why it needs a person",
    "reviewer conclusion",
    "reviewer",
    "date",
)
CONTRACT_COLUMNS = ("contract", "judgments", "failed checks", "needs a reviewer", "extractor", "memo")

# Wide enough to read a question without opening the cell; the evidence and
# the reasons wrap.
WIDTHS = {
    "contract": 26,
    "kind": 13,
    "step": 6,
    "item": 28,
    "question or result": 60,
    "raised by": 50,
    "evidence": 70,
    "affects": 30,
    "why it needs a person": 60,
    "reviewer conclusion": 40,
    "reviewer": 16,
    "date": 12,
}


def _evidence(citations: list[Citation]) -> str:
    """Each citation as 'clause · p.N: the words', one per line."""
    return "\n".join(f"{citation.label()}: {citation.excerpt()}" for citation in citations)


def worklist_rows(reviews: list[ContractReview], unreadable: Sequence[tuple[str, str]] = ()) -> list[list[str]]:
    """The open items, one row each, in WORKLIST_COLUMNS order, without the header."""
    rows: list[list[str]] = []
    for name, reason in unreadable:
        rows.append([name, "unreadable", "", "could not be read", reason, "", "", "", "", "", "", ""])
    for review in attention_order(reviews):
        for check in review.failed_checks():
            rows.append(
                [
                    review.doc_id,
                    "failed check",
                    "",
                    check.name,
                    check.detail,
                    "",
                    _evidence(check.evidence),
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )
        for flag in review.flags_in_review_order():
            rows.append(
                [
                    review.doc_id,
                    "judgment",
                    str(flag.step),
                    flag.judgment_type.value.replace("_", " "),
                    flag.question,
                    flag.trigger,
                    _evidence(flag.evidence),
                    "; ".join(flag.affects),
                    flag.why_a_human,
                    "",
                    "",
                    "",
                ]
            )
    return rows


def contract_rows(reviews: list[ContractReview]) -> list[list[object]]:
    return [
        [
            review.doc_id,
            len(review.flags),
            len(review.failed_checks()),
            "yes" if review.needs_review() else "no",
            review.extraction.extractor + (f" ({review.extraction.model})" if review.extraction.model else ""),
            f"{review.doc_id}.html",
        ]
        for review in attention_order(reviews)
    ]


def write_worklist(reviews: list[ContractReview], out_dir: Path, unreadable: Sequence[tuple[str, str]] = ()) -> Path:
    """Write worklist.xlsx into out_dir and return its path."""
    workbook = Workbook()
    for blank in list(workbook.worksheets):
        workbook.remove(blank)

    items = workbook.create_sheet("open items")
    items.append(list(WORKLIST_COLUMNS))
    for row in worklist_rows(reviews, unreadable):
        items.append(row)
    contracts = workbook.create_sheet("contracts")
    contracts.append(list(CONTRACT_COLUMNS))
    for contract_row in contract_rows(reviews):
        contracts.append(contract_row)

    for sheet in (items, contracts):
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        sheet.freeze_panes = "B2"
        for column_cells in sheet.iter_cols():
            header = str(column_cells[0].value)
            sheet.column_dimensions[column_cells[0].column_letter].width = WIDTHS.get(header, 18)
            for cell in column_cells[1:]:
                cell.alignment = Alignment(wrap_text=True, vertical="top")

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "worklist.xlsx"
    workbook.save(path)
    return path
