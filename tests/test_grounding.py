"""The gate. These tests are the ones that matter most in the whole suite."""

from __future__ import annotations

from revrec_contract_reviewer.extract.grounding import Grounder
from revrec_contract_reviewer.extract.schema import Claim
from revrec_contract_reviewer.extract.values import parse_decimal, parse_int, parse_str
from revrec_contract_reviewer.models.document import ContractDocument
from revrec_contract_reviewer.models.fields import FieldStatus


def test_a_claim_whose_quote_is_not_in_the_document_is_dropped(helix: ContractDocument):
    ground = Grounder(helix)

    field = ground.field(
        Claim(value="90", quotes=["either party may terminate on ninety (90) days notice"]),
        parse_int,
    )

    assert field.status is FieldStatus.ABSENT
    assert field.value is None
    assert ground.dropped == 1
    assert "could not be located" in field.note


def test_a_grounded_claim_becomes_an_extracted_field(helix: ContractDocument):
    ground = Grounder(helix)

    field = ground.field(
        Claim(value="312000", quotes=["Total committed fees GBP 312,000"]),
        parse_decimal,
    )

    assert field.status is FieldStatus.EXTRACTED
    assert str(field.value) == "312000"
    assert field.citations[0].page == 1
    assert ground.dropped == 0


def test_grounding_does_not_check_whether_the_value_is_right(helix: ContractDocument):
    """A real quote with a misread number gets through. That failure mode is the
    eval harness's job -- conflating it with invention would let a hallucinated
    citation hide inside an accuracy percentage."""
    ground = Grounder(helix)

    field = ground.field(
        Claim(value="999999", quotes=["Total committed fees GBP 312,000"]),
        parse_decimal,
    )

    assert field.is_known
    assert str(field.value) == "999999"


def test_an_unparseable_value_is_dropped_too(helix: ContractDocument):
    ground = Grounder(helix)

    field = ground.field(
        Claim(value="about three hundred thousand", quotes=["Total committed fees GBP 312,000"]),
        parse_decimal,
    )

    assert field.status is FieldStatus.ABSENT
    assert ground.dropped == 1


def test_a_quote_too_short_to_identify_anything_is_refused(helix: ContractDocument):
    """"30" grounds against forty places in a contract, which is evidence of nothing."""
    ground = Grounder(helix)

    field = ground.field(Claim(value="30", quotes=["30"]), parse_int)

    assert field.status is FieldStatus.ABSENT
    assert ground.dropped == 1


def test_conflicting_claims_become_ambiguous_with_both_quotes(vantage: ContractDocument):
    ground = Grounder(vantage)

    field = ground.field(
        Claim(
            value="true",
            quotes=[
                "Customer may additionally terminate this Agreement for convenience",
                "no right of termination for convenience is granted under this Agreement",
            ],
            conflicting=True,
            note="the clauses disagree",
        ),
        lambda raw: raw == "true",
    )

    assert field.status is FieldStatus.AMBIGUOUS
    assert not field.is_known
    assert len(field.citations) == 2


def test_a_missing_claim_is_absent_without_counting_as_a_drop(helix: ContractDocument):
    """Not extracting a field is normal. Only asserting something unsupported is a drop."""
    ground = Grounder(helix)

    field = ground.field(None, parse_str)

    assert field.status is FieldStatus.ABSENT
    assert ground.dropped == 0
