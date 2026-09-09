"""Wire format in, domain model out, with grounding in between.

The only place in the codebase where a ContractExtraction gets built. Both
extractors funnel through here, which is what makes "nothing is asserted without
evidence" a property of the system rather than a property of whichever extractor
happened to run.
"""

from __future__ import annotations

from revrec_contract_reviewer.extract.grounding import Grounder
from revrec_contract_reviewer.extract.schema import ContractField as F
from revrec_contract_reviewer.extract.schema import WireExtraction, one
from revrec_contract_reviewer.models.document import ContractDocument
from revrec_contract_reviewer.models.extraction import (
    AgreementType,
    ContractExtraction,
    ContractTerm,
    PaymentTerms,
    PerformanceObligation,
    RecognitionPattern,
    RenewalOption,
    VariableConsideration,
)


def assemble(
    document: ContractDocument,
    wire: WireExtraction,
    extractor: str,
    model: str | None = None,
) -> ContractExtraction:
    """Ground every claim in `wire` against `document` and build the extraction."""
    ground = Grounder(document)

    obligations: list[PerformanceObligation] = []
    for proposed in wire.obligations:
        evidence = ground.citations_for(proposed.quotes)
        if not evidence:
            # An obligation nobody can point at in the contract is not an
            # obligation. Dropping the whole thing rather than keeping a
            # label with empty fields, because a labelled row in the memo
            # reads as a finding even when every cell under it is blank.
            ground.dropped += 1
            continue
        obligations.append(
            PerformanceObligation(
                label=proposed.label,
                kind=proposed.kind,
                evidence=evidence,
                stated_price=ground.money_field(one(proposed.stated_price)),
                list_price=ground.money_field(one(proposed.list_price)),
                duration_months=ground.count_field(one(proposed.duration_months)),
                recognition=ground.enum_field(one(proposed.recognition), RecognitionPattern),
                integration_language=ground.text_field(one(proposed.integration_language)),
            )
        )

    variable: list[VariableConsideration] = []
    for proposed in wire.variable_consideration:
        evidence = ground.citations_for(proposed.quotes)
        if not evidence:
            ground.dropped += 1
            continue
        variable.append(
            VariableConsideration(
                kind=proposed.kind,
                description=proposed.description,
                evidence=evidence,
                cap=ground.money_field(one(proposed.cap)),
                estimable_from_contract=proposed.estimable_from_contract,
            )
        )

    term = ContractTerm(
        effective_date=ground.date_field(wire.claim_for(F.EFFECTIVE_DATE)),
        stated_term_months=ground.count_field(wire.claim_for(F.STATED_TERM_MONTHS)),
        auto_renews=ground.flag_field(wire.claim_for(F.AUTO_RENEWS)),
        termination_for_convenience=ground.flag_field(wire.claim_for(F.TERMINATION_FOR_CONVENIENCE)),
        termination_notice_days=ground.count_field(wire.claim_for(F.TERMINATION_NOTICE_DAYS)),
        termination_compensation=ground.text_field(wire.claim_for(F.TERMINATION_COMPENSATION)),
    )

    payment = PaymentTerms(
        net_days=ground.count_field(wire.claim_for(F.NET_DAYS)),
        billing_frequency=ground.text_field(wire.claim_for(F.BILLING_FREQUENCY)),
        upfront_fee=ground.money_field(wire.claim_for(F.UPFRONT_FEE)),
        upfront_fee_refundable=ground.flag_field(wire.claim_for(F.UPFRONT_FEE_REFUNDABLE)),
        payment_spread_months=ground.count_field(wire.claim_for(F.PAYMENT_SPREAD_MONTHS)),
    )

    renewal = RenewalOption(
        renewal_term_months=ground.count_field(wire.claim_for(F.RENEWAL_TERM_MONTHS)),
        renewal_price=ground.money_field(wire.claim_for(F.RENEWAL_PRICE)),
        described_as_discounted=ground.flag_field(wire.claim_for(F.RENEWAL_DESCRIBED_AS_DISCOUNTED)),
    )

    return ContractExtraction(
        doc_id=document.doc_id,
        agreement_type=ground.enum_field(wire.claim_for(F.AGREEMENT_TYPE), AgreementType),
        customer=ground.text_field(wire.claim_for(F.CUSTOMER)),
        supplier=ground.text_field(wire.claim_for(F.SUPPLIER)),
        amends=ground.text_field(wire.claim_for(F.AMENDS)),
        currency=ground.text_field(wire.claim_for(F.CURRENCY)),
        total_fixed_consideration=ground.money_field(wire.claim_for(F.TOTAL_FIXED_CONSIDERATION)),
        term=term,
        payment=payment,
        renewal=renewal,
        obligations=obligations,
        variable_consideration=variable,
        third_party_components=ground.text_field(wire.claim_for(F.THIRD_PARTY_COMPONENTS)),
        extractor=extractor,
        model=model,
        # Read last: every field above has been built by this point, so the
        # counter has seen everything it is going to see.
        dropped_for_no_evidence=ground.dropped,
    )
