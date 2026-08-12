"""Checks and judgment flags."""

from __future__ import annotations

from decimal import Decimal

import pytest

from revrec_contract_reviewer.assess import assess, raise_flags, run_checks
from revrec_contract_reviewer.extract import ExtractorChoice, extract_contract
from revrec_contract_reviewer.models.citation import Citation
from revrec_contract_reviewer.models.extraction import (
    AgreementType,
    ContractExtraction,
    ObligationKind,
    PerformanceObligation,
)
from revrec_contract_reviewer.models.fields import ExtractedField
from revrec_contract_reviewer.models.judgment import JudgmentType
from revrec_contract_reviewer.models.review import CheckOutcome


@pytest.fixture
def citation() -> Citation:
    return Citation(page=1, start=0, end=24, quote="Total committed fees GBP")


def _priced(kind: ObligationKind, amount: str, citation: Citation) -> PerformanceObligation:
    return PerformanceObligation(
        label=f"{kind.value} line",
        kind=kind,
        evidence=[citation],
        stated_price=ExtractedField[Decimal].found(Decimal(amount), [citation]),
    )


def _check(extraction: ContractExtraction, name: str):
    return next(check for check in run_checks(extraction) if check.name.startswith(name))


def test_footing_passes_when_the_schedule_adds_up(citation: Citation):
    extraction = ContractExtraction(
        doc_id="x",
        extractor="rules",
        total_fixed_consideration=ExtractedField[Decimal].found(Decimal("312000"), [citation]),
        obligations=[
            _priced(ObligationKind.SAAS_SUBSCRIPTION, "288000", citation),
            _priced(ObligationKind.SUPPORT, "24000", citation),
        ],
    )

    assert _check(extraction, "Fee schedule").outcome is CheckOutcome.PASSED


def test_footing_fails_on_any_difference_at_all(citation: Citation):
    """No tolerance: both numbers are printed in the same table, in the same
    currency. A difference means a line was misread, not that a rate moved."""
    extraction = ContractExtraction(
        doc_id="x",
        extractor="rules",
        total_fixed_consideration=ExtractedField[Decimal].found(Decimal("312000.01"), [citation]),
        obligations=[_priced(ObligationKind.SAAS_SUBSCRIPTION, "312000", citation)],
    )

    check = _check(extraction, "Fee schedule")
    assert check.outcome is CheckOutcome.FAILED
    assert "incomplete" in check.detail


def test_footing_is_not_applicable_without_a_stated_total(citation: Citation):
    extraction = ContractExtraction(
        doc_id="x",
        extractor="rules",
        obligations=[_priced(ObligationKind.SAAS_SUBSCRIPTION, "312000", citation)],
    )

    assert _check(extraction, "Fee schedule").outcome is CheckOutcome.NOT_APPLICABLE


def test_a_missing_currency_fails_its_check(citation: Citation):
    extraction = ContractExtraction(doc_id="x", extractor="rules")

    assert _check(extraction, "Currency").outcome is CheckOutcome.FAILED


def test_one_obligation_raises_no_allocation_question(citation: Citation):
    """Nothing to allocate. This is why the quiet contract stays quiet."""
    extraction = ContractExtraction(
        doc_id="x",
        extractor="rules",
        obligations=[_priced(ObligationKind.SAAS_SUBSCRIPTION, "14400", citation)],
    )

    assert raise_flags(extraction) == []


def test_two_obligations_raise_the_ssp_question(citation: Citation):
    extraction = ContractExtraction(
        doc_id="x",
        extractor="rules",
        obligations=[
            _priced(ObligationKind.SAAS_SUBSCRIPTION, "288000", citation),
            _priced(ObligationKind.SUPPORT, "24000", citation),
        ],
    )

    assert [flag.judgment_type for flag in raise_flags(extraction)] == [JudgmentType.SSP_NOT_OBSERVABLE]


def test_an_express_denial_of_termination_raises_nothing(citation: Citation):
    extraction = ContractExtraction(doc_id="x", extractor="rules")
    extraction.term.termination_for_convenience = ExtractedField[bool].found(False, [citation])

    assert raise_flags(extraction) == []


def test_an_ambiguous_termination_right_still_raises_the_term_question(citation: Citation):
    extraction = ContractExtraction(doc_id="x", extractor="rules")
    extraction.term.termination_for_convenience = ExtractedField[bool].ambiguous(
        True, [citation], "clauses disagree"
    )

    flags = raise_flags(extraction)
    assert flags[0].judgment_type is JudgmentType.ENFORCEABLE_TERM
    assert "disagree" in flags[0].trigger


def test_payment_inside_the_practical_expedient_raises_no_financing_question(citation: Citation):
    extraction = ContractExtraction(doc_id="x", extractor="rules")
    extraction.payment.payment_spread_months = ExtractedField[int].found(12, [citation])

    assert raise_flags(extraction) == []


def test_payment_beyond_a_year_does(citation: Citation):
    extraction = ContractExtraction(doc_id="x", extractor="rules")
    extraction.payment.payment_spread_months = ExtractedField[int].found(48, [citation])

    assert raise_flags(extraction)[0].judgment_type is JudgmentType.SIGNIFICANT_FINANCING


def test_an_amendment_cannot_be_assessed_alone(citation: Citation):
    extraction = ContractExtraction(
        doc_id="x",
        extractor="rules",
        agreement_type=ExtractedField[AgreementType].found(AgreementType.AMENDMENT, [citation]),
    )

    assert raise_flags(extraction)[0].judgment_type is JudgmentType.CONTRACT_MODIFICATION


def test_flags_come_back_in_the_order_of_the_five_step_model(citation: Citation):
    extraction = ContractExtraction(
        doc_id="x",
        extractor="rules",
        agreement_type=ExtractedField[AgreementType].found(AgreementType.AMENDMENT, [citation]),
        obligations=[
            _priced(ObligationKind.SAAS_SUBSCRIPTION, "288000", citation),
            _priced(ObligationKind.SUPPORT, "24000", citation),
        ],
    )
    extraction.payment.payment_spread_months = ExtractedField[int].found(48, [citation])

    steps = [flag.step for flag in raise_flags(extraction)]

    assert steps == sorted(steps)
    assert steps[0] == 1


def test_every_flag_carries_a_standing_reason_it_is_not_automated(citation: Citation):
    extraction = ContractExtraction(
        doc_id="x",
        extractor="rules",
        obligations=[
            _priced(ObligationKind.SAAS_SUBSCRIPTION, "288000", citation),
            _priced(ObligationKind.THIRD_PARTY_RESALE, "88000", citation),
        ],
    )

    for flag in raise_flags(extraction):
        assert flag.why_a_human
        assert flag.evidence


def test_the_quiet_contract_stays_quiet(pinegrove):
    """A reviewer that flags something on every contract stops being read."""
    review = assess(extract_contract(pinegrove, ExtractorChoice.RULES))

    assert review.flags == []
    assert review.failed_checks() == []
    assert not review.needs_review()
