# The held-out test set

Seven synthetic contracts, made the same way as the twelve in `corpus/` and
just as invented: nothing here comes from any real agreement.

They were written on 18 October 2026, after the rules extractor and the
prompt, and committed with their gold records before either extractor had been
run on them. `revrec generate-corpus --set test` rebuilds them from
`src/revrec_contract_reviewer/corpus/heldout.py`, byte for byte.

Results on this set are reported separately and are not used: nothing seen
here goes back into the rules, the prompt or the scorer. A fix for something
this set shows is made against the development set, and this set measures it
again afterwards.

| Contract | Type | Currency | Judgments it should raise |
|---|---|---|---|
| `nimbus-of-larkspur` | order_form | USD | material_right, ssp_not_observable |
| `nimbus-of-fenwick` | order_form | GBP | enforceable_term, variable_consideration_constraint |
| `nimbus-sow-harbourline` | statement_of_work | USD | variable_consideration_constraint |
| `nimbus-amendment-wexford` | amendment | EUR | contract_modification, ssp_not_observable |
| `nimbus-of-saltmarsh` | order_form | USD | principal_vs_agent, ssp_not_observable |
| `nimbus-of-tamarind` | order_form | USD | distinct_uncertain, significant_financing, ssp_not_observable |
| `nimbus-of-alder` | order_form | USD | _none_ |

## What each one is for

### `nimbus-of-larkspur`

Three promises, one of which looks like the Calderwood implementation and isn't: configuration with the platform's own tools, which the customer could buy from a partner or skip. No distinct-or-not question should be raised. The renewal is priced as a stated discount on list, the second material-right case, and three obligations sold together leave the allocation question as they always do.

### `nimbus-of-fenwick`

The fee is stated in a sentence rather than a table, as short order forms often do. The customer can leave on thirty days' notice for half the remaining instalments, which sits between Helix's nothing and a full make-whole: the enforceable-term question in its usual unhelpful middle. Service credits only ever reduce the price, and they still make it variable.

### `nimbus-sow-harbourline`

A fixed fee invoiced on milestones, which the contract says in so many words, and a reduction for late delivery that makes the price variable anyway. One deliverable, so nothing to allocate; termination only for breach, so no question about the enforceable term.

### `nimbus-amendment-wexford`

A blend-and-extend: a lower annual fee now in exchange for two more years. What remains to be delivered is more months of the same distinct subscription, so whether this is a separate contract or a prospective modification turns on whether EUR 102,000 a year is a standalone selling price for those months -- the SSP question asked of a single obligation, as Orchid asks it. Annual billing in advance is not a financing arrangement, however many years it runs.

### `nimbus-of-saltmarsh`

Beacon and Quarry each point every indicator one way. This one splits them: Nimbus buys the licence, sets the price and can substitute the provider, which points to principal; Orbisat delivers the data and answers for its accuracy, which points to agent. The question has to be raised, and the document can't settle it.

### `nimbus-of-tamarind`

The licence is delivered on day one and paid for over twenty-one months with no interest, which is where a financing question starts. The customisation is the strong form of the distinct-or-not question: the contract says the software can't do its job until the work is done. Three obligations, or two, depending on the answer, and the allocation follows from it.

### `nimbus-of-alder`

The held-out control: one service, a fixed price, renewal at list, no way out. Like Pinegrove it should raise nothing, and anything it does raise is a false positive measured on a contract nobody tuned against.
