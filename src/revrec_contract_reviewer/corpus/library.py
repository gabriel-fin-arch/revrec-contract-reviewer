"""The twelve synthetic contracts.

Every party name, product and number here is invented. The *shapes* are not:
each document is built around a specific ASC 606 question I wanted the reviewer
to have to face, and two of them are built around no question at all, because a
tool that flags something on every contract is not a reviewer, it's a
smoke alarm with a stuck button.

The supplier is a different legal entity from one contract to the next --
Nimbus Analytics, Inc., its UK and German subsidiaries, and the group's clinical
services arm. That's the whole reason a group-level review exists: the same
group, selling on materially different paper, with local finance teams reaching
their own conclusions about it.

Documents are compressed. A real master agreement runs forty pages of
indemnities and data processing terms that have nothing to do with revenue; what
survives here is the part a revenue reviewer would actually read.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from revrec_contract_reviewer.corpus.spec import (
    ContractSpec,
    ContractTruth,
    FeeTable,
    Section,
    TruthObligation,
)
from revrec_contract_reviewer.models.extraction import AgreementType, ObligationKind
from revrec_contract_reviewer.models.judgment import JudgmentType

_SIGNATURE = (
    "IN WITNESS WHEREOF, the parties have executed this document by their duly authorised representatives. "
    "<br/><br/>For {supplier}: _______________________&nbsp;&nbsp;&nbsp;Name: {supplier_signer}&nbsp;&nbsp;&nbsp;"
    "Title: {supplier_title}<br/><br/>For {customer}: _______________________&nbsp;&nbsp;&nbsp;"
    "Name: {customer_signer}&nbsp;&nbsp;&nbsp;Title: {customer_title}"
)


def _signature(supplier: str, supplier_signer: str, supplier_title: str, customer: str, customer_signer: str,
               customer_title: str) -> str:
    return _SIGNATURE.format(
        supplier=supplier,
        supplier_signer=supplier_signer,
        supplier_title=supplier_title,
        customer=customer,
        customer_signer=customer_signer,
        customer_title=customer_title,
    )


NIMBUS_MSA_CALDERWOOD = ContractSpec(
    doc_id="nimbus-msa-calderwood",
    title="MASTER SUBSCRIPTION AGREEMENT",
    subtitle="Nimbus Analytics, Inc. and Calderwood Logistics Group, Inc.",
    supplier="Nimbus Analytics, Inc.",
    customer="Calderwood Logistics Group, Inc.",
    preamble=(
        "This Master Subscription Agreement (the &quot;Agreement&quot;) is entered into as of January 15, 2025 "
        "(the &quot;Effective Date&quot;) by and between Nimbus Analytics, Inc., a Delaware corporation with its "
        "principal place of business at 1400 Corvina Street, Suite 900, Wilmington, Delaware (&quot;Nimbus&quot;), "
        "and Calderwood Logistics Group, Inc., a Pennsylvania corporation (&quot;Customer&quot;). This Agreement "
        "governs all Order Forms executed by the parties that reference it."
    ),
    sections=[
        Section(
            number="1",
            heading="Definitions",
            paragraphs=[
                "&quot;Platform&quot; means the Nimbus hosted freight analytics service, together with any "
                "modules, application programming interfaces and documentation made available by Nimbus.",
                "&quot;Order Form&quot; means an ordering document executed by both parties that references this "
                "Agreement and specifies the subscriptions, professional services and fees agreed for a "
                "particular transaction.",
                "&quot;Subscription Term&quot; means the period stated in an Order Form during which Customer is "
                "entitled to access the Platform.",
            ],
        ),
        Section(
            number="2",
            heading="Scope and Order Forms",
            paragraphs=[
                "Nimbus grants Customer a non-exclusive, non-transferable right to access and use the Platform "
                "during the Subscription Term, solely for Customer's internal business operations and subject to "
                "the usage limits stated in the applicable Order Form.",
                "Each Order Form forms part of this Agreement. In the event of a conflict between this Agreement "
                "and an Order Form, the Order Form controls, but only as to the transaction it describes.",
                "No Order Form is binding until executed by an authorised representative of both parties.",
            ],
        ),
        Section(
            number="3",
            heading="Fees and Payment",
            paragraphs=[
                "Customer shall pay the fees set out in each Order Form. Unless an Order Form states otherwise, "
                "subscription fees are invoiced annually in advance and all invoices are payable within thirty "
                "(30) days of the invoice date.",
                "All fees are stated in United States Dollars and are exclusive of taxes. Fees are non-refundable "
                "except where this Agreement expressly provides otherwise.",
                "Nimbus may suspend access to the Platform if an undisputed invoice remains unpaid more than "
                "fifteen (15) days after written notice of non-payment.",
            ],
        ),
        Section(
            number="4",
            heading="Term and Termination",
            paragraphs=[
                "This Agreement commences on the Effective Date and continues until the expiry or termination of "
                "the last Order Form executed under it.",
                "Either party may terminate this Agreement or any Order Form for material breach if the breaching "
                "party fails to cure that breach within thirty (30) days of written notice describing it.",
                "Customer has no right to terminate an Order Form for convenience. Termination of this Agreement "
                "does not relieve Customer of the obligation to pay fees accrued or committed under any Order "
                "Form as at the effective date of termination.",
            ],
        ),
        Section(
            number="5",
            heading="Warranties and Disclaimers",
            paragraphs=[
                "Nimbus warrants that the Platform will perform materially in accordance with its documentation. "
                "Customer's exclusive remedy for breach of this warranty is correction of the non-conformity or, "
                "where Nimbus cannot correct it within a reasonable period, termination of the affected Order "
                "Form and a refund of prepaid fees for the unused portion of the Subscription Term.",
                "Except as expressly stated, the Platform is provided &quot;as is&quot; and Nimbus disclaims all "
                "other warranties to the extent permitted by law.",
            ],
        ),
        Section(
            number="6",
            heading="General",
            paragraphs=[
                "This Agreement is governed by the laws of the State of Delaware, without regard to its conflict "
                "of laws rules.",
                "Neither party may assign this Agreement without the other party's prior written consent, except "
                "to a successor in connection with a merger or sale of substantially all of its assets.",
                "This Agreement, together with all Order Forms, constitutes the entire agreement between the "
                "parties with respect to its subject matter.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics, Inc.", "D. Ashworth", "VP Commercial",
        "Calderwood Logistics Group, Inc.", "M. Reyes", "Chief Financial Officer",
    ),
    truth=ContractTruth(
        customer="Calderwood Logistics Group, Inc.",
        supplier="Nimbus Analytics, Inc.",
        agreement_type=AgreementType.MASTER_AGREEMENT,
        currency="USD",
        effective_date=date(2025, 1, 15),
        stated_term_months=None,
        termination_for_convenience=False,
        termination_notice_days=None,
        net_days=30,
        total_fixed_consideration=None,
        obligations=(),
        judgments=(),
    ),
    commentary=(
        "The framework document with no economics in it. A master agreement on its own is not a contract with a "
        "customer under ASC 606 -- there is no consideration and nothing has been ordered -- so the right answer "
        "here is a clean review with no judgments raised. Half the value of having it in the corpus is measuring "
        "that the reviewer stays quiet."
    ),
)


NIMBUS_OF_CALDERWOOD = ContractSpec(
    doc_id="nimbus-of-calderwood-2025",
    title="ORDER FORM NA-OF-2025-0231",
    subtitle="Issued under the Master Subscription Agreement dated January 15, 2025",
    supplier="Nimbus Analytics, Inc.",
    customer="Calderwood Logistics Group, Inc.",
    preamble=(
        "This Order Form is entered into as of March 3, 2025 between Nimbus Analytics, Inc. "
        "(&quot;Nimbus&quot;) and Calderwood Logistics Group, Inc. (&quot;Customer&quot;), and is governed by the "
        "Master Subscription Agreement between the parties dated January 15, 2025. Capitalised terms not defined "
        "here have the meanings given in that Agreement."
    ),
    sections=[
        Section(
            number="1",
            heading="Subscription Term",
            paragraphs=[
                "The Subscription Term commences on April 1, 2025 and continues for thirty-six (36) months, "
                "expiring on March 31, 2028.",
                "Customer may not terminate this Order Form for convenience. Section 4 of the Agreement "
                "(termination for material breach) continues to apply.",
            ],
        ),
        Section(
            number="2",
            heading="Products and Services",
            paragraphs=[
                "Nimbus will provide the following, at the fees stated. The &quot;List Rate&quot; column shows "
                "Nimbus's published rate card price for each item as at the date of this Order Form; the "
                "&quot;Fee&quot; column shows the price agreed for this transaction.",
            ],
            table=FeeTable(
                columns=["Item", "List Rate", "Fee"],
                rows=[
                    ["Platform subscription, Tier 3 (36 months)", "USD 612,000", "USD 540,000"],
                    ["Implementation and data migration services", "USD 110,000", "USD 95,000"],
                    ["Premium Support, 36 months", "USD 60,000", "USD 54,000"],
                    ["Total", "USD 782,000", "USD 689,000"],
                ],
            ),
        ),
        Section(
            number="3",
            heading="Implementation Services",
            paragraphs=[
                "Nimbus will configure the Platform to Customer's operational workflows, including the "
                "development of custom data connectors to Customer's transport management and warehouse systems, "
                "migration of twenty-four (24) months of historical shipment data, and configuration of "
                "Customer-specific routing rules within the Platform's analytics engine.",
                "Customer acknowledges that the Platform as configured under this Order Form is dependent on the "
                "connectors developed as part of these services, and that the analytics outputs Customer has "
                "contracted for cannot be produced from the standard Platform configuration alone.",
                "Implementation services are estimated to complete within four (4) months of the commencement of "
                "the Subscription Term. Fees for implementation are invoiced 50% on commencement and 50% on "
                "Customer's written acceptance.",
            ],
        ),
        Section(
            number="4",
            heading="Support",
            paragraphs=[
                "Premium Support entitles Customer to a named technical account manager, a one (1) hour target "
                "response time for severity-one incidents, and access to all Platform updates and new modules "
                "released during the Subscription Term at no additional charge.",
            ],
        ),
        Section(
            number="5",
            heading="Renewal",
            paragraphs=[
                "At the end of the Subscription Term, Customer may renew the Platform subscription for a further "
                "twelve (12) months at a fee of USD 165,000. The parties acknowledge that this renewal fee "
                "represents a discount to the list rate that would otherwise apply on renewal.",
                "The renewal right in this Section may be exercised by written notice given not less than sixty "
                "(60) days before expiry of the Subscription Term.",
            ],
        ),
        Section(
            number="6",
            heading="Invoicing",
            paragraphs=[
                "Subscription and support fees are invoiced annually in advance in three equal instalments of "
                "USD 198,000 on April 1, 2025, April 1, 2026 and April 1, 2027. Payment terms are net thirty (30) "
                "days from the invoice date, as provided in Section 3 of the Agreement.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics, Inc.", "D. Ashworth", "VP Commercial",
        "Calderwood Logistics Group, Inc.", "P. Okonjo", "Group Financial Controller",
    ),
    truth=ContractTruth(
        customer="Calderwood Logistics Group, Inc.",
        supplier="Nimbus Analytics, Inc.",
        agreement_type=AgreementType.ORDER_FORM,
        currency="USD",
        effective_date=date(2025, 3, 3),
        stated_term_months=36,
        termination_for_convenience=False,
        termination_notice_days=None,
        net_days=30,
        total_fixed_consideration=Decimal("689000"),
        obligations=(
            TruthObligation(ObligationKind.SAAS_SUBSCRIPTION, Decimal("540000")),
            TruthObligation(ObligationKind.IMPLEMENTATION, Decimal("95000")),
            TruthObligation(ObligationKind.SUPPORT, Decimal("54000")),
        ),
        judgments=(
            JudgmentType.DISTINCT_UNCERTAIN,
            JudgmentType.MATERIAL_RIGHT,
            JudgmentType.SSP_NOT_OBSERVABLE,
        ),
    ),
    commentary=(
        "The workhorse of the corpus: a three-element bundle sold at an aggregate discount, with implementation "
        "language that leans hard on integration, and a renewal at a stated discount. The list rate column is "
        "there on purpose -- it is an input to the SSP question and it is routinely mistaken for the answer."
    ),
)


NIMBUS_OF_HELIX = ContractSpec(
    doc_id="nimbus-of-helix",
    title="ORDER FORM NAL-2025-0088",
    subtitle="Nimbus Analytics Ltd and Helix Robotics Limited",
    supplier="Nimbus Analytics Ltd",
    customer="Helix Robotics Limited",
    preamble=(
        "This Order Form is made on 12 June 2025 between Nimbus Analytics Ltd, a company registered in England "
        "and Wales (&quot;Nimbus&quot;), and Helix Robotics Limited (&quot;Customer&quot;), under the Nimbus "
        "Standard Terms of Service incorporated by reference."
    ),
    sections=[
        Section(
            number="1",
            heading="Services and Fees",
            paragraphs=[
                "Nimbus will provide Customer with access to the Nimbus Telemetry Platform and standard support "
                "for a term of twenty-four (24) months commencing 1 July 2025.",
            ],
            table=FeeTable(
                columns=["Item", "Fee"],
                rows=[
                    ["Telemetry Platform subscription (24 months)", "GBP 288,000"],
                    ["Standard Support, 24 months", "GBP 24,000"],
                    ["Total committed fees", "GBP 312,000"],
                ],
            ),
        ),
        Section(
            number="2",
            heading="Included Volume and Overage",
            paragraphs=[
                "The fees in Section 1 include processing of up to five million (5,000,000) telemetry events per "
                "calendar month.",
                "Events processed above that allowance are charged at GBP 0.02 per one thousand (1,000) events, "
                "invoiced monthly in arrears. There is no cap on overage charges.",
                "Customer's average monthly volume over the six months preceding this Order Form was "
                "approximately 4.1 million events. The parties acknowledge that actual volumes may vary "
                "materially with Customer's deployment schedule.",
            ],
        ),
        Section(
            number="3",
            heading="Termination",
            paragraphs=[
                "Either party may terminate this Order Form at any time for convenience by giving sixty (60) "
                "days' written notice to the other party.",
                "On termination for convenience, Customer shall pay all fees for services rendered up to the "
                "effective date of termination, and Nimbus shall refund any prepaid fees relating to the period "
                "after that date. Neither party owes the other any further compensation, penalty or termination "
                "fee in respect of the unexpired portion of the term.",
            ],
        ),
        Section(
            number="4",
            heading="Payment",
            paragraphs=[
                "Committed fees are invoiced quarterly in advance. All invoices are payable within thirty (30) "
                "days of the invoice date.",
                "All amounts are stated in Pounds Sterling and are exclusive of value added tax.",
            ],
        ),
        Section(
            number="5",
            heading="Support",
            paragraphs=[
                "Standard Support provides access to the Nimbus support desk during UK business hours, with a "
                "target response time of one (1) business day, and includes all Platform updates released during "
                "the term.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics Ltd", "H. Vaughan", "Regional Director",
        "Helix Robotics Limited", "S. Ibrahim", "Finance Director",
    ),
    truth=ContractTruth(
        customer="Helix Robotics Limited",
        supplier="Nimbus Analytics Ltd",
        agreement_type=AgreementType.ORDER_FORM,
        currency="GBP",
        effective_date=date(2025, 6, 12),
        stated_term_months=24,
        termination_for_convenience=True,
        termination_notice_days=60,
        net_days=30,
        total_fixed_consideration=Decimal("312000"),
        obligations=(
            TruthObligation(ObligationKind.SAAS_SUBSCRIPTION, Decimal("288000")),
            TruthObligation(ObligationKind.SUPPORT, Decimal("24000")),
        ),
        judgments=(
            JudgmentType.ENFORCEABLE_TERM,
            JudgmentType.SSP_NOT_OBSERVABLE,
            JudgmentType.VARIABLE_CONSIDERATION_CONSTRAINT,
        ),
    ),
    commentary=(
        "A twenty-four month contract that may well be a one-month contract. Termination for convenience on 60 "
        "days' notice with an express statement that no further compensation is owed is about as clean a "
        "not-substantive termination penalty as you will see, and if the enforceable term really is two months, "
        "the transaction price the local team booked is wrong by an order of magnitude. Uncapped overage is the "
        "second question: the historical volume is disclosed, which tempts an estimate, but it is the customer's "
        "future deployment schedule that decides it."
    ),
)


NIMBUS_AMENDMENT_ORCHID = ContractSpec(
    doc_id="nimbus-amendment-orchid",
    title="AMENDMENT NO. 2 TO ORDER FORM NA-OF-2024-114",
    subtitle="Nimbus Analytics GmbH and Orchid Retail Holdings AG",
    supplier="Nimbus Analytics GmbH",
    customer="Orchid Retail Holdings AG",
    preamble=(
        "This Amendment No. 2 is entered into as of 1 September 2025 between Nimbus Analytics GmbH "
        "(&quot;Nimbus&quot;) and Orchid Retail Holdings AG (&quot;Customer&quot;) and amends Order Form "
        "NA-OF-2024-114 dated 1 July 2024, as previously amended by Amendment No. 1 dated 15 January 2025 (the "
        "&quot;Original Order Form&quot;). Except as expressly amended here, the Original Order Form continues "
        "in full force and effect."
    ),
    sections=[
        Section(
            number="1",
            heading="Additional Modules",
            paragraphs=[
                "With effect from 1 October 2025, Nimbus will make available to Customer the Demand Forecasting "
                "Module and the Supplier Scorecard Module (together, the &quot;Additional Modules&quot;) for the "
                "remainder of the Subscription Term under the Original Order Form.",
                "The Additional Modules are generally available products that Nimbus sells separately, and are "
                "delivered through the same hosted Platform to which Customer already subscribes. No "
                "implementation services are required.",
            ],
        ),
        Section(
            number="2",
            heading="Additional Fees",
            paragraphs=[
                "The fee for the Additional Modules for the period from 1 October 2025 to 30 November 2026 "
                "(fourteen months) is EUR 48,000 in aggregate.",
                "Nimbus's published rate card price for the two Additional Modules over the same period is EUR "
                "78,400. The parties agree that the fee stated above reflects preferential pricing granted in "
                "recognition of Customer's existing commitment.",
                "The additional fee is invoiced in two instalments of EUR 24,000 on 1 October 2025 and 1 April "
                "2026, payable within thirty (30) days of the invoice date.",
            ],
        ),
        Section(
            number="3",
            heading="No Other Changes",
            paragraphs=[
                "The Subscription Term, termination provisions and all other commercial terms of the Original "
                "Order Form are unchanged. The end date of the Subscription Term remains 30 November 2026.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics GmbH", "K. Brandt", "Geschäftsführer",
        "Orchid Retail Holdings AG", "L. Fenner", "Head of Group Accounting",
    ),
    truth=ContractTruth(
        customer="Orchid Retail Holdings AG",
        supplier="Nimbus Analytics GmbH",
        agreement_type=AgreementType.AMENDMENT,
        currency="EUR",
        effective_date=date(2025, 9, 1),
        stated_term_months=14,
        termination_for_convenience=None,
        termination_notice_days=None,
        net_days=30,
        total_fixed_consideration=Decimal("48000"),
        obligations=(TruthObligation(ObligationKind.SAAS_SUBSCRIPTION, Decimal("48000")),),
        judgments=(
            JudgmentType.CONTRACT_MODIFICATION,
            JudgmentType.SSP_NOT_OBSERVABLE,
        ),
    ),
    commentary=(
        "A textbook modification, and the corpus's clearest case of a document that cannot be assessed alone. "
        "The added modules are plainly distinct -- separately sold, no implementation, same platform -- so the "
        "only question standing between this and separate-contract treatment is whether EUR 48,000 reflects "
        "their standalone selling price. The document helpfully states a rate card price that is 39% higher, "
        "which answers nothing: a rate card is not an SSP either."
    ),
)


NIMBUS_OF_BEACON = ContractSpec(
    doc_id="nimbus-of-beacon",
    title="ORDER FORM NA-OF-2025-0304",
    subtitle="Perpetual Licence -- Nimbus Analytics, Inc. and Beacon Municipal Utilities",
    supplier="Nimbus Analytics, Inc.",
    customer="Beacon Municipal Utilities Authority",
    preamble=(
        "This Order Form is entered into as of May 20, 2025 between Nimbus Analytics, Inc. (&quot;Nimbus&quot;) "
        "and Beacon Municipal Utilities Authority (&quot;Customer&quot;), a public body constituted under the "
        "laws of the State of Ohio."
    ),
    sections=[
        Section(
            number="1",
            heading="Licence Grant",
            paragraphs=[
                "Nimbus grants Customer a perpetual, non-exclusive licence to install and use the Nimbus Grid "
                "Analytics software (the &quot;Software&quot;) on Customer's own infrastructure, for up to two "
                "hundred (200) named users.",
                "The Software is delivered by secure download. The licence is effective, and Customer's right to "
                "use the Software begins, on delivery of the download credentials and licence key, which Nimbus "
                "will provide within five (5) business days of execution of this Order Form.",
                "The licence granted under this Section is not contingent on Customer purchasing maintenance, "
                "and does not terminate if maintenance lapses.",
            ],
        ),
        Section(
            number="2",
            heading="Fees",
            paragraphs=[],
            table=FeeTable(
                columns=["Item", "Fee"],
                rows=[
                    ["Perpetual licence, Grid Analytics (200 users)", "USD 310,000"],
                    ["Maintenance and support, 12 months", "USD 62,000"],
                    ["On-site administrator training (4 days)", "USD 18,000"],
                    ["Cartos Spatial Database licence, 12 months (third party)", "USD 45,000"],
                    ["Total", "USD 435,000"],
                ],
            ),
        ),
        Section(
            number="3",
            heading="Third Party Software",
            paragraphs=[
                "The Software requires the Cartos Spatial Database, which is licensed by Cartos Geospatial LLC, "
                "an unaffiliated third party. Nimbus procures that licence on Customer's behalf and passes the "
                "cost through at the price charged to Nimbus by Cartos, without mark-up.",
                "The Cartos licence is granted directly by Cartos to Customer under Cartos's own end user terms, "
                "and Customer is responsible for compliance with those terms. Nimbus does not warrant the Cartos "
                "Spatial Database and has no obligation to support it. Cartos sets the licence price and may "
                "revise it on renewal.",
            ],
        ),
        Section(
            number="4",
            heading="Maintenance and Support",
            paragraphs=[
                "For twelve (12) months from delivery, Nimbus will provide telephone and email support during "
                "US business hours and will make available all corrective patches and version updates to the "
                "Software released during that period.",
                "Maintenance renews annually at Nimbus's then-current published maintenance rate, at Customer's "
                "option.",
            ],
        ),
        Section(
            number="5",
            heading="Training",
            paragraphs=[
                "Nimbus will deliver four (4) days of on-site administrator training at Customer's premises, on "
                "dates to be agreed, within six (6) months of delivery of the Software. Training is a standard "
                "Nimbus course and is offered separately to other customers at the same rate.",
            ],
        ),
        Section(
            number="6",
            heading="Payment",
            paragraphs=[
                "All fees are invoiced on delivery of the licence key and are payable within forty-five (45) "
                "days of the invoice date.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics, Inc.", "D. Ashworth", "VP Commercial",
        "Beacon Municipal Utilities Authority", "R. Danvers", "Director of Finance",
    ),
    truth=ContractTruth(
        customer="Beacon Municipal Utilities Authority",
        supplier="Nimbus Analytics, Inc.",
        agreement_type=AgreementType.ORDER_FORM,
        currency="USD",
        effective_date=date(2025, 5, 20),
        stated_term_months=12,
        termination_for_convenience=None,
        termination_notice_days=None,
        net_days=45,
        total_fixed_consideration=Decimal("435000"),
        obligations=(
            TruthObligation(ObligationKind.SOFTWARE_LICENSE, Decimal("310000")),
            TruthObligation(ObligationKind.SUPPORT, Decimal("62000")),
            TruthObligation(ObligationKind.TRAINING, Decimal("18000")),
            TruthObligation(ObligationKind.THIRD_PARTY_RESALE, Decimal("45000")),
        ),
        judgments=(
            JudgmentType.PRINCIPAL_VS_AGENT,
            JudgmentType.SSP_NOT_OBSERVABLE,
        ),
    ),
    commentary=(
        "The one contract in the corpus where an obligation transfers at a point in time. It also carries every "
        "indicator that points towards agent treatment on the Cartos line -- no mark-up, third party sets the "
        "price, licence granted directly to the customer, no warranty or support obligation -- which is exactly "
        "why it is a judgment and not a rule: those are indicators, and control is the criterion."
    ),
)


NIMBUS_SOW_TESSELLATE = ContractSpec(
    doc_id="nimbus-sow-tessellate",
    title="STATEMENT OF WORK SOW-2025-041",
    subtitle="Data Platform Migration -- Nimbus Analytics, Inc. and Tessellate Media LLC",
    supplier="Nimbus Analytics, Inc.",
    customer="Tessellate Media LLC",
    preamble=(
        "This Statement of Work is entered into as of August 4, 2025 under the Professional Services Agreement "
        "between Nimbus Analytics, Inc. (&quot;Nimbus&quot;) and Tessellate Media LLC (&quot;Customer&quot;) "
        "dated February 2, 2024."
    ),
    sections=[
        Section(
            number="1",
            heading="Scope of Work",
            paragraphs=[
                "Nimbus will migrate Customer's advertising performance data from its existing on-premise "
                "warehouse to the Nimbus Platform, comprising discovery and mapping, construction of the "
                "extract-transform-load pipelines, two parallel-run cycles, and cutover.",
                "The work is a single integrated engagement delivered by one Nimbus team. The individual phases "
                "are not separately saleable and Customer receives no usable output until cutover is complete.",
            ],
        ),
        Section(
            number="2",
            heading="Fees",
            paragraphs=[
                "The fixed fee for the work described in Section 1 is USD 240,000, invoiced monthly in arrears "
                "in proportion to the percentage of the work completed, as agreed between the parties' project "
                "managers at each month end. Invoices are payable within thirty (30) days.",
            ],
        ),
        Section(
            number="3",
            heading="Delivery Incentive",
            paragraphs=[
                "If cutover is achieved on or before January 31, 2026, Customer shall pay Nimbus an additional "
                "fee of USD 30,000.",
                "If cutover is achieved after February 28, 2026 for reasons attributable to Nimbus, the fixed "
                "fee shall be reduced by USD 2,500 for each complete week of delay, up to a maximum reduction of "
                "USD 25,000.",
                "Delay attributable to Customer's failure to provide access to source systems, or to the "
                "unavailability of Customer personnel, does not count towards the reduction in this Section.",
            ],
        ),
        Section(
            number="4",
            heading="Term",
            paragraphs=[
                "This Statement of Work commences on September 1, 2025 and continues until completion of the "
                "work, expected to be no later than February 28, 2026.",
            ],
        ),
        Section(
            number="5",
            heading="Acceptance",
            paragraphs=[
                "Cutover is achieved when Customer's production reporting runs entirely on the Nimbus Platform "
                "for five (5) consecutive business days without a severity-one defect. Customer will confirm "
                "acceptance in writing within five (5) business days of that condition being met.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics, Inc.", "T. Larkin", "Director of Professional Services",
        "Tessellate Media LLC", "J. Whitfield", "VP Finance",
    ),
    truth=ContractTruth(
        customer="Tessellate Media LLC",
        supplier="Nimbus Analytics, Inc.",
        agreement_type=AgreementType.STATEMENT_OF_WORK,
        currency="USD",
        effective_date=date(2025, 8, 4),
        stated_term_months=None,
        termination_for_convenience=None,
        termination_notice_days=None,
        net_days=30,
        total_fixed_consideration=Decimal("240000"),
        obligations=(TruthObligation(ObligationKind.PROFESSIONAL_SERVICES, Decimal("240000")),),
        judgments=(JudgmentType.VARIABLE_CONSIDERATION_CONSTRAINT,),
    ),
    commentary=(
        "Variable consideration in both directions -- a bonus for early delivery and a penalty for late -- on a "
        "single performance obligation. Because there is only one obligation there is nothing to allocate, so no "
        "SSP question arises, which is the point: the corpus should not produce the same three flags on every "
        "document."
    ),
)


NIMBUS_OF_NORTHGATE = ContractSpec(
    doc_id="nimbus-of-northgate",
    title="ORDER FORM NA-OF-2025-0412",
    subtitle="Enterprise Agreement -- Nimbus Analytics, Inc. and Northgate Financial Services, Inc.",
    supplier="Nimbus Analytics, Inc.",
    customer="Northgate Financial Services, Inc.",
    preamble=(
        "This Order Form is entered into as of October 9, 2025 between Nimbus Analytics, Inc. "
        "(&quot;Nimbus&quot;) and Northgate Financial Services, Inc. (&quot;Customer&quot;) under the Master "
        "Subscription Agreement between the parties dated June 30, 2023."
    ),
    sections=[
        Section(
            number="1",
            heading="Subscription",
            paragraphs=[
                "The Subscription Term commences on January 1, 2026 and continues for sixty (60) months.",
                "Customer commits to an enterprise-wide deployment covering all business units listed in "
                "Schedule A, with a committed minimum of eight hundred (800) licensed users.",
            ],
            table=FeeTable(
                columns=["Item", "List Rate", "Fee"],
                rows=[
                    ["Enterprise Platform subscription (60 months)", "USD 1,380,000", "USD 1,050,000"],
                    ["Enterprise Support, 60 months", "USD 195,000", "USD 150,000"],
                    ["Total committed fees", "USD 1,575,000", "USD 1,200,000"],
                ],
            ),
        ),
        Section(
            number="2",
            heading="Payment Schedule",
            paragraphs=[
                "Notwithstanding Section 3 of the Agreement, the committed fees are payable as follows: "
                "twenty-five percent (25%), being USD 300,000, on execution of this Order Form; and the balance "
                "of USD 900,000 in four (4) equal annual instalments of USD 225,000 on each of January 1, 2027, "
                "January 1, 2028, January 1, 2029 and January 1, 2030.",
                "The parties agree that the aggregate amount payable under this Order Form is the same "
                "irrespective of the payment schedule, and no interest is charged on the deferred instalments.",
                "Each instalment is payable within thirty (30) days of the invoice date.",
            ],
        ),
        Section(
            number="3",
            heading="Volume Rebate",
            paragraphs=[
                "If Customer's licensed user count exceeds one thousand two hundred (1,200) at any point during "
                "a contract year, Nimbus will credit Customer with a rebate equal to five percent (5%) of the "
                "fees invoiced for that contract year.",
                "The rebate is applied against the next instalment falling due, or refunded in cash if no further "
                "instalment remains.",
            ],
        ),
        Section(
            number="4",
            heading="Termination",
            paragraphs=[
                "Customer may not terminate this Order Form for convenience. If Customer terminates for Nimbus's "
                "material breach, Nimbus shall refund a pro rata portion of amounts paid in respect of the "
                "unexpired portion of the Subscription Term.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics, Inc.", "D. Ashworth", "VP Commercial",
        "Northgate Financial Services, Inc.", "A. Sundaram", "Controller",
    ),
    truth=ContractTruth(
        customer="Northgate Financial Services, Inc.",
        supplier="Nimbus Analytics, Inc.",
        agreement_type=AgreementType.ORDER_FORM,
        currency="USD",
        effective_date=date(2025, 10, 9),
        stated_term_months=60,
        termination_for_convenience=False,
        termination_notice_days=None,
        net_days=30,
        total_fixed_consideration=Decimal("1200000"),
        obligations=(
            TruthObligation(ObligationKind.SAAS_SUBSCRIPTION, Decimal("1050000")),
            TruthObligation(ObligationKind.SUPPORT, Decimal("150000")),
        ),
        judgments=(
            JudgmentType.SIGNIFICANT_FINANCING,
            JudgmentType.VARIABLE_CONSIDERATION_CONSTRAINT,
            JudgmentType.SSP_NOT_OBSERVABLE,
        ),
    ),
    commentary=(
        "Payment stretched over five years with an express statement that the price does not change with the "
        "schedule and no interest is charged. That sentence reads as reassurance and is actually the opposite: "
        "the customer is receiving credit, and whether that is a significant financing component depends on "
        "rates at inception, not on what the paper says about interest."
    ),
)


NIMBUS_OF_PINEGROVE = ContractSpec(
    doc_id="nimbus-of-pinegrove",
    title="ORDER FORM NA-OF-2025-0195",
    subtitle="Nimbus Analytics, Inc. and Pinegrove Dental Partners, LLC",
    supplier="Nimbus Analytics, Inc.",
    customer="Pinegrove Dental Partners, LLC",
    preamble=(
        "This Order Form is entered into as of February 18, 2025 between Nimbus Analytics, Inc. "
        "(&quot;Nimbus&quot;) and Pinegrove Dental Partners, LLC (&quot;Customer&quot;) under the Nimbus "
        "Standard Subscription Terms."
    ),
    sections=[
        Section(
            number="1",
            heading="Subscription",
            paragraphs=[
                "Nimbus will provide Customer with access to the Nimbus Practice Insights service for twelve "
                "(12) months commencing March 1, 2025, for up to twelve (12) named users.",
            ],
            table=FeeTable(
                columns=["Item", "List Rate", "Fee"],
                rows=[
                    ["Practice Insights subscription, 12 users (12 months)", "USD 14,400", "USD 14,400"],
                    ["Total", "USD 14,400", "USD 14,400"],
                ],
            ),
        ),
        Section(
            number="2",
            heading="Payment",
            paragraphs=[
                "The subscription fee is invoiced in full in advance on the commencement date and is payable "
                "within thirty (30) days of the invoice date.",
                "No implementation, configuration or training services are included or required. Customer "
                "self-provisions through the Nimbus web console.",
            ],
        ),
        Section(
            number="3",
            heading="Renewal",
            paragraphs=[
                "This Order Form renews automatically for successive twelve (12) month terms at Nimbus's "
                "then-current published list rate, unless either party gives written notice of non-renewal not "
                "less than thirty (30) days before the end of the then-current term.",
            ],
        ),
        Section(
            number="4",
            heading="Termination",
            paragraphs=[
                "Neither party may terminate this Order Form for convenience during a term. Either party may "
                "terminate for material breach not cured within thirty (30) days of written notice.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics, Inc.", "C. Meeks", "Inside Sales Manager",
        "Pinegrove Dental Partners, LLC", "E. Barlow", "Managing Partner",
    ),
    truth=ContractTruth(
        customer="Pinegrove Dental Partners, LLC",
        supplier="Nimbus Analytics, Inc.",
        agreement_type=AgreementType.ORDER_FORM,
        currency="USD",
        effective_date=date(2025, 2, 18),
        stated_term_months=12,
        termination_for_convenience=False,
        termination_notice_days=None,
        net_days=30,
        total_fixed_consideration=Decimal("14400"),
        obligations=(TruthObligation(ObligationKind.SAAS_SUBSCRIPTION, Decimal("14400")),),
        judgments=(),
    ),
    commentary=(
        "One obligation, sold at list, renewing at list, no services, no variability, no termination right. "
        "Nothing to allocate and nothing to judge. Most SaaS revenue looks like this, and a reviewer that raises "
        "a flag here is one a controller will stop reading within a month -- which is why it is measured."
    ),
)


NIMBUS_MSA_VANTAGE = ContractSpec(
    doc_id="nimbus-msa-vantage",
    title="MASTER SUBSCRIPTION AGREEMENT",
    subtitle="Nimbus Analytics, Inc. and Vantage Freight Systems, Inc.",
    supplier="Nimbus Analytics, Inc.",
    customer="Vantage Freight Systems, Inc.",
    preamble=(
        "This Master Subscription Agreement is entered into as of April 7, 2025 between Nimbus Analytics, Inc. "
        "(&quot;Nimbus&quot;) and Vantage Freight Systems, Inc. (&quot;Customer&quot;). This Agreement was "
        "negotiated from Customer's standard purchasing terms and departs in several respects from Nimbus's own "
        "form."
    ),
    sections=[
        Section(
            number="1",
            heading="Subscription and Term",
            paragraphs=[
                "Nimbus will provide Customer with access to the Platform for an initial term of thirty-six (36) "
                "months from the Effective Date, renewing thereafter for successive twelve (12) month terms "
                "unless either party gives notice of non-renewal.",
            ],
        ),
        Section(
            number="2",
            heading="Fees",
            paragraphs=[
                "Customer shall pay an annual subscription fee of USD 264,000, invoiced annually in advance and "
                "payable within forty-five (45) days of the invoice date.",
            ],
        ),
        Section(
            number="3",
            heading="Termination",
            paragraphs=[
                "Either party may terminate this Agreement for material breach not cured within thirty (30) "
                "days of written notice.",
                "Customer may additionally terminate this Agreement for convenience at any time after the first "
                "twelve (12) months of the initial term, on ninety (90) days' written notice, without further "
                "liability save for fees accrued to the effective date of termination.",
            ],
        ),
        Section(
            number="4",
            heading="Suspension",
            paragraphs=[
                "Nimbus may suspend Customer's access for non-payment of undisputed invoices, for breach of the "
                "acceptable use policy, or where required by law. Suspension is not termination and does not "
                "relieve Customer of its payment obligations.",
            ],
        ),
        Section(
            number="5",
            heading="General",
            paragraphs=[
                "Customer's obligation to pay the subscription fees is unconditional for the full initial term. "
                "Customer may not terminate this Agreement or reduce its committed spend prior to the end of the "
                "initial term other than under Section 3.1 (termination for material breach), and no right of "
                "termination for convenience is granted under this Agreement.",
                "This Agreement is governed by the laws of the State of New York. The parties agree that no "
                "course of dealing or prior draft shall be used to interpret its terms.",
                "In the event of an inconsistency between provisions of this Agreement, the parties shall "
                "negotiate in good faith to resolve it.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics, Inc.", "D. Ashworth", "VP Commercial",
        "Vantage Freight Systems, Inc.", "G. Petrossian", "Head of Procurement",
    ),
    truth=ContractTruth(
        customer="Vantage Freight Systems, Inc.",
        supplier="Nimbus Analytics, Inc.",
        agreement_type=AgreementType.MASTER_AGREEMENT,
        currency="USD",
        effective_date=date(2025, 4, 7),
        stated_term_months=36,
        termination_for_convenience=None,
        termination_notice_days=None,
        net_days=45,
        total_fixed_consideration=None,
        obligations=(TruthObligation(ObligationKind.SAAS_SUBSCRIPTION, Decimal("264000")),),
        judgments=(JudgmentType.ENFORCEABLE_TERM,),
    ),
    commentary=(
        "Section 3.2 grants a termination right for convenience and Section 5.1 says none is granted, and the "
        "boilerplate that would normally break the tie only says the parties will talk about it. This is not a "
        "trick: it is what negotiating from the customer's paper produces when two people redline different "
        "sections. The correct machine answer is *ambiguous* with both clauses cited -- not a coin flip between "
        "them, and not silence."
    ),
)


NIMBUS_OF_QUARRY = ContractSpec(
    doc_id="nimbus-of-quarry",
    title="ORDER FORM NA-OF-2025-0377",
    subtitle="Connected Assets Bundle -- Nimbus Analytics, Inc. and Quarry Industrial Supply Co.",
    supplier="Nimbus Analytics, Inc.",
    customer="Quarry Industrial Supply Co.",
    preamble=(
        "This Order Form is entered into as of September 22, 2025 between Nimbus Analytics, Inc. "
        "(&quot;Nimbus&quot;) and Quarry Industrial Supply Co. (&quot;Customer&quot;) under the Master "
        "Subscription Agreement dated September 22, 2025."
    ),
    sections=[
        Section(
            number="1",
            heading="Bundle Contents",
            paragraphs=[
                "Nimbus will provide the Connected Assets bundle for a term of thirty-six (36) months commencing "
                "November 1, 2025, comprising the Platform subscription, standard support, and the gateway "
                "hardware described in Section 3.",
            ],
            table=FeeTable(
                columns=["Item", "Fee"],
                rows=[
                    ["Connected Assets Platform subscription (36 months)", "USD 396,000"],
                    ["Standard Support, 36 months", "USD 36,000"],
                    ["Sentinel Systems SG-40 gateway units (110 units)", "USD 88,000"],
                    ["Total", "USD 520,000"],
                ],
            ),
        ),
        Section(
            number="2",
            heading="Service Level Credits",
            paragraphs=[
                "Nimbus commits to monthly Platform availability of 99.5%. If availability in any calendar month "
                "falls below that level, Customer is entitled to a credit against the following month's "
                "subscription fee, calculated as two percent (2%) of the monthly fee for each full 0.5% by which "
                "availability falls short, up to a maximum of ten percent (10%) of the monthly fee.",
                "Credits are the sole remedy for failure to meet the availability commitment and are applied "
                "automatically without the need for a claim by Customer.",
            ],
        ),
        Section(
            number="3",
            heading="Gateway Hardware",
            paragraphs=[
                "The SG-40 gateway units are manufactured and supplied by Sentinel Systems Inc., an unaffiliated "
                "third party. Nimbus purchases the units, holds them in its own inventory, and resells them to "
                "Customer at a price Nimbus sets.",
                "Nimbus bears the risk of loss for the units until delivery to Customer's site, is responsible "
                "for their configuration and installation, and provides the first line warranty for the units "
                "for the duration of the subscription term. Customer's sole recourse in respect of a defective "
                "unit is to Nimbus.",
                "Title to the units passes to Customer on delivery.",
            ],
        ),
        Section(
            number="4",
            heading="Payment",
            paragraphs=[
                "Hardware fees are invoiced on delivery. Subscription and support fees are invoiced annually in "
                "advance. All invoices are payable within thirty (30) days of the invoice date.",
            ],
        ),
    ],
    signature_block=_signature(
        "Nimbus Analytics, Inc.", "D. Ashworth", "VP Commercial",
        "Quarry Industrial Supply Co.", "N. Halloran", "Finance Manager",
    ),
    truth=ContractTruth(
        customer="Quarry Industrial Supply Co.",
        supplier="Nimbus Analytics, Inc.",
        agreement_type=AgreementType.ORDER_FORM,
        currency="USD",
        effective_date=date(2025, 9, 22),
        stated_term_months=36,
        termination_for_convenience=None,
        termination_notice_days=None,
        net_days=30,
        total_fixed_consideration=Decimal("520000"),
        obligations=(
            TruthObligation(ObligationKind.SAAS_SUBSCRIPTION, Decimal("396000")),
            TruthObligation(ObligationKind.SUPPORT, Decimal("36000")),
            TruthObligation(ObligationKind.THIRD_PARTY_RESALE, Decimal("88000")),
        ),
        judgments=(
            JudgmentType.PRINCIPAL_VS_AGENT,
            JudgmentType.VARIABLE_CONSIDERATION_CONSTRAINT,
            JudgmentType.SSP_NOT_OBSERVABLE,
        ),
    ),
    commentary=(
        "Deliberately the mirror image of the Beacon third-party line. Here Nimbus takes inventory risk, sets "
        "the price, installs, and stands behind the warranty -- indicators pointing to principal. Same flag, "
        "opposite likely conclusion, which is the argument for raising the question rather than answering it: a "
        "rule that keyed on the phrase 'third party' would have got one of these two badly wrong."
    ),
)


MERIDIAN_MSA_ASTER = ContractSpec(
    doc_id="meridian-msa-aster",
    title="CLINICAL SERVICES AGREEMENT",
    subtitle="Meridian Clinical Partners, S.L. and Aster Therapeutics AB",
    supplier="Meridian Clinical Partners, S.L.",
    customer="Aster Therapeutics AB",
    preamble=(
        "This Clinical Services Agreement is entered into as of 3 March 2025 between Meridian Clinical Partners, "
        "S.L., a company incorporated in Spain (&quot;Meridian&quot;), and Aster Therapeutics AB, a company "
        "incorporated in Sweden (&quot;Sponsor&quot;), in respect of Sponsor's Phase II study AST-204 "
        "(the &quot;Study&quot;)."
    ),
    sections=[
        Section(
            number="1",
            heading="Services",
            paragraphs=[
                "Meridian will provide clinical trial site management services for the Study across up to "
                "twenty-two (22) investigator sites in six countries, comprising site identification and "
                "qualification, regulatory submission support, site initiation, ongoing monitoring visits, data "
                "management, and database lock.",
                "The activities described above are provided as an integrated service for the duration of the "
                "Study. Sponsor does not receive a separately usable deliverable at the conclusion of any "
                "individual activity, and Meridian's obligation is to deliver a locked, monitored clinical "
                "database meeting the protocol's requirements.",
            ],
        ),
        Section(
            number="2",
            heading="Service Fees",
            paragraphs=[
                "Sponsor shall pay Meridian the following fees on achievement of the corresponding milestones. "
                "Each milestone fee is earned only on achievement of the stated event and is not payable in "
                "part.",
            ],
            table=FeeTable(
                columns=["Milestone", "Fee"],
                rows=[
                    ["Activation of the first eight (8) investigator sites", "EUR 120,000"],
                    ["Enrolment of 50% of the target subject population", "EUR 260,000"],
                    ["Last subject last visit", "EUR 210,000"],
                    ["Database lock", "EUR 180,000"],
                    ["Total service fees", "EUR 770,000"],
                ],
            ),
        ),
        Section(
            number="3",
            heading="Investigator and Pass-Through Costs",
            paragraphs=[
                "In addition to the service fees, Sponsor shall reimburse investigator grants, ethics committee "
                "fees, central laboratory charges and subject travel costs (together, &quot;Pass-Through "
                "Costs&quot;).",
                "Meridian contracts with investigator sites as Sponsor's authorised representative and under "
                "budgets that Sponsor approves in advance. Pass-Through Costs are invoiced to Sponsor at the "
                "amount charged by the third party, without mark-up or administrative fee. Meridian holds "
                "Pass-Through funds in a designated account and returns any unspent balance to Sponsor at the "
                "conclusion of the Study.",
                "Sponsor sets the investigator grant budget and Meridian has no discretion to vary it. Meridian "
                "is not liable to investigator sites for amounts Sponsor fails to fund.",
            ],
        ),
        Section(
            number="4",
            heading="Term and Termination",
            paragraphs=[
                "This Agreement commences on the date stated above and continues until database lock, expected "
                "in the fourth quarter of 2027.",
                "Sponsor may terminate this Agreement or the Study at any time on thirty (30) days' written "
                "notice. On such termination, Sponsor shall pay Meridian for services performed to the effective "
                "date of termination, together with non-cancellable costs Meridian has committed on Sponsor's "
                "behalf and a close-out fee equal to fifteen percent (15%) of the service fees not yet earned.",
            ],
        ),
        Section(
            number="5",
            heading="Change Orders",
            paragraphs=[
                "Any change to the protocol, the number of sites, the enrolment target or the Study timeline "
                "that affects Meridian's scope of work shall be documented in a written change order signed by "
                "both parties, specifying the change in scope and the corresponding change in fees.",
            ],
        ),
        Section(
            number="6",
            heading="Invoicing",
            paragraphs=[
                "Milestone fees are invoiced on achievement of the relevant milestone. Pass-Through Costs are "
                "invoiced monthly in arrears. All invoices are payable within forty-five (45) days of the "
                "invoice date.",
            ],
        ),
    ],
    signature_block=_signature(
        "Meridian Clinical Partners, S.L.", "I. Ferreiro", "Managing Director",
        "Aster Therapeutics AB", "K. Lindqvist", "Chief Financial Officer",
    ),
    truth=ContractTruth(
        customer="Aster Therapeutics AB",
        supplier="Meridian Clinical Partners, S.L.",
        agreement_type=AgreementType.MASTER_AGREEMENT,
        currency="EUR",
        effective_date=date(2025, 3, 3),
        stated_term_months=None,
        termination_for_convenience=True,
        termination_notice_days=30,
        net_days=45,
        total_fixed_consideration=Decimal("770000"),
        obligations=(TruthObligation(ObligationKind.CLINICAL_SERVICES, Decimal("770000")),),
        judgments=(
            JudgmentType.ENFORCEABLE_TERM,
            JudgmentType.DISTINCT_UNCERTAIN,
            JudgmentType.PRINCIPAL_VS_AGENT,
            JudgmentType.VARIABLE_CONSIDERATION_CONSTRAINT,
        ),
    ),
    commentary=(
        "The densest document in the corpus and the one furthest from the SaaS pattern. Milestone fees that are "
        "all-or-nothing are variable consideration whatever the invoicing schedule suggests; the pass-through "
        "arrangement has every agent indicator including holding funds in a designated account; and the "
        "termination right carries a 15% close-out fee, which is the interesting case -- a penalty that exists "
        "but may not be substantive enough to make the stated term enforceable."
    ),
)


MERIDIAN_CHANGE_ORDER = ContractSpec(
    doc_id="meridian-change-order-03",
    title="CHANGE ORDER NO. 3",
    subtitle="To the Clinical Services Agreement dated 3 March 2025 -- Study AST-204",
    supplier="Meridian Clinical Partners, S.L.",
    customer="Aster Therapeutics AB",
    preamble=(
        "This Change Order No. 3 is entered into as of 14 January 2026 between Meridian Clinical Partners, S.L. "
        "(&quot;Meridian&quot;) and Aster Therapeutics AB (&quot;Sponsor&quot;) under Section 5 of the Clinical "
        "Services Agreement between the parties dated 3 March 2025 (the &quot;Agreement&quot;)."
    ),
    sections=[
        Section(
            number="1",
            heading="Change in Scope",
            paragraphs=[
                "Following a protocol amendment, Sponsor has increased the target subject population from 180 to "
                "260 subjects. To support the revised enrolment target, the number of investigator sites is "
                "increased from twenty-two (22) to thirty (30).",
                "Meridian will accordingly perform site identification, qualification, initiation and ongoing "
                "monitoring for the eight (8) additional sites, and will extend monitoring of all sites through "
                "the revised Study timeline.",
                "The additional services are of the same nature as those already being provided under the "
                "Agreement and are delivered by the same study team as part of the same integrated engagement.",
            ],
        ),
        Section(
            number="2",
            heading="Change in Fees",
            paragraphs=[
                "The service fees under Section 2 of the Agreement are increased by EUR 340,000, payable as "
                "follows: EUR 140,000 on activation of the eight additional sites, and EUR 200,000 on enrolment "
                "of the revised 50% target.",
                "The additional fees have been calculated using the unit rates in the budget appended to the "
                "Agreement, applied to the incremental scope.",
            ],
        ),
        Section(
            number="3",
            heading="Change in Timeline",
            paragraphs=[
                "The expected date of database lock is extended from the fourth quarter of 2027 to the second "
                "quarter of 2028. The milestone descriptions in Section 2 of the Agreement are otherwise "
                "unchanged.",
            ],
        ),
        Section(
            number="4",
            heading="Effect",
            paragraphs=[
                "Except as expressly amended by this Change Order, the Agreement remains in full force and "
                "effect. Payment terms remain net forty-five (45) days.",
            ],
        ),
    ],
    signature_block=_signature(
        "Meridian Clinical Partners, S.L.", "I. Ferreiro", "Managing Director",
        "Aster Therapeutics AB", "K. Lindqvist", "Chief Financial Officer",
    ),
    truth=ContractTruth(
        customer="Aster Therapeutics AB",
        supplier="Meridian Clinical Partners, S.L.",
        agreement_type=AgreementType.AMENDMENT,
        currency="EUR",
        effective_date=date(2026, 1, 14),
        stated_term_months=None,
        termination_for_convenience=None,
        termination_notice_days=None,
        net_days=45,
        total_fixed_consideration=Decimal("340000"),
        obligations=(TruthObligation(ObligationKind.CLINICAL_SERVICES, Decimal("340000")),),
        judgments=(JudgmentType.CONTRACT_MODIFICATION,),
    ),
    commentary=(
        "The counterpart to the Orchid amendment and the reason both are in the corpus. Orchid adds a distinct "
        "product; this adds more of the same service to an engagement that is a single performance obligation, "
        "so it cannot be a separate contract and the question is prospective versus cumulative catch-up. Same "
        "flag, entirely different answer, and nothing in the document says which."
    ),
)


CORPUS: list[ContractSpec] = [
    NIMBUS_MSA_CALDERWOOD,
    NIMBUS_OF_CALDERWOOD,
    NIMBUS_OF_HELIX,
    NIMBUS_AMENDMENT_ORCHID,
    NIMBUS_OF_BEACON,
    NIMBUS_SOW_TESSELLATE,
    NIMBUS_OF_NORTHGATE,
    NIMBUS_OF_PINEGROVE,
    NIMBUS_MSA_VANTAGE,
    NIMBUS_OF_QUARRY,
    MERIDIAN_MSA_ASTER,
    MERIDIAN_CHANGE_ORDER,
]


def spec_by_id(doc_id: str) -> ContractSpec:
    for spec in CORPUS:
        if spec.doc_id == doc_id:
            return spec
    raise KeyError(f"no contract spec with id {doc_id!r}")
