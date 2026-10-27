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


def test_a_conflict_with_one_passage_missing_is_dropped(vantage: ContractDocument):
    """A conflict is an assertion about two places in the document. If only one
    of them is there, nothing shows a disagreement -- and keeping the value
    would be worse, since it may be the reading of the passage that isn't."""
    ground = Grounder(vantage)

    field = ground.field(
        Claim(
            value="false",
            quotes=[
                "Customer may additionally terminate this Agreement for convenience",
                "Neither party may terminate this Agreement before the end of the Term",
            ],
            conflicting=True,
        ),
        lambda raw: raw == "true",
    )

    assert field.status is FieldStatus.ABSENT
    assert not field.citations
    assert ground.dropped == 1


def test_a_missing_claim_is_absent_without_counting_as_a_drop(helix: ContractDocument):
    """Not extracting a field is normal. Only asserting something unsupported is a drop."""
    ground = Grounder(helix)

    field = ground.field(None, parse_str)

    assert field.status is FieldStatus.ABSENT
    assert ground.dropped == 0


def test_a_citation_carries_the_clause_it_falls_in(helix: ContractDocument):
    """The reason segmentation exists. "p.1" tells a reviewer almost nothing;
    "3 Termination" is how they would refer to it themselves."""
    ground = Grounder(helix)

    citation = ground.citations_for(
        ["Either party may terminate this Order Form at any time for convenience"]
    )[0]

    assert citation.clause == "3 Termination"
    assert citation.label() == "3 Termination · p.1"


def test_a_quote_in_the_preamble_is_labelled_as_such(helix: ContractDocument):
    ground = Grounder(helix)

    citation = ground.citations_for(["This Order Form is made on 12 June 2025"])[0]

    assert citation.clause == "Preamble"


def test_a_variable_consideration_term_with_no_evidence_is_dropped(helix: ContractDocument):
    from revrec_contract_reviewer.extract import assemble
    from revrec_contract_reviewer.extract.schema import WireExtraction, WireVariableConsideration
    from revrec_contract_reviewer.models.extraction import VariableConsiderationKind

    invented = WireExtraction(
        variable_consideration=[
            WireVariableConsideration(
                kind=VariableConsiderationKind.VOLUME_REBATE,
                description="A rebate nobody wrote down",
                quotes=["Customer shall receive a rebate of fifteen percent on renewal"],
            )
        ]
    )

    extraction = assemble(helix, invented, extractor="llm", model="stub")

    assert extraction.variable_consideration == []
    assert extraction.dropped_for_no_evidence == 1


def test_a_claim_with_one_real_quote_and_one_invented_is_dropped(helix: ContractDocument):
    """One quote that resolves doesn't carry another that doesn't.

    Here the real quote is the total-fees line and the invented one claims a
    different total; keeping the field on the strength of the real quote would
    put an invented number in the memo with a genuine citation under it.
    """
    ground = Grounder(helix)

    field = ground.field(
        Claim(
            value="792000",
            quotes=["Total committed fees GBP 312,000", "a total contract value of GBP 792,000"],
        ),
        parse_decimal,
    )

    assert field.status is FieldStatus.ABSENT
    assert field.value is None
    assert ground.dropped == 1
    assert "one of the supporting quotes" in field.note


def test_an_obligation_or_term_with_an_invented_quote_among_real_ones_is_dropped(helix: ContractDocument):
    from revrec_contract_reviewer.extract import assemble
    from revrec_contract_reviewer.extract.schema import (
        WireExtraction,
        WireObligation,
        WireVariableConsideration,
    )
    from revrec_contract_reviewer.models.extraction import ObligationKind, VariableConsiderationKind

    real = "Total committed fees GBP 312,000"
    partly_invented = WireExtraction(
        obligations=[
            WireObligation(
                label="An obligation half made up",
                kind=next(iter(ObligationKind)),
                quotes=[real, "Supplier shall provide a dedicated on-site engineer"],
            )
        ],
        variable_consideration=[
            WireVariableConsideration(
                kind=VariableConsiderationKind.VOLUME_REBATE,
                description="A rebate half made up",
                quotes=[real, "Customer shall receive a rebate of fifteen percent on renewal"],
            )
        ],
    )

    extraction = assemble(helix, partly_invented, extractor="llm", model="stub")

    assert extraction.obligations == []
    assert extraction.variable_consideration == []
    assert extraction.dropped_for_no_evidence == 2
