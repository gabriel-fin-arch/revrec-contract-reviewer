"""PDF loading, page offsets, and the footer that would otherwise poison quotes."""

from __future__ import annotations

from pathlib import Path

import pytest

from revrec_contract_reviewer.ingest import load_contract
from revrec_contract_reviewer.models.document import ContractDocument


def test_pages_carry_offsets_into_the_document_text(helix: ContractDocument):
    assert helix.page_count == 2
    for page in helix.pages:
        assert helix.text[page.start : page.end] == page.text


def test_page_lookup_matches_the_page_the_text_is_on(helix: ContractDocument):
    second = helix.pages[1]

    assert helix.page_for_offset(second.start) == 2
    assert helix.page_for_offset(second.end - 1) == 2
    assert helix.page_for_offset(0) == 1


def test_running_footer_is_stripped(helix: ContractDocument):
    """Left in, "Page 2" lands mid-sentence in any clause crossing the break."""
    assert "Page 1" not in helix.text
    assert "Page 2" not in helix.text


def test_missing_file_is_an_error(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_contract(tmp_path / "nope.pdf")


def test_a_pdf_with_no_text_layer_is_refused(tmp_path: Path):
    """Scanned contracts are out of scope, and saying so beats returning an
    empty review that looks like a contract with nothing in it."""
    from reportlab.pdfgen import canvas

    blank = tmp_path / "scanned.pdf"
    page = canvas.Canvas(str(blank))
    page.showPage()
    page.save()

    with pytest.raises(ValueError, match="OCR"):
        load_contract(blank)
