"""Scoring an extraction against the gold set.

Four things get measured, and they are kept apart because they fail for
different reasons and get fixed in different places.

**Fields.** Precision and recall over the scalar contract terms. A field the
document does not state is scored too: reporting a value where the contract is
silent is counted as an invention, separately from getting a stated value wrong.
Those two mistakes feel similar in a spreadsheet and are not similar at all in a
review -- a wrong term length gets caught by the reviewer reading the clause, an
invented one sends them looking for a clause that does not exist.

**Obligations.** Matched as a multiset of (kind, price). Not by label: labels are
free text and a fair scorer should not reward one wording of "Premium Support,
36 months" over another.

**Judgments.** Set comparison per contract. This is the number that matters most
for the product, because a reviewer's trust is spent by false positives long
before it is spent by misses.

**Citations.** Every citation in the output is re-resolved against the document.
This should always be 100% -- grounding already refused anything that failed --
so it is really an independent check that the invariant holds rather than a
measure of the extractor. It is here because "the control is enforced" is a
claim worth being able to prove after the fact rather than by reading the code.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel, Field

from revrec_contract_reviewer.evaluate.gold import SCORED_FIELDS, GoldRecord
from revrec_contract_reviewer.ingest.text import NormalizedText
from revrec_contract_reviewer.models.document import ContractDocument
from revrec_contract_reviewer.models.extraction import ContractExtraction
from revrec_contract_reviewer.models.fields import ExtractedField
from revrec_contract_reviewer.models.review import ContractReview


class Tally(BaseModel):
    """True positives, false positives and misses, plus the rates they imply."""

    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    @property
    def precision(self) -> float:
        predicted = self.true_positives + self.false_positives
        return self.true_positives / predicted if predicted else 1.0

    @property
    def recall(self) -> float:
        actual = self.true_positives + self.false_negatives
        return self.true_positives / actual if actual else 1.0

    @property
    def f1(self) -> float:
        if not self.precision or not self.recall:
            return 0.0
        return 2 * self.precision * self.recall / (self.precision + self.recall)

    def add(self, other: Tally) -> None:
        self.true_positives += other.true_positives
        self.false_positives += other.false_positives
        self.false_negatives += other.false_negatives


class ContractScore(BaseModel):
    doc_id: str
    fields: Tally = Field(default_factory=Tally)
    silence: Tally = Field(
        default_factory=Tally,
        description="Fields the contract does not state. A true positive here means the extractor stayed quiet.",
    )
    obligations: Tally = Field(default_factory=Tally)
    judgments: Tally = Field(default_factory=Tally)
    citations_total: int = 0
    citations_resolved: int = 0
    dropped_for_no_evidence: int = 0
    mistakes: list[str] = []


class EvalReport(BaseModel):
    extractor: str
    model: str | None = None
    per_contract: list[ContractScore] = []
    fields: Tally = Field(default_factory=Tally)
    silence: Tally = Field(default_factory=Tally)
    obligations: Tally = Field(default_factory=Tally)
    judgments: Tally = Field(default_factory=Tally)
    citations_total: int = 0
    citations_resolved: int = 0
    dropped_for_no_evidence: int = 0

    @property
    def citation_rate(self) -> float:
        return self.citations_resolved / self.citations_total if self.citations_total else 1.0


def _extracted_value(extraction: ContractExtraction, name: str) -> ExtractedField[Any]:
    """Where each scored field lives on the extraction."""
    lookup: dict[str, ExtractedField[Any]] = {
        "customer": extraction.customer,
        "supplier": extraction.supplier,
        "agreement_type": extraction.agreement_type,
        "currency": extraction.currency,
        "effective_date": extraction.term.effective_date,
        "stated_term_months": extraction.term.stated_term_months,
        "termination_for_convenience": extraction.term.termination_for_convenience,
        "termination_notice_days": extraction.term.termination_notice_days,
        "net_days": extraction.payment.net_days,
        "total_fixed_consideration": extraction.total_fixed_consideration,
    }
    return lookup[name]


def _matches(expected: Any, actual: Any) -> bool:
    """Compare a gold value to an extracted one, tolerating representation only.

    "689000" and Decimal("689000.00") are the same amount; "USD" and "usd" are
    the same currency. Nothing here tolerates a different answer.
    """
    if isinstance(expected, bool) or isinstance(actual, bool):
        return bool(expected) == bool(actual)

    actual_value = getattr(actual, "value", actual)

    if isinstance(expected, str):
        try:
            return Decimal(expected) == Decimal(str(actual_value))
        except (InvalidOperation, ValueError):
            return expected.strip().lower() == str(actual_value).strip().lower()

    return str(expected) == str(actual_value)


def _score_fields(extraction: ContractExtraction, gold: GoldRecord, score: ContractScore) -> None:
    for name in SCORED_FIELDS:
        expected = gold.fields.get(name)
        field = _extracted_value(extraction, name)

        if expected is None:
            # The contract says nothing. Staying quiet is the right answer, and
            # ambiguous counts as quiet -- it does not assert a value either.
            if field.is_known:
                score.silence.false_positives += 1
                score.mistakes.append(f"{name}: invented {field.value!r} where the contract is silent")
            else:
                score.silence.true_positives += 1
            continue

        if not field.is_known:
            score.fields.false_negatives += 1
            score.mistakes.append(f"{name}: missed (gold {expected!r}, status {field.status.value})")
        elif _matches(expected, field.value):
            score.fields.true_positives += 1
        else:
            score.fields.false_positives += 1
            score.fields.false_negatives += 1
            score.mistakes.append(f"{name}: read {field.value!r}, gold {expected!r}")


def _score_obligations(extraction: ContractExtraction, gold: GoldRecord, score: ContractScore) -> None:
    def key(kind: str, price: str | None) -> tuple[str, str]:
        return kind, str(Decimal(price)) if price is not None else "-"

    expected = Counter(key(item.kind, item.stated_price) for item in gold.obligations)
    actual = Counter(
        key(
            obligation.kind.value,
            str(obligation.stated_price.value) if obligation.stated_price.is_known else None,
        )
        for obligation in extraction.obligations
    )

    matched = expected & actual
    score.obligations.true_positives = sum(matched.values())
    score.obligations.false_positives = sum((actual - expected).values())
    score.obligations.false_negatives = sum((expected - actual).values())

    for item, count in (actual - expected).items():
        score.mistakes.append(f"obligation not in gold: {item[0]} at {item[1]} (x{count})")
    for item, count in (expected - actual).items():
        score.mistakes.append(f"obligation missed: {item[0]} at {item[1]} (x{count})")


def _score_judgments(review: ContractReview, gold: GoldRecord, score: ContractScore) -> None:
    expected = set(gold.judgments)
    actual = {flag.judgment_type.value for flag in review.flags}

    score.judgments.true_positives = len(expected & actual)
    score.judgments.false_positives = len(actual - expected)
    score.judgments.false_negatives = len(expected - actual)

    for judgment in sorted(actual - expected):
        score.mistakes.append(f"judgment raised but not expected: {judgment}")
    for judgment in sorted(expected - actual):
        score.mistakes.append(f"judgment expected but not raised: {judgment}")


def _score_citations(review: ContractReview, document: ContractDocument, score: ContractScore) -> None:
    """Re-resolve every citation in the review against the document text."""
    text = NormalizedText(document.text)

    def check(citations: list) -> None:
        for citation in citations:
            score.citations_total += 1
            if text.contains(citation.quote):
                score.citations_resolved += 1
            else:
                score.mistakes.append(f"citation does not resolve: {citation.excerpt(60)!r}")

    extraction = review.extraction
    for field in (
        extraction.customer,
        extraction.supplier,
        extraction.agreement_type,
        extraction.currency,
        extraction.amends,
        extraction.total_fixed_consideration,
        extraction.third_party_components,
        extraction.term.effective_date,
        extraction.term.stated_term_months,
        extraction.term.auto_renews,
        extraction.term.termination_for_convenience,
        extraction.term.termination_notice_days,
        extraction.term.termination_compensation,
        extraction.payment.net_days,
        extraction.payment.billing_frequency,
        extraction.payment.upfront_fee,
        extraction.payment.upfront_fee_refundable,
        extraction.payment.payment_spread_months,
        extraction.renewal.renewal_term_months,
        extraction.renewal.renewal_price,
        extraction.renewal.described_as_discounted,
    ):
        check(field.citations)

    for obligation in extraction.obligations:
        check(obligation.evidence)
        for field in (
            obligation.stated_price,
            obligation.list_price,
            obligation.duration_months,
            obligation.recognition,
            obligation.integration_language,
        ):
            check(field.citations)

    for term in extraction.variable_consideration:
        check(term.evidence)
        check(term.cap.citations)

    for flag in review.flags:
        check(flag.evidence)


def score_contract(review: ContractReview, document: ContractDocument, gold: GoldRecord) -> ContractScore:
    score = ContractScore(doc_id=gold.doc_id)
    _score_fields(review.extraction, gold, score)
    _score_obligations(review.extraction, gold, score)
    _score_judgments(review, gold, score)
    _score_citations(review, document, score)
    score.dropped_for_no_evidence = review.extraction.dropped_for_no_evidence
    return score


def aggregate(scores: list[ContractScore], extractor: str, model: str | None) -> EvalReport:
    report = EvalReport(extractor=extractor, model=model, per_contract=scores)
    for score in scores:
        report.fields.add(score.fields)
        report.silence.add(score.silence)
        report.obligations.add(score.obligations)
        report.judgments.add(score.judgments)
        report.citations_total += score.citations_total
        report.citations_resolved += score.citations_resolved
        report.dropped_for_no_evidence += score.dropped_for_no_evidence
    return report
