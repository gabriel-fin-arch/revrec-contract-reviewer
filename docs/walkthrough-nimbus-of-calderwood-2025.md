# Walkthrough: nimbus-of-calderwood-2025

My own ASC 606 pass over this contract, done by hand before reading the tool
memo. I timed both.

## The contract in two lines

Nimbus Analytics sells Calderwood Logistics a 36-month Tier 3 platform
subscription, implementation and data migration, and premium support, for
USD 689,000 in total, under an order form (NA-OF-2025-0231) issued under the
master agreement of 15 January 2025. The customer cannot terminate for
convenience and can renew for one further year at USD 165,000.

## Step 1, the contract

There is a contract: an order form signed under an existing master agreement
(preamble, page 1). The stated term is thirty-six months from 1 April 2025
to 31 March 2028 (section 1, page 1), and it is enforceable for the full
term because section 1 takes away termination for convenience. So the
enforceable term and the stated term are the same 36 months. Nothing here is
optional or subject to approval.

## Step 2, performance obligations

Three things are promised (section 2, page 1): the platform subscription,
the implementation and data migration services, and premium support.

Support looks distinct to me: a named account manager, a one-hour response
target, access to updates. It does not change what the platform does and a
customer could in principle buy the platform without it.

Subscription vs implementation is where I hesitate, and the contract itself
tells me to. Section 3 (page 1) says the platform as configured "is
dependent on the connectors developed as part of these services" and the
analytics outputs "cannot be produced from the standard Platform
configuration alone". Read one way, implementation is a separate setup
service. Read the other way, what the customer actually bought is a
configured platform and the two move together. I would not sign off one or
two obligations without discussing that sentence, so for me the
distinctness of the platform and implementation is genuinely uncertain.
(Spoiler from the gold: it says the same.)

## Step 3, transaction price

Fixed. The fee schedule in section 2 (page 1) states USD 540,000 +
95,000 + 54,000 = 689,000, and it foots. No usage-based fees, no rebates,
no variable consideration anywhere in the document. The renewal price in
section 5 (USD 165,000) is not part of this transaction price; it only
matters for the material-right question below.

Financing: subscription and support are invoiced annually in advance,
three instalments of USD 198,000 (section 6, page 2), net 30. The longest
gap between payment and service is just under twelve months, so the
practical expedient for significant financing applies and I would not
adjust the price. I note it only because someone will ask.

## Step 4, allocation

Relative standalone selling price, and the SSP is not observable here:
nothing in this order form is sold on its own, the only price points are
the agreed fees and the list rates they were discounted from (section 2
shows both: list USD 782,000, agreed USD 689,000, about a 12% discount
overall). If I had to estimate SSP I would start from list rates and
adjust for the discounts Nimbus typically grants, and I would document
that as an estimate, not a measurement.

The renewal option needs a decision before allocation: section 5 (page 2)
grants a further 12 months at USD 165,000 and the parties state it is a
discount to the renewal list rate. If that discount exceeds what Calderwood
would get anyway as this class of customer, part of the USD 689,000 is a
prepayment for the renewal and has to be deferred. The document does not
say what the standard renewal discount is, so I would defer to the range
and flag it rather than guess a number.

## Step 5, recognition

Subscription: over time, straight line over 36 months. Continuous access,
customer benefits as it is provided.

Support: over time, straight line over 36 months. Same reasoning.

Implementation: this depends on step 2. If it is a distinct service, over time
as the work is done (it is configuration and migration work performed over
about four months, invoiced 50% on commencement and 50% on written
acceptance — section 3, page 1); the acceptance milestone does not move
recognition by itself. If it is not distinct, it is spread with the
platform. Either way it is not a point-in-time licence-style transfer.

## The eight judgment calls

| judgment | I would flag it? | tool flags it? | gold flags it? | comment |
|---|---|---|---|---|
| `enforceable_term` | no | no | no | stated 36 months, no termination for convenience; enforceable term = stated term |
| `contract_modification` | no | no | no | new order form under an existing MSA; nothing is being modified |
| `distinct_uncertain` | yes | **no** | yes | section 3's integration sentence makes platform vs implementation genuinely unclear; this is the one I'd raise in review |
| `material_right` | yes | yes | yes | renewal at a stated discount; needs the incremental-discount test; defer, don't guess |
| `principal_vs_agent` | no | no | no | Nimbus sells its own platform; no third-party component in this order form |
| `variable_consideration_constraint` | no | no | no | fixed fees only |
| `significant_financing` | no (noted) | no | no | annual advance invoicing, gap under 12 months; practical expedient |
| `ssp_not_observable` | yes | yes | yes | bundle only; estimate from list rates and typical discounts |

## Where the tool helped and where it didn't

Helped: the extraction was exact on every number and date I had read
myself — parties, dates, fee schedule, the fee column rather than the list
rate. The footing check passed. On the fields, I found nothing to
correct. That is worth saying plainly.

Didn't: it did not flag `distinct_uncertain`, even though section 3 is
sitting in its own extracted evidence and that sentence is the whole
reason the question is open. It treated three obligations as obviously
separate and moved on. If I had trusted the memo, that judgment would have
been made silently, the wrong way for a reviewer to find out. Its
`material_right` and `ssp_not_observable` flags were well grounded and
matched my reading.

## Time

- By hand, reading the PDF and working through the five steps with notes:
  about 50 minutes.
- Reading the tool memo and extracting the same conclusions from it:
  about 10 minutes.

Contract read before memo, on 28 October 2026.
