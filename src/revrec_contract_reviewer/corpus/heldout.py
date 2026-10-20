"""The held-out test set: seven synthetic contracts nobody tuned against.

Written on 18 October 2026, after the rules extractor and the prompt, the
same way as the twelve in library.py: the same group of suppliers, the same
compressed documents, the same `truth` block authored from the text with the
judgment taxonomy in docs/judgment-calls.md. They were committed, with their
gold records, before either extractor had been run on them.

The rule that makes them worth having: results on this set are reported, not
used. Nothing seen here goes back into the rules, the prompt or the scorer;
a fix for something it shows is tested against the development set, and this
set measures it again afterwards.

Every party, product and number is invented.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from revrec_contract_reviewer.corpus.library import _signature
from revrec_contract_reviewer.corpus.spec import (
    ContractSpec,
    ContractTruth,
    FeeTable,
    Section,
    TruthObligation,
)
from revrec_contract_reviewer.models.extraction import AgreementType, ObligationKind
from revrec_contract_reviewer.models.judgment import JudgmentType

NIMBUS_OF_LARKSPUR = ContractSpec(
    doc_id="nimbus-of-larkspur",
    title="ORDER FORM NA-OF-2025-0467",
    subtitle="Nimbus Analytics, Inc. and Larkspur Health Systems, Inc.",
    supplier="Nimbus Analytics, Inc.",
    customer="Larkspur Health Systems, Inc.",
    preamble=(
        "This Order Form is entered into as of November 17, 2025 between Nimbus Analytics, Inc. "
        "(&quot;Nimbus&quot;) and Larkspur Health Systems, Inc. (&quot;Customer&quot;) under the Nimbus "
        "Standard Subscription Terms."
    ),
    sections=[
        Section(
            number="1",
            heading="Subscription Term",
            paragraphs=[
                "The Subscription Term commences on December 1, 2025 and continues for thirty-six (36) months.",
            ],
        ),
        Section(
            number="2",
            heading="Products and Services",
            paragraphs=["Customer orders the following:"],
            table=FeeTable(
                columns=["Item", "Fee"],
                rows=[
                    ["Clinical Operations Analytics subscription (36 months)", "USD 360,000"],
                    ["Configuration Services", "USD 45,000"],
                    ["Premium Support, 36 months", "USD 54,000"],
                    ["Total committed fees", "USD 459,000"],
                ],
            ),
        ),
        Section(
            number="3",
            heading="Configuration Services",
            paragraphs=[
                "Nimbus will configure the Platform's standard clinical operations dashboards and load Customer's "
                "facility and department hierarchy, using the configuration tools available to every Platform "
                "customer. The Configuration Services do not modify the Platform, and Customer may use the "
                "Platform without them; equivalent configuration services are offered by Nimbus's certified "
                "partners.",
                "The Configuration Services are expected to be completed within eight (8) weeks of the start of "
                "the Subscription Term.",
            ],
        ),
        Section(
            number="4",
            heading="Premium Support",
            paragraphs=[
                "Premium Support provides access to the Nimbus support desk at all hours, a named technical account "
                "manager, and a target response time of two (2) hours for priority one incidents.",
            ],
        ),
        Section(
            number="5",
            heading="Renewal",
            paragraphs=[
                "Customer may renew the subscription for one further term of twelve (12) months by written notice "
                "given at least sixty (60) days before the end of the Subscription Term. The renewal fee is "
                "Nimbus's then-current list price less a discount of fifteen percent (15%).",
            ],
        ),
        Section(
            number="6",
            heading="Invoicing and Termination",
            paragraphs=[
                "The subscription and support fees for each contract year are invoiced annually in advance, and "
                "the Configuration Services fee is invoiced at the start of the Subscription Term. All invoices "
                "are payable within thirty (30) days of the invoice date.",
                "This Order Form may not be terminated for convenience by either party.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics, Inc.", "R. Okafor", "VP, Healthcare",
        "Larkspur Health Systems, Inc.", "D. Whitcombe", "Chief Financial Officer",
    ),
    truth=ContractTruth(
        customer="Larkspur Health Systems, Inc.",
        supplier="Nimbus Analytics, Inc.",
        agreement_type=AgreementType.ORDER_FORM,
        currency="USD",
        effective_date=date(2025, 11, 17),
        stated_term_months=36,
        termination_for_convenience=False,
        termination_notice_days=None,
        net_days=30,
        total_fixed_consideration=Decimal("459000"),
        obligations=(
            TruthObligation(ObligationKind.SAAS_SUBSCRIPTION, Decimal("360000")),
            TruthObligation(ObligationKind.IMPLEMENTATION, Decimal("45000")),
            TruthObligation(ObligationKind.SUPPORT, Decimal("54000")),
        ),
        judgments=(
            JudgmentType.MATERIAL_RIGHT,
            JudgmentType.SSP_NOT_OBSERVABLE,
        ),
    ),
    commentary=(
        "Three promises, one of which looks like the Calderwood implementation and isn't: configuration with the "
        "platform's own tools, which the customer could buy from a partner or skip. No distinct-or-not question "
        "should be raised. The renewal is priced as a stated discount on list, the second material-right case, "
        "and three obligations sold together leave the allocation question as they always do."
    ),
)


NIMBUS_OF_FENWICK = ContractSpec(
    doc_id="nimbus-of-fenwick",
    title="ORDER FORM NAL-2025-0131",
    subtitle="Nimbus Analytics Ltd and Fenwick Rowe Engineering Ltd",
    supplier="Nimbus Analytics Ltd",
    customer="Fenwick Rowe Engineering Ltd",
    preamble=(
        "This Order Form is made on 6 October 2025 between Nimbus Analytics Ltd, a company registered in England "
        "and Wales (&quot;Nimbus&quot;), and Fenwick Rowe Engineering Ltd (&quot;Customer&quot;), under the "
        "Nimbus Standard Terms of Service incorporated by reference."
    ),
    sections=[
        Section(
            number="1",
            heading="Subscription",
            paragraphs=[
                "Nimbus will provide Customer with access to the Nimbus Asset Monitoring Platform for a term of "
                "twelve (12) months commencing 1 November 2025.",
                "The subscription fee for the term is GBP 66,000, invoiced in twelve (12) equal monthly "
                "instalments of GBP 5,500 in advance on the first day of each month.",
            ],
        ),
        Section(
            number="2",
            heading="Service Levels",
            paragraphs=[
                "Nimbus will make the Platform available at least 99.5% of the time in each calendar month, "
                "excluding scheduled maintenance notified at least five (5) days in advance.",
                "If availability in a month falls below that level, Customer will receive a service credit of "
                "five percent (5%) of that month's instalment for each full 0.5% of shortfall, up to a maximum of "
                "twenty-five percent (25%) of the instalment. Service credits are Customer's sole remedy for "
                "unavailability.",
            ],
        ),
        Section(
            number="3",
            heading="Termination",
            paragraphs=[
                "Customer may terminate this Order Form for convenience by giving thirty (30) days' written notice "
                "to Nimbus.",
                "On such termination Customer shall pay, in addition to the instalments falling due up to the "
                "effective date of termination, an early termination charge equal to fifty percent (50%) of the "
                "instalments that would have fallen due for the remainder of the term.",
            ],
        ),
        Section(
            number="4",
            heading="Payment",
            paragraphs=[
                "All invoices are payable within fourteen (14) days of the invoice date.",
                "All amounts are stated in Pounds Sterling and are exclusive of value added tax.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics Ltd", "H. Vaughan", "Regional Director",
        "Fenwick Rowe Engineering Ltd", "P. Lindqvist", "Head of Finance",
    ),
    truth=ContractTruth(
        customer="Fenwick Rowe Engineering Ltd",
        supplier="Nimbus Analytics Ltd",
        agreement_type=AgreementType.ORDER_FORM,
        currency="GBP",
        effective_date=date(2025, 10, 6),
        stated_term_months=12,
        termination_for_convenience=True,
        termination_notice_days=30,
        net_days=14,
        total_fixed_consideration=Decimal("66000"),
        obligations=(TruthObligation(ObligationKind.SAAS_SUBSCRIPTION, Decimal("66000")),),
        judgments=(
            JudgmentType.ENFORCEABLE_TERM,
            JudgmentType.VARIABLE_CONSIDERATION_CONSTRAINT,
        ),
    ),
    commentary=(
        "The fee is stated in a sentence rather than a table, as short order forms often do. The customer can "
        "leave on thirty days' notice for half the remaining instalments, which sits between Helix's nothing and "
        "a full make-whole: the enforceable-term question in its usual unhelpful middle. Service credits only "
        "ever reduce the price, and they still make it variable."
    ),
)


NIMBUS_SOW_HARBOURLINE = ContractSpec(
    doc_id="nimbus-sow-harbourline",
    title="STATEMENT OF WORK SOW-2025-058",
    subtitle="Berth Scheduling Model -- Nimbus Analytics, Inc. and Harbourline Port Authority",
    supplier="Nimbus Analytics, Inc.",
    customer="Harbourline Port Authority",
    preamble=(
        "This Statement of Work is entered into as of December 1, 2025 under the Professional Services Agreement "
        "between Nimbus Analytics, Inc. (&quot;Nimbus&quot;) and Harbourline Port Authority "
        "(&quot;Customer&quot;) dated May 12, 2024."
    ),
    sections=[
        Section(
            number="1",
            heading="Scope of Work",
            paragraphs=[
                "Nimbus will design, build and document a berth scheduling model that forecasts vessel arrivals "
                "and berth occupancy from Customer's historical port call data, and will deliver it as a set of "
                "models and reports running in Customer's own analytics environment.",
                "The deliverables are the design document, the trained models with their source code, and a "
                "handover workshop for Customer's analytics team.",
            ],
        ),
        Section(
            number="2",
            heading="Fees",
            paragraphs=[
                "The fee for the work is fixed. The milestones below set when it is invoiced, not whether it is "
                "earned.",
            ],
            table=FeeTable(
                columns=["Milestone", "Invoiced amount"],
                rows=[
                    ["Design document approved", "USD 54,000"],
                    ["Models delivered for acceptance testing", "USD 90,000"],
                    ["Acceptance", "USD 36,000"],
                    ["Total fixed fee", "USD 180,000"],
                ],
            ),
        ),
        Section(
            number="3",
            heading="Delivery Date",
            paragraphs=[
                "The target Acceptance Date is March 31, 2026. If Acceptance occurs after that date for reasons "
                "attributable to Nimbus, the fixed fee is reduced by USD 2,000 for each full week of delay, up to "
                "a maximum reduction of USD 20,000.",
            ],
        ),
        Section(
            number="4",
            heading="Acceptance",
            paragraphs=[
                "Customer will test the models within ten (10) business days of delivery and will either accept "
                "them or describe in reasonable detail any respect in which they fail to meet the design "
                "document. Nimbus will correct the reported failures and deliver the models again.",
            ],
        ),
        Section(
            number="5",
            heading="Termination and Payment",
            paragraphs=[
                "Either party may terminate this Statement of Work only for the other party's material breach "
                "that remains uncured thirty (30) days after written notice of it.",
                "Invoices are payable within thirty (30) days of the invoice date.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics, Inc.", "J. Castellano", "Director, Professional Services",
        "Harbourline Port Authority", "M. Osei", "Director of Operations",
    ),
    truth=ContractTruth(
        customer="Harbourline Port Authority",
        supplier="Nimbus Analytics, Inc.",
        agreement_type=AgreementType.STATEMENT_OF_WORK,
        currency="USD",
        effective_date=date(2025, 12, 1),
        stated_term_months=None,
        termination_for_convenience=False,
        termination_notice_days=None,
        net_days=30,
        total_fixed_consideration=Decimal("180000"),
        obligations=(TruthObligation(ObligationKind.PROFESSIONAL_SERVICES, Decimal("180000")),),
        judgments=(JudgmentType.VARIABLE_CONSIDERATION_CONSTRAINT,),
    ),
    commentary=(
        "A fixed fee invoiced on milestones, which the contract says in so many words, and a reduction for late "
        "delivery that makes the price variable anyway. One deliverable, so nothing to allocate; termination "
        "only for breach, so no question about the enforceable term."
    ),
)


NIMBUS_AMENDMENT_WEXFORD = ContractSpec(
    doc_id="nimbus-amendment-wexford",
    title="AMENDMENT NO. 1 TO ORDER FORM NA-OF-2023-207",
    subtitle="Nimbus Analytics GmbH and Wexford Instruments GmbH",
    supplier="Nimbus Analytics GmbH",
    customer="Wexford Instruments GmbH",
    preamble=(
        "This Amendment No. 1 is entered into as of 3 November 2025 between Nimbus Analytics GmbH "
        "(&quot;Nimbus&quot;) and Wexford Instruments GmbH (&quot;Customer&quot;) and amends Order Form "
        "NA-OF-2023-207 dated 1 January 2024 (the &quot;Original Order Form&quot;), under which Customer "
        "subscribes to the Nimbus Quality Analytics Platform for a Subscription Term ending 31 December 2026 at an "
        "annual fee of EUR 120,000. Except as expressly amended here, the Original Order Form continues in full "
        "force and effect."
    ),
    sections=[
        Section(
            number="1",
            heading="Extension of the Subscription Term",
            paragraphs=[
                "The Subscription Term is extended by twenty-four (24) months and now ends on 31 December 2028.",
            ],
        ),
        Section(
            number="2",
            heading="Revised Fees",
            paragraphs=[
                "With effect from 1 January 2026, the annual subscription fee is reduced from EUR 120,000 to EUR "
                "102,000 for each remaining contract year, in consideration of Customer's commitment to the "
                "extended term.",
                "The total subscription fees payable for the period from 1 January 2026 to 31 December 2028 "
                "(thirty-six months) are therefore EUR 306,000, invoiced in three annual instalments of EUR "
                "102,000 on 1 January of each year, each payable within thirty (30) days of the invoice date.",
            ],
        ),
        Section(
            number="3",
            heading="No Other Changes",
            paragraphs=[
                "The Platform, the number of licensed users and all other terms of the Original Order Form are "
                "unchanged.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics GmbH", "K. Brandt", "Geschäftsführer",
        "Wexford Instruments GmbH", "A. Hollmann", "Leiter Rechnungswesen",
    ),
    truth=ContractTruth(
        customer="Wexford Instruments GmbH",
        supplier="Nimbus Analytics GmbH",
        agreement_type=AgreementType.AMENDMENT,
        currency="EUR",
        effective_date=date(2025, 11, 3),
        stated_term_months=36,
        termination_for_convenience=None,
        termination_notice_days=None,
        net_days=30,
        total_fixed_consideration=Decimal("306000"),
        obligations=(TruthObligation(ObligationKind.SAAS_SUBSCRIPTION, Decimal("306000")),),
        judgments=(
            JudgmentType.CONTRACT_MODIFICATION,
            JudgmentType.SSP_NOT_OBSERVABLE,
        ),
    ),
    commentary=(
        "A blend-and-extend: a lower annual fee now in exchange for two more years. What remains to be delivered "
        "is more months of the same distinct subscription, so whether this is a separate contract or a "
        "prospective modification turns on whether EUR 102,000 a year is a standalone selling price for those "
        "months -- the SSP question asked of a single obligation, as Orchid asks it. Annual billing in advance is "
        "not a financing arrangement, however many years it runs."
    ),
)


NIMBUS_OF_SALTMARSH = ContractSpec(
    doc_id="nimbus-of-saltmarsh",
    title="ORDER FORM NA-OF-2026-0012",
    subtitle="Crop Analytics Bundle -- Nimbus Analytics, Inc. and Saltmarsh Grain Cooperative",
    supplier="Nimbus Analytics, Inc.",
    customer="Saltmarsh Grain Cooperative",
    preamble=(
        "This Order Form is entered into as of January 12, 2026 between Nimbus Analytics, Inc. "
        "(&quot;Nimbus&quot;) and Saltmarsh Grain Cooperative (&quot;Customer&quot;) under the Master "
        "Subscription Agreement between the parties dated March 4, 2024."
    ),
    sections=[
        Section(
            number="1",
            heading="Bundle Contents",
            paragraphs=[
                "The Subscription Term commences on February 1, 2026 and continues for twenty-four (24) months.",
            ],
            table=FeeTable(
                columns=["Item", "Fee"],
                rows=[
                    ["Crop Yield Analytics subscription (24 months)", "USD 168,000"],
                    ["Orbisat satellite imagery feed (24 months)", "USD 72,000"],
                    ["Total committed fees", "USD 240,000"],
                ],
            ),
        ),
        Section(
            number="2",
            heading="Satellite Imagery",
            paragraphs=[
                "The imagery feed is supplied by Orbisat Imaging Ltd, which is not affiliated with Nimbus. Nimbus "
                "purchases the imagery licence from Orbisat and grants Customer a sublicence to use the imagery "
                "within the Crop Yield Analytics service. Nimbus sets the price of the feed to Customer.",
                "Orbisat delivers the imagery directly to Customer's account and is responsible for its accuracy "
                "and coverage. Customer raises any question about the feed with Nimbus support, which passes it "
                "to Orbisat.",
                "If Orbisat ceases to supply the feed, Nimbus may substitute imagery of comparable resolution from "
                "another provider, or refund the unused portion of the feed fee.",
            ],
        ),
        Section(
            number="3",
            heading="Payment and Termination",
            paragraphs=[
                "Committed fees are invoiced annually in advance, on February 1, 2026 and February 1, 2027. "
                "Invoices are payable within thirty (30) days of the invoice date.",
                "Neither party may terminate this Order Form for convenience.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics, Inc.", "T. Adeyemi", "Account Director",
        "Saltmarsh Grain Cooperative", "E. Brandvold", "General Manager",
    ),
    truth=ContractTruth(
        customer="Saltmarsh Grain Cooperative",
        supplier="Nimbus Analytics, Inc.",
        agreement_type=AgreementType.ORDER_FORM,
        currency="USD",
        effective_date=date(2026, 1, 12),
        stated_term_months=24,
        termination_for_convenience=False,
        termination_notice_days=None,
        net_days=30,
        total_fixed_consideration=Decimal("240000"),
        obligations=(
            TruthObligation(ObligationKind.SAAS_SUBSCRIPTION, Decimal("168000")),
            TruthObligation(ObligationKind.THIRD_PARTY_RESALE, Decimal("72000")),
        ),
        judgments=(
            JudgmentType.PRINCIPAL_VS_AGENT,
            JudgmentType.SSP_NOT_OBSERVABLE,
        ),
    ),
    commentary=(
        "Beacon and Quarry each point every indicator one way. This one splits them: Nimbus buys the licence, "
        "sets the price and can substitute the provider, which points to principal; Orbisat delivers the data "
        "and answers for its accuracy, which points to agent. The question has to be raised, and the document "
        "can't settle it."
    ),
)


NIMBUS_OF_TAMARIND = ContractSpec(
    doc_id="nimbus-of-tamarind",
    title="ORDER FORM NA-OF-2025-0489",
    subtitle="Perpetual Licence -- Nimbus Analytics, Inc. and Tamarind Shipping Pte. Ltd.",
    supplier="Nimbus Analytics, Inc.",
    customer="Tamarind Shipping Pte. Ltd.",
    preamble=(
        "This Order Form is entered into as of December 8, 2025 between Nimbus Analytics, Inc. "
        "(&quot;Nimbus&quot;) and Tamarind Shipping Pte. Ltd. (&quot;Customer&quot;), a company incorporated in "
        "Singapore, under the Nimbus Software Licence Terms."
    ),
    sections=[
        Section(
            number="1",
            heading="Licence Grant",
            paragraphs=[
                "Nimbus grants Customer a perpetual, non-exclusive licence to install and use the Nimbus Fleet "
                "Planner software (the &quot;Software&quot;) on Customer's own servers for up to sixty (60) "
                "vessels. The Software is delivered by download on the date of this Order Form.",
            ],
        ),
        Section(
            number="2",
            heading="Fleet Rules Customisation",
            paragraphs=[
                "Nimbus will modify the Software's scheduling engine to apply Customer's fleet rules for crew "
                "rotation and port rotation. The Software as delivered does not support those rules, and Customer "
                "cannot use it for its intended scheduling purpose until the customisation is complete.",
                "The customisation is expected to take sixteen (16) weeks from delivery of the Software.",
            ],
        ),
        Section(
            number="3",
            heading="Fees",
            paragraphs=["The fees under this Order Form are:"],
            table=FeeTable(
                columns=["Item", "Fee"],
                rows=[
                    ["Fleet Planner perpetual licence (60 vessels)", "USD 360,000"],
                    ["Fleet rules customisation", "USD 80,000"],
                    ["Support and updates, 24 months", "USD 120,000"],
                    ["Total", "USD 560,000"],
                ],
            ),
        ),
        Section(
            number="4",
            heading="Payment",
            paragraphs=[
                "The licence fee is payable in eight (8) equal quarterly instalments of USD 45,000, the first on "
                "delivery of the Software and the last twenty-one (21) months later. No interest is charged on "
                "the instalments.",
                "The customisation fee is invoiced on completion, and support is invoiced annually in advance. All "
                "invoices are payable within thirty (30) days of the invoice date.",
                "This Order Form is non-cancellable.",
            ],
        ),
        Section(
            number="5",
            heading="Support",
            paragraphs=[
                "Support and updates are provided for twenty-four (24) months from delivery of the Software and "
                "may be renewed annually at Nimbus's then-current rates.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics, Inc.", "S. Raman", "Regional Vice President, APAC",
        "Tamarind Shipping Pte. Ltd.", "W. Tan", "Group Financial Controller",
    ),
    truth=ContractTruth(
        customer="Tamarind Shipping Pte. Ltd.",
        supplier="Nimbus Analytics, Inc.",
        agreement_type=AgreementType.ORDER_FORM,
        currency="USD",
        effective_date=date(2025, 12, 8),
        stated_term_months=24,
        termination_for_convenience=False,
        termination_notice_days=None,
        net_days=30,
        total_fixed_consideration=Decimal("560000"),
        obligations=(
            TruthObligation(ObligationKind.SOFTWARE_LICENSE, Decimal("360000")),
            TruthObligation(ObligationKind.IMPLEMENTATION, Decimal("80000")),
            TruthObligation(ObligationKind.SUPPORT, Decimal("120000")),
        ),
        judgments=(
            JudgmentType.DISTINCT_UNCERTAIN,
            JudgmentType.SIGNIFICANT_FINANCING,
            JudgmentType.SSP_NOT_OBSERVABLE,
        ),
    ),
    commentary=(
        "The licence is delivered on day one and paid for over twenty-one months with no interest, which is "
        "where a financing question starts. The customisation is the strong form of the distinct-or-not "
        "question: the contract says the software can't do its job until the work is done. Three obligations, "
        "or two, depending on the answer, and the allocation follows from it."
    ),
)


NIMBUS_OF_ALDER = ContractSpec(
    doc_id="nimbus-of-alder",
    title="ORDER FORM NA-OF-2025-0451",
    subtitle="Nimbus Analytics, Inc. and Alder Creek Veterinary Group, LLC",
    supplier="Nimbus Analytics, Inc.",
    customer="Alder Creek Veterinary Group, LLC",
    preamble=(
        "This Order Form is entered into as of October 27, 2025 between Nimbus Analytics, Inc. "
        "(&quot;Nimbus&quot;) and Alder Creek Veterinary Group, LLC (&quot;Customer&quot;) under the Nimbus "
        "Standard Subscription Terms."
    ),
    sections=[
        Section(
            number="1",
            heading="Subscription",
            paragraphs=[
                "Nimbus will provide Customer with access to the Nimbus Clinic Scheduling Insights service for a "
                "term of twelve (12) months commencing November 1, 2025, for up to twenty (20) named users.",
            ],
            table=FeeTable(
                columns=["Item", "Fee"],
                rows=[
                    ["Clinic Scheduling Insights subscription (12 months, 20 users)", "USD 9,600"],
                    ["Total committed fees", "USD 9,600"],
                ],
            ),
        ),
        Section(
            number="2",
            heading="Payment",
            paragraphs=[
                "The subscription fee is invoiced annually in advance and is payable within thirty (30) days of "
                "the invoice date.",
            ],
        ),
        Section(
            number="3",
            heading="Renewal",
            paragraphs=[
                "The subscription renews automatically for successive twelve (12) month terms at Nimbus's "
                "then-current list price, unless either party gives notice of non-renewal at least thirty (30) "
                "days before the end of the current term.",
            ],
        ),
        Section(
            number="4",
            heading="Termination",
            paragraphs=[
                "Neither party may terminate this Order Form for convenience during a term.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics, Inc.", "L. Moreau", "Account Executive",
        "Alder Creek Veterinary Group, LLC", "C. Ibarra", "Practice Manager",
    ),
    truth=ContractTruth(
        customer="Alder Creek Veterinary Group, LLC",
        supplier="Nimbus Analytics, Inc.",
        agreement_type=AgreementType.ORDER_FORM,
        currency="USD",
        effective_date=date(2025, 10, 27),
        stated_term_months=12,
        termination_for_convenience=False,
        termination_notice_days=None,
        net_days=30,
        total_fixed_consideration=Decimal("9600"),
        obligations=(TruthObligation(ObligationKind.SAAS_SUBSCRIPTION, Decimal("9600")),),
        judgments=(),
    ),
    commentary=(
        "The held-out control: one service, a fixed price, renewal at list, no way out. Like Pinegrove it should "
        "raise nothing, and anything it does raise is a false positive measured on a contract nobody tuned "
        "against."
    ),
)


HELD_OUT: list[ContractSpec] = [
    NIMBUS_OF_LARKSPUR,
    NIMBUS_OF_FENWICK,
    NIMBUS_SOW_HARBOURLINE,
    NIMBUS_AMENDMENT_WEXFORD,
    NIMBUS_OF_SALTMARSH,
    NIMBUS_OF_TAMARIND,
    NIMBUS_OF_ALDER,
]
