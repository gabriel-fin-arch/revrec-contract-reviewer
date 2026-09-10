"""What the reviewer reads off a contract, organised the way ASC 606 asks the questions.

One thing worth saying loudly, because it shaped the whole schema: **standalone
selling price is not in the contract.** SSP is the price at which an entity would
sell a good or service separately, and a contract is by definition the price it
sold at *this time, to this customer*. Every schema I sketched that had an
`ssp` field on it was quietly lying about where that number comes from.

So what gets extracted here is what the four corners of the document actually
contain: the stated price, the list or undiscounted rate where the order form
shows one, the renewal price. The SSP question itself is raised as a judgment for
a human with access to the entity's pricing data. Same reasoning applies to the
variable consideration constraint and to whether a renewal discount is
"incremental to the range typically given": those live outside the document.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from revrec_contract_reviewer.models.citation import Citation
from revrec_contract_reviewer.models.fields import ExtractedField


class AgreementType(StrEnum):
    """What kind of paper this is.

    Matters more than it looks: an order form and the MSA it hangs off are one
    contract for ASC 606 purposes, while an amendment signed later is a contract
    modification with its own accounting question.
    """

    MASTER_AGREEMENT = "master_agreement"
    ORDER_FORM = "order_form"
    STATEMENT_OF_WORK = "statement_of_work"
    AMENDMENT = "amendment"
    UNKNOWN = "unknown"


class ObligationKind(StrEnum):
    SAAS_SUBSCRIPTION = "saas_subscription"
    SOFTWARE_LICENSE = "software_license"
    IMPLEMENTATION = "implementation"
    SUPPORT = "support"
    TRAINING = "training"
    PROFESSIONAL_SERVICES = "professional_services"
    THIRD_PARTY_RESALE = "third_party_resale"
    CLINICAL_SERVICES = "clinical_services"
    OTHER = "other"


class RecognitionPattern(StrEnum):
    """Whether the contract language points at over-time or point-in-time transfer.

    UNDETERMINED is a real answer here, not a failure. Plenty of clauses describe
    a deliverable without saying anything about how control passes, and guessing
    from the obligation's name is how you end up recognising a term licence
    ratably because it had the word "subscription" in the product code.
    """

    OVER_TIME = "over_time"
    POINT_IN_TIME = "point_in_time"
    UNDETERMINED = "undetermined"


class VariableConsiderationKind(StrEnum):
    USAGE_OVERAGE = "usage_overage"
    VOLUME_REBATE = "volume_rebate"
    SERVICE_LEVEL_CREDIT = "service_level_credit"
    MILESTONE_BONUS = "milestone_bonus"
    LATE_DELIVERY_PENALTY = "late_delivery_penalty"
    ROYALTY = "royalty"
    REFUND_RIGHT = "refund_right"


class PerformanceObligation(BaseModel):
    """A promised good or service, as the contract describes it.

    Deliberately *not* holding a `distinct` flag. Whether a promise is distinct
    is the single most argued judgment in ASC 606 and it turns on facts the
    contract only hints at. What this model carries instead is the evidence:
    the integration and customisation language. The assessment step turns that
    evidence into a flag for a human rather than an answer.
    """

    label: str = Field(description="The promise as the contract names it, e.g. 'Platform subscription, Tier 3'.")
    kind: ObligationKind
    evidence: list[Citation] = Field(
        default=[],
        description="Where the document establishes this promise. An obligation with none of this is not built.",
    )
    stated_price: ExtractedField[Decimal] = ExtractedField[Decimal].absent()
    list_price: ExtractedField[Decimal] = Field(
        default=ExtractedField[Decimal].absent(),
        description="Undiscounted rate where the order form prints one. An input to the SSP question, not the answer.",
    )
    duration_months: ExtractedField[int] = ExtractedField[int].absent()
    recognition: ExtractedField[RecognitionPattern] = ExtractedField[RecognitionPattern].absent()
    integration_language: ExtractedField[str] = Field(
        default=ExtractedField[str].absent(),
        description="Wording suggesting this promise is integrated with, or significantly customises, another one.",
    )


class VariableConsideration(BaseModel):
    """A term that makes the transaction price something other than a fixed number."""

    kind: VariableConsiderationKind
    description: str
    evidence: list[Citation] = []
    cap: ExtractedField[Decimal] = Field(
        default=ExtractedField[Decimal].absent(),
        description="Stated ceiling on the variable amount, where the contract sets one.",
    )
    estimable_from_contract: bool = Field(
        default=False,
        description=(
            "True only when the contract itself fixes the amount and the trigger: a stated milestone fee on a "
            "stated deliverable. Usage tiers and rebates are False: the amount depends on the customer's behaviour, "
            "which is not in the document."
        ),
    )


class ContractTerm(BaseModel):
    """Dates, duration, and the clauses that decide how long the contract really is.

    The stated term and the enforceable term are different questions. A three-year
    subscription that either party can walk away from on 30 days' notice with no
    compensation is, for ASC 606, closer to a rolling one-month contract, and
    that changes the transaction price, the allocation, and whether the renewal
    discount is even a material right. Both get captured; neither gets resolved here.
    """

    effective_date: ExtractedField[date] = ExtractedField[date].absent()
    stated_term_months: ExtractedField[int] = ExtractedField[int].absent()
    auto_renews: ExtractedField[bool] = ExtractedField[bool].absent()
    termination_for_convenience: ExtractedField[bool] = ExtractedField[bool].absent()
    termination_notice_days: ExtractedField[int] = ExtractedField[int].absent()
    termination_compensation: ExtractedField[str] = Field(
        default=ExtractedField[str].absent(),
        description="What the terminating party owes, verbatim. 'Substantive' is a legal read, so the words are kept.",
    )


class PaymentTerms(BaseModel):
    net_days: ExtractedField[int] = ExtractedField[int].absent()
    billing_frequency: ExtractedField[str] = ExtractedField[str].absent()
    upfront_fee: ExtractedField[Decimal] = ExtractedField[Decimal].absent()
    upfront_fee_refundable: ExtractedField[bool] = ExtractedField[bool].absent()
    payment_spread_months: ExtractedField[int] = Field(
        default=ExtractedField[int].absent(),
        description=(
            "Months from the first payment to the last, where the contract sets out an instalment schedule. "
            "Net terms are a different question. This is about consideration deferred across years, which is "
            "where a financing component starts to be worth asking about."
        ),
    )


class RenewalOption(BaseModel):
    """A right to renew, which may or may not be a material right.

    It's a material right only if the renewal price is discounted *relative to
    the range the entity typically offers*, market data that is nowhere in the
    contract. So this captures the renewal price and whether the contract itself
    frames it as a discount, and stops there.
    """

    renewal_term_months: ExtractedField[int] = ExtractedField[int].absent()
    renewal_price: ExtractedField[Decimal] = ExtractedField[Decimal].absent()
    described_as_discounted: ExtractedField[bool] = ExtractedField[bool].absent()


class ContractExtraction(BaseModel):
    """Everything read off one document, before any assessment runs."""

    doc_id: str
    agreement_type: ExtractedField[AgreementType] = ExtractedField[AgreementType].absent()
    customer: ExtractedField[str] = ExtractedField[str].absent()
    supplier: ExtractedField[str] = ExtractedField[str].absent()
    amends: ExtractedField[str] = Field(
        default=ExtractedField[str].absent(),
        description="For an amendment, the agreement it modifies.",
    )
    currency: ExtractedField[str] = ExtractedField[str].absent()
    total_fixed_consideration: ExtractedField[Decimal] = ExtractedField[Decimal].absent()

    term: ContractTerm = ContractTerm()
    payment: PaymentTerms = PaymentTerms()
    renewal: RenewalOption = RenewalOption()

    obligations: list[PerformanceObligation] = []
    variable_consideration: list[VariableConsideration] = []

    third_party_components: ExtractedField[str] = Field(
        default=ExtractedField[str].absent(),
        description="Language about goods or services supplied by a third party. The principal vs agent trigger.",
    )

    extractor: str = Field(description='Which extractor produced this: "llm" or "rules".')
    model: str | None = Field(default=None, description="Model id, when the LLM extractor ran.")
    dropped_for_no_evidence: int = Field(
        default=0,
        description=(
            "How many proposed facts grounding threw away because their quote could not be found in the document. "
            "Surfaced rather than swallowed: a run where this climbs is a run whose extraction is drifting."
        ),
    )

    def priced_obligations(self) -> list[PerformanceObligation]:
        return [ob for ob in self.obligations if ob.stated_price.is_known]

    def allocated_total(self) -> Decimal:
        """Sum of the stated prices we could actually read. Not the transaction price --
        variable consideration is deliberately not in here."""
        return sum((ob.stated_price.value for ob in self.priced_obligations()), Decimal("0"))
