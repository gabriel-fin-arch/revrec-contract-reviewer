"""Deterministic checks: the things a reviewer ticks off without thinking.

Every check here has a right answer that follows from the extraction alone. No
model is consulted and none of the `detail` strings are generated: they are
written by the check that failed, from the numbers that made it fail.

The footing check is the one that earns its place. Whatever else a reviewer
believes about a contract, the fee schedule adds up or it doesn't, and when it
doesn't the cause is almost always that the extraction missed a line, not that
the contract is wrong. It is the cheapest available signal that everything below
it in the memo is built on an incomplete reading.
"""

from __future__ import annotations

from decimal import Decimal

from revrec_contract_reviewer.models.extraction import ContractExtraction, RecognitionPattern
from revrec_contract_reviewer.models.review import CheckOutcome, ReviewCheck

# The fee schedule is compared to the stated total at the cent. There is no
# tolerance because there is nothing for a tolerance to absorb: both numbers are
# printed in the same table, in the same currency, and a difference of any size
# means a line was misread. This is not an intercompany balance translated at
# two different rates. It is arithmetic on one page.
FOOTING_TOLERANCE = Decimal("0")


def _footing(extraction: ContractExtraction) -> ReviewCheck:
    total = extraction.total_fixed_consideration
    priced = extraction.priced_obligations()

    if not total.is_known or not priced:
        return ReviewCheck(
            name="Fee schedule foots to the stated total",
            outcome=CheckOutcome.NOT_APPLICABLE,
            detail=(
                "No stated total, or no priced obligations, to compare. Common in master agreements and in "
                "documents that set out fees in prose rather than a schedule."
            ),
        )

    summed = extraction.allocated_total()
    difference = summed - total.value
    evidence = list(total.citations)

    if abs(difference) <= FOOTING_TOLERANCE:
        return ReviewCheck(
            name="Fee schedule foots to the stated total",
            outcome=CheckOutcome.PASSED,
            detail=f"{len(priced)} priced items sum to {summed}, matching the stated total.",
            evidence=evidence,
        )

    return ReviewCheck(
        name="Fee schedule foots to the stated total",
        outcome=CheckOutcome.FAILED,
        detail=(
            f"{len(priced)} priced items sum to {summed} against a stated total of {total.value}, "
            f"a difference of {difference}. Most likely a line the extraction did not pick up; until it is "
            f"reconciled, treat the obligation list below as incomplete."
        ),
        evidence=evidence,
    )


def _parties(extraction: ContractExtraction) -> ReviewCheck:
    missing = [
        label
        for label, field in (("customer", extraction.customer), ("supplier", extraction.supplier))
        if not field.is_known
    ]
    if not missing:
        return ReviewCheck(
            name="Both parties identified",
            outcome=CheckOutcome.PASSED,
            detail=f"{extraction.supplier.value} contracting with {extraction.customer.value}.",
            evidence=[*extraction.supplier.citations[:1], *extraction.customer.citations[:1]],
        )
    return ReviewCheck(
        name="Both parties identified",
        outcome=CheckOutcome.FAILED,
        detail=f"Could not identify the {' and the '.join(missing)} from the document.",
    )


def _effective_date(extraction: ContractExtraction) -> ReviewCheck:
    field = extraction.term.effective_date
    if field.is_known:
        return ReviewCheck(
            name="Effective date identified",
            outcome=CheckOutcome.PASSED,
            detail=f"Effective {field.value.isoformat()}.",
            evidence=field.citations[:1],
        )
    return ReviewCheck(
        name="Effective date identified",
        outcome=CheckOutcome.FAILED,
        detail=(
            "No effective date could be read from the document. Contract inception drives the whole model: "
            "the enforceable term, the discount rate for any financing component, and the period the "
            "obligations sit in."
        ),
    )


def _currency(extraction: ContractExtraction) -> ReviewCheck:
    if extraction.currency.is_known:
        return ReviewCheck(
            name="Currency identified",
            outcome=CheckOutcome.PASSED,
            detail=f"Amounts are stated in {extraction.currency.value}.",
            evidence=extraction.currency.citations[:1],
        )
    return ReviewCheck(
        name="Currency identified",
        outcome=CheckOutcome.FAILED,
        detail=(
            "No currency code found. Every amount in this review is therefore a bare number, and a group "
            "reporting in one currency cannot consolidate a bare number."
        ),
    )


def _obligations_priced(extraction: ContractExtraction) -> ReviewCheck:
    if not extraction.obligations:
        return ReviewCheck(
            name="Every obligation carries a price",
            outcome=CheckOutcome.NOT_APPLICABLE,
            detail="No performance obligations were identified in this document.",
        )

    unpriced = [ob.label for ob in extraction.obligations if not ob.stated_price.is_known]
    if not unpriced:
        return ReviewCheck(
            name="Every obligation carries a price",
            outcome=CheckOutcome.PASSED,
            detail=f"All {len(extraction.obligations)} identified obligations have a stated price.",
        )
    return ReviewCheck(
        name="Every obligation carries a price",
        outcome=CheckOutcome.FAILED,
        detail=(
            f"No stated price for: {', '.join(unpriced)}. An obligation with no price still has to be "
            f"allocated to, so this is a gap in the allocation rather than an item to leave out of it."
        ),
    )


def _recognition_pattern(extraction: ContractExtraction) -> ReviewCheck:
    if not extraction.obligations:
        return ReviewCheck(
            name="Recognition pattern evidenced for each obligation",
            outcome=CheckOutcome.NOT_APPLICABLE,
            detail="No performance obligations were identified in this document.",
        )

    # Three outcomes, because there are genuinely three situations, and an
    # earlier two-way version collapsed two of them and reported green on all
    # twelve contracts while every obligation in them was undetermined.
    #
    #   read, and the contract says      -> passed
    #   read, and the contract is silent -> failed: a finding about the drafting
    #   not read at all                  -> not applicable
    #
    # The third is the one that matters. UNDETERMINED is an assertion about the
    # contract; absence is an assertion about nothing. Reporting a failure for
    # absence would be blaming the document for what the extractor didn't do.
    silent = [
        ob.label
        for ob in extraction.obligations
        if ob.recognition.is_known and ob.recognition.value is RecognitionPattern.UNDETERMINED
    ]
    unread = [ob.label for ob in extraction.obligations if not ob.recognition.is_known]

    if silent:
        return ReviewCheck(
            name="Recognition pattern evidenced for each obligation",
            outcome=CheckOutcome.FAILED,
            detail=(
                f"The contract says nothing about how control transfers for: {', '.join(silent)}. "
                f"That is a finding about the drafting rather than a fault in the reading, but it means "
                f"the local team's over-time or point-in-time conclusion is not supported by this document."
            ),
        )
    if unread:
        return ReviewCheck(
            name="Recognition pattern evidenced for each obligation",
            outcome=CheckOutcome.NOT_APPLICABLE,
            detail=(
                f"No reading of how control transfers was attempted for: {', '.join(unread)}. The offline "
                f"extractor does not attempt it; run the model extractor to get an answer here."
            ),
        )
    return ReviewCheck(
        name="Recognition pattern evidenced for each obligation",
        outcome=CheckOutcome.PASSED,
        detail="Each obligation has language in the contract bearing on how control transfers.",
    )


def run_checks(extraction: ContractExtraction) -> list[ReviewCheck]:
    """Every deterministic check, in the order a reviewer would work them."""
    return [
        _parties(extraction),
        _effective_date(extraction),
        _currency(extraction),
        _footing(extraction),
        _obligations_priced(extraction),
        _recognition_pattern(extraction),
    ]
