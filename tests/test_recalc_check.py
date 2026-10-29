"""The reconciliation of recalc/rr_recalc.xlsx against the rules extractor (recalc_check.py).

CI runs the check itself, on the accountant's workbook, in its own job. These
tests hold the comparison to what it promises, against a real extraction of
Helix: every row that differs is reported, nothing that agrees is, and a
recorded difference passes only while it still occurs.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook

from revrec_contract_reviewer.extract import ExtractorChoice
from revrec_contract_reviewer.models.extraction import ContractExtraction
from revrec_contract_reviewer.pipeline import review_contract
from revrec_contract_reviewer.recalc_check import (
    Difference,
    Known,
    Row,
    differences,
    judge,
    load_known,
    read_sheet,
    report,
)

HELIX = "nimbus-of-helix"


@pytest.fixture(scope="module")
def helix_extraction(corpus_dir: Path) -> dict[str, ContractExtraction | None]:
    return {HELIX: review_contract(corpus_dir / f"{HELIX}.pdf", ExtractorChoice.RULES).extraction}


def _rows(**changes: object) -> list[Row]:
    """Helix as the contract reads, with any field replaced or, given None, left empty."""
    values: dict[str, object] = {
        "customer": "Helix Robotics Limited",
        "currency": "GBP",
        "effective_date": "2025-06-12",
        "stated_term_months": 24,
        "termination_for_convenience": True,
        "net_days": 30,
        "total_fixed_consideration": 312000,
        "obligation:saas_subscription": 288000,
        "obligation:support": 24000,
    }
    values.update(changes)
    return [Row(HELIX, field, value) for field, value in values.items()]


def _found(rows: list[Row], extractions: dict[str, ContractExtraction | None]) -> list[tuple[str, object, object]]:
    return [(d.field, d.recalc, d.tool) for d in differences(rows, extractions)]


def test_a_reading_that_agrees_with_the_tool_has_no_differences(helix_extraction):
    assert differences(_rows(), helix_extraction) == []


def test_a_field_that_differs_is_reported_with_both_values(helix_extraction):
    assert _found(_rows(net_days=45), helix_extraction) == [("net_days", 45, 30)]


def test_a_number_never_equals_a_bool_and_an_empty_cell_is_not_a_value(helix_extraction):
    found = _found(_rows(termination_for_convenience=1, currency=None), helix_extraction)
    assert found == [("currency", None, "GBP"), ("termination_for_convenience", 1, True)]


def test_an_obligation_on_one_side_only_or_under_another_kind_is_reported(helix_extraction):
    rows = [r for r in _rows() if r.field != "obligation:support"]
    assert _found(rows, helix_extraction) == [("obligation:support", "(no row)", 24000)]

    rows = [r for r in _rows() if r.field != "obligation:support"] + [Row(HELIX, "obligation:implementation", 24000)]
    assert _found(rows, helix_extraction) == [("obligation kind, price 24,000", "implementation", "support")]


def test_a_contract_with_no_pdf_and_a_field_the_check_does_not_know_are_reported(helix_extraction):
    rows = [Row("nimbus-of-nowhere", "currency", "USD"), *_rows(), Row(HELIX, "currency_symbol", "£")]
    assert _found(rows, {**helix_extraction, "nimbus-of-nowhere": None}) == [
        ("(contract)", "in the sheet", "no PDF in corpus/ or corpus/test/"),
        ("currency_symbol", "£", "(not a field this check knows)"),
    ]


def test_a_recorded_difference_passes_only_while_it_still_occurs():
    found = [Difference(HELIX, "net_days", 45, 30)]
    recorded = Known(HELIX, "net_days", "45", "30", issue=12)

    assert judge(found, []).passes is False
    assert judge(found, [recorded]).passes is True
    gone = judge([], [recorded])
    assert gone.passes is False and gone.stale == [recorded]


def test_the_report_marks_what_is_recorded_and_what_is_not():
    rows = _rows()
    found = [Difference(HELIX, "net_days", 45, 30), Difference(HELIX, "currency", "EUR", "GBP")]
    lines = report(rows, judge(found, [Known(HELIX, "net_days", "45", "30", issue=12)]))
    assert f"| {HELIX} | net_days | 45 | 30 | #12 |" in lines
    assert f"| {HELIX} | currency | EUR | GBP | **no** |" in lines
    assert lines[-1].startswith("**Fails:** 1 difference(s) not recorded, 0 recorded")
    assert report(rows, judge([], []))[-1] == "Passes: 9 rows of 1 contracts compared one by one; no differences."


def test_the_known_differences_file_needs_an_issue_for_each_entry(tmp_path):
    path = tmp_path / "known.toml"
    entry = '[[difference]]\ndoc_id = "a"\nfield = "b"\nrecalc = "c"\ntool = "d"\n'
    path.write_text(entry + "issue = 7\n", encoding="utf-8")
    assert load_known(path) == [Known("a", "b", "c", "d", 7)]
    path.write_text(entry, encoding="utf-8")
    with pytest.raises(ValueError, match="no issue"):
        load_known(path)
    assert load_known(tmp_path / "missing.toml") == []


def test_the_sheet_is_read_by_its_fixed_columns(tmp_path):
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "recalc"
    sheet.append(["doc_id", "field", "my_value", "page", "clause"])
    sheet.append([HELIX, "currency", "GBP", 1, "1 Services and Fees"])
    sheet.append([None, None, None, None, None])
    workbook.save(tmp_path / "recalc.xlsx")
    assert read_sheet(tmp_path / "recalc.xlsx") == [Row(HELIX, "currency", "GBP")]
