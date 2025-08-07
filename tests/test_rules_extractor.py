"""The offline extractor, on the corpus it was written for.

These tests pin the specific failures that were expensive to find, not the
happy path -- the happy path is covered by the eval harness, which scores every
field on every contract.
"""

from __future__ import annotations

from revrec_contract_reviewer.extract import ExtractorChoice, extract_contract
from revrec_contract_reviewer.models.document import ContractDocument
from revrec_contract_reviewer.models.fields import FieldStatus


def _extract(document: ContractDocument):
    return extract_contract(document, ExtractorChoice.RULES)


def test_party_names_survive_a_line_break(calderwood_order: ContractDocument):
    """"Calderwood\\nLogistics Group, Inc." lost its first word for a while."""
    extraction = _extract(calderwood_order)

    assert extraction.customer.value == "Calderwood Logistics Group, Inc."
    assert extraction.supplier.value == "Nimbus Analytics, Inc."


def test_the_supplier_is_not_cut_at_its_own_conjunction(helix: ContractDocument):
    """"registered in England and Wales" once produced a supplier called Wales."""
    extraction = _extract(helix)

    assert extraction.supplier.value == "Nimbus Analytics Ltd"


def test_the_order_form_takes_its_own_date_not_the_agreement_it_hangs_off(
    calderwood_order: ContractDocument,
):
    """The subtitle references the MSA's January date before the preamble gives March."""
    extraction = _extract(calderwood_order)

    assert extraction.term.effective_date.value.isoformat() == "2025-03-03"


def test_the_total_row_is_read_and_takes_the_agreed_column(calderwood_order: ContractDocument):
    extraction = _extract(calderwood_order)

    assert str(extraction.total_fixed_consideration.value) == "689000"


def test_list_rates_are_kept_separate_from_the_agreed_price(calderwood_order: ContractDocument):
    subscription = extraction_by_kind(_extract(calderwood_order), "saas_subscription")

    assert str(subscription.stated_price.value) == "540000"
    assert str(subscription.list_price.value) == "612000"


def extraction_by_kind(extraction, kind: str):
    return next(ob for ob in extraction.obligations if ob.kind.value == kind)


def test_prose_amounts_do_not_become_performance_obligations(documents):
    """"the balance of USD 900,000 in four (4) equal annual instalments of USD
    225,000" parses as a fee line and is not a promise to anyone."""
    extraction = _extract(documents["nimbus-of-northgate"])

    labels = [ob.label for ob in extraction.obligations]
    assert labels == [
        "Enterprise Platform subscription (60 months)",
        "Enterprise Support, 60 months",
    ]


def test_contradictory_termination_clauses_produce_ambiguous_not_a_guess(vantage: ContractDocument):
    field = _extract(vantage).term.termination_for_convenience

    assert field.status is FieldStatus.AMBIGUOUS
    assert len(field.citations) == 2


def test_an_express_denial_is_not_read_as_a_grant(pinegrove: ContractDocument):
    """"Neither party may terminate ... for convenience" contains "may terminate
    ... for convenience" verbatim."""
    field = _extract(pinegrove).term.termination_for_convenience

    assert field.status is FieldStatus.EXTRACTED
    assert field.value is False


def test_a_discount_elsewhere_in_the_document_is_not_a_renewal_discount(documents):
    """The Orchid amendment prices itself as preferential and has no renewal at all."""
    extraction = _extract(documents["nimbus-amendment-orchid"])

    assert extraction.renewal.described_as_discounted.status is FieldStatus.ABSENT


def test_the_rules_extractor_never_asserts_without_evidence(documents):
    for document in documents.values():
        extraction = _extract(document)
        for field in (
            extraction.customer,
            extraction.supplier,
            extraction.currency,
            extraction.total_fixed_consideration,
            extraction.term.effective_date,
        ):
            if field.is_known:
                assert field.citations, f"{document.doc_id} asserted a value with no citation"
