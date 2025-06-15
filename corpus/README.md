# The corpus

Twelve synthetic contracts. Every party, product, price and person here is
invented; nothing in this directory comes from any real agreement.

They are generated, not stored: `revrec generate-corpus` rebuilds every PDF from
`src/revrec_contract_reviewer/corpus/library.py`, and the output is
byte-reproducible so a rebuild never shows up as a diff.

The documents are compressed. A real master subscription agreement runs forty
pages, most of which is indemnity, data protection and export control language
that has no bearing on revenue. What is kept here is the part a revenue reviewer
reads: term, termination, fees, what was promised, and how it gets paid for.

The supplier changes from document to document -- a US parent, its UK and German
subsidiaries, and the group's clinical services arm in Spain. That is the point
of a group-level review. Each local team reaches its own conclusion on its own
paper, and the differences only become visible when someone reads all twelve
next to each other.

| Contract | Type | Currency | Judgments it should raise |
|---|---|---|---|
| `nimbus-msa-calderwood` | master_agreement | USD | _none_ |
| `nimbus-of-calderwood-2025` | order_form | USD | distinct_uncertain, material_right, ssp_not_observable |
| `nimbus-of-helix` | order_form | GBP | enforceable_term, ssp_not_observable, variable_consideration_constraint |
| `nimbus-amendment-orchid` | amendment | EUR | contract_modification, ssp_not_observable |
| `nimbus-of-beacon` | order_form | USD | principal_vs_agent, ssp_not_observable |
| `nimbus-sow-tessellate` | statement_of_work | USD | variable_consideration_constraint |
| `nimbus-of-northgate` | order_form | USD | significant_financing, ssp_not_observable, variable_consideration_constraint |
| `nimbus-of-pinegrove` | order_form | USD | _none_ |
| `nimbus-msa-vantage` | master_agreement | USD | enforceable_term |
| `nimbus-of-quarry` | order_form | USD | principal_vs_agent, ssp_not_observable, variable_consideration_constraint |
| `meridian-msa-aster` | master_agreement | EUR | distinct_uncertain, enforceable_term, principal_vs_agent, variable_consideration_constraint |
| `meridian-change-order-03` | amendment | EUR | contract_modification |

## What each one is for

### `nimbus-msa-calderwood`

The framework document with no economics in it. A master agreement on its own is not a contract with a customer under ASC 606 -- there is no consideration and nothing has been ordered -- so the right answer here is a clean review with no judgments raised. Half the value of having it in the corpus is measuring that the reviewer stays quiet.

### `nimbus-of-calderwood-2025`

The workhorse of the corpus: a three-element bundle sold at an aggregate discount, with implementation language that leans hard on integration, and a renewal at a stated discount. The list rate column is there on purpose -- it is an input to the SSP question and it is routinely mistaken for the answer.

### `nimbus-of-helix`

A twenty-four month contract that may well be a one-month contract. Termination for convenience on 60 days' notice with an express statement that no further compensation is owed is about as clean a not-substantive termination penalty as you will see, and if the enforceable term really is two months, the transaction price the local team booked is wrong by an order of magnitude. Uncapped overage is the second question: the historical volume is disclosed, which tempts an estimate, but it is the customer's future deployment schedule that decides it.

### `nimbus-amendment-orchid`

A textbook modification, and the corpus's clearest case of a document that cannot be assessed alone. The added modules are plainly distinct -- separately sold, no implementation, same platform -- so the only question standing between this and separate-contract treatment is whether EUR 48,000 reflects their standalone selling price. The document helpfully states a rate card price that is 39% higher, which answers nothing: a rate card is not an SSP either.

### `nimbus-of-beacon`

The one contract in the corpus where an obligation transfers at a point in time. It also carries every indicator that points towards agent treatment on the Cartos line -- no mark-up, third party sets the price, licence granted directly to the customer, no warranty or support obligation -- which is exactly why it is a judgment and not a rule: those are indicators, and control is the criterion.

### `nimbus-sow-tessellate`

Variable consideration in both directions -- a bonus for early delivery and a penalty for late -- on a single performance obligation. Because there is only one obligation there is nothing to allocate, so no SSP question arises, which is the point: the corpus should not produce the same three flags on every document.

### `nimbus-of-northgate`

Payment stretched over five years with an express statement that the price does not change with the schedule and no interest is charged. That sentence reads as reassurance and is actually the opposite: the customer is receiving credit, and whether that is a significant financing component depends on rates at inception, not on what the paper says about interest.

### `nimbus-of-pinegrove`

One obligation, sold at list, renewing at list, no services, no variability, no termination right. Nothing to allocate and nothing to judge. Most SaaS revenue looks like this, and a reviewer that raises a flag here is one a controller will stop reading within a month -- which is why it is measured.

### `nimbus-msa-vantage`

Section 3.2 grants a termination right for convenience and Section 5.1 says none is granted, and the boilerplate that would normally break the tie only says the parties will talk about it. This is not a trick: it is what negotiating from the customer's paper produces when two people redline different sections. The correct machine answer is *ambiguous* with both clauses cited -- not a coin flip between them, and not silence.

### `nimbus-of-quarry`

Deliberately the mirror image of the Beacon third-party line. Here Nimbus takes inventory risk, sets the price, installs, and stands behind the warranty -- indicators pointing to principal. Same flag, opposite likely conclusion, which is the argument for raising the question rather than answering it: a rule that keyed on the phrase 'third party' would have got one of these two badly wrong.

### `meridian-msa-aster`

The densest document in the corpus and the one furthest from the SaaS pattern. Milestone fees that are all-or-nothing are variable consideration whatever the invoicing schedule suggests; the pass-through arrangement has every agent indicator including holding funds in a designated account; and the termination right carries a 15% close-out fee, which is the interesting case -- a penalty that exists but may not be substantive enough to make the stated term enforceable.

### `meridian-change-order-03`

The counterpart to the Orchid amendment and the reason both are in the corpus. Orchid adds a distinct product; this adds more of the same service to an engagement that is a single performance obligation, so it cannot be a separate contract and the question is prospective versus cumulative catch-up. Same flag, entirely different answer, and nothing in the document says which.
