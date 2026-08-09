"""Clause segmentation."""

from __future__ import annotations

from revrec_contract_reviewer.models.document import ContractDocument
from revrec_contract_reviewer.segment import find_clause, segment


def test_clauses_are_found_in_document_order(helix: ContractDocument):
    headings = [clause.heading for clause in helix.clauses]

    assert headings[0] == "Preamble"
    assert "Termination" in headings
    assert [clause.start for clause in helix.clauses] == sorted(clause.start for clause in helix.clauses)


def test_the_preamble_is_kept(helix: ContractDocument):
    """The effective date and the parties live before clause 1."""
    preamble = helix.clauses[0]

    assert preamble.number == ""
    assert "12 June 2025" in preamble.text


def test_clause_text_slices_back_out_of_the_document(helix: ContractDocument):
    for clause in helix.clauses:
        assert helix.text[clause.start : clause.end] == clause.text


def test_a_decimal_in_prose_is_not_mistaken_for_a_clause_number():
    document = ContractDocument(
        doc_id="synthetic",
        source_path="synthetic.pdf",
        text="1. Scope\nThe parties agree.\n2.5 million events were processed last year.\n2. Fees\nPay up.",
        pages=[{"number": 1, "start": 0, "end": 92, "text": "x"}],
    )

    numbers = [clause.number for clause in segment(document)]

    assert numbers == ["1", "2"]


def test_find_clause_matches_headings_not_bodies(helix: ContractDocument):
    """Matching bodies would return clause 1 for almost any keyword."""
    assert find_clause(helix, "termination").heading == "Termination"
    assert find_clause(helix, "indemnity") is None


def test_clause_reference_prefers_number_and_heading(helix: ContractDocument):
    termination = find_clause(helix, "termination")

    assert termination.reference() == "3 Termination"
