"""The invariant that makes 'no claim without evidence' structural."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from revrec_contract_reviewer.models.citation import Citation
from revrec_contract_reviewer.models.extraction import ContractExtraction
from revrec_contract_reviewer.models.fields import ExtractedField, FieldStatus


@pytest.fixture
def citation() -> Citation:
    return Citation(page=1, start=0, end=20, quote="payable within thirty")


def test_extracted_field_requires_a_citation():
    with pytest.raises(ValidationError):
        ExtractedField[str](value="USD", status=FieldStatus.EXTRACTED, citations=[])


def test_extracted_field_requires_a_value(citation: Citation):
    with pytest.raises(ValidationError):
        ExtractedField[str](value=None, status=FieldStatus.EXTRACTED, citations=[citation])


def test_absent_field_cannot_smuggle_a_value(citation: Citation):
    with pytest.raises(ValidationError):
        ExtractedField[str](value="USD", status=FieldStatus.ABSENT, citations=[citation])


def test_ambiguous_is_not_known(citation: Citation):
    """Ambiguous carries a value so the memo can show which reading was leant to,
    but nothing downstream may treat it as settled."""
    field = ExtractedField[bool].ambiguous(True, [citation], "two clauses disagree")

    assert field.value is True
    assert not field.is_known


def test_citation_span_must_be_coherent():
    with pytest.raises(ValidationError):
        Citation(page=1, start=40, end=40, quote="x")


def test_citation_excerpt_collapses_and_truncates():
    citation = Citation(page=3, start=0, end=100, quote="a  b\nc " + "long " * 80)

    excerpt = citation.excerpt(30)

    assert excerpt.startswith("a b c")
    assert len(excerpt) <= 30
    assert citation.label() == "p.3"


def test_default_fields_are_not_shared_between_extractions(citation: Citation):
    """Pydantic copies mutable defaults; this pins the behaviour the models rely on."""
    first = ContractExtraction(doc_id="a", extractor="rules")
    second = ContractExtraction(doc_id="b", extractor="rules")

    first.currency = ExtractedField[str].found("USD", [citation])
    first.obligations.append(None)  # type: ignore[arg-type]

    assert second.currency.status is FieldStatus.ABSENT
    assert second.obligations == []
    assert first.term is not second.term
