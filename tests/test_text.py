"""Grounding's search layer -- the part that has to say no."""

from __future__ import annotations

from revrec_contract_reviewer.ingest.text import NormalizedText


def test_quote_spanning_a_line_break_is_found():
    raw = "terminate this Order Form at any time for convenience by giving sixty\n(60) days' written notice"
    view = NormalizedText(raw)

    spans = view.find_all("for convenience by giving sixty (60) days' written notice")

    assert len(spans) == 1
    start, end = spans[0]
    assert raw[start:end].endswith("written notice")
    assert "\n" in raw[start:end]


def test_case_and_typographic_variants_fold():
    """Each fold is one character onto one character, so the offset map stays
    one-to-one -- an em dash becomes a single hyphen, not two."""
    view = NormalizedText("The Customer’s notice period — thirty days.")

    assert view.contains("the customer's notice period - thirty days")


def test_a_quote_that_is_not_there_is_not_found():
    view = NormalizedText("Either party may terminate for material breach.")

    assert view.find_all("either party may terminate for convenience") == []


def test_near_misses_are_rejected_rather_than_tolerated():
    """No edit distance anywhere. One wrong word is a different sentence."""
    view = NormalizedText("payable within thirty (30) days of the invoice date")

    assert not view.contains("payable within sixty (60) days of the invoice date")


def test_offsets_point_into_the_raw_text():
    raw = "  Clause one.\n\n   Clause two says   forty (40) days.  "
    view = NormalizedText(raw)

    start, end = view.find_all("clause two says forty (40) days")[0]

    assert raw[start:end] == "Clause two says   forty (40) days"


def test_repeated_quotes_return_every_occurrence():
    """Ambiguity detection depends on seeing both places, not the first."""
    view = NormalizedText("no right of termination. Later: no right of termination.")

    assert len(view.find_all("no right of termination")) == 2


def test_case_preserving_view_still_collapses_whitespace():
    view = NormalizedText("Nimbus Analytics\nLtd", fold_case=False)

    assert view.text == "Nimbus Analytics Ltd"
    assert not view.contains("nimbus analytics ltd")
