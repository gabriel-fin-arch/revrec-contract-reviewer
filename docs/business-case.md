# The business case, from the desk that would use it

A scope note first: I do not review contracts under ASC 606. That work
sits with the local teams and revenue accounting. What reaches my desk
in consolidation is the shadow those contracts leave behind — so this
page is written from the desk that would use the tool's output, not
from the desk that would run it. Figures are mine, rounded, and
deliberately anonymous.

## The problem today

What consolidation sees, every close: unbilled and contract-asset
balances that do not move, an AR aging I reconcile against the AR
control accounts, and adjustments that surface in Special Charges
because something changed after booking. Few entities carry a
significant unbilled balance, but when one does, it can sit there for
two closes before anyone asks why. The pattern that escapes most often
— seen from above — is a scope change that never made it into the
accounting on time, and an unbilled balance aging while it waits.

It costs me a day or two per close to reconcile those balances and
chase the explanations. That is not the real cost. The real cost is the
adjustment that appears as a Special Charge in close three instead of
a booking change in close one, and the audit question that follows it.

## What the tool would change

A memo-first pass at booking time: contract in, the eight judgment
flags from this project's memo out. A scope change flagged
`contract_modification` when it happens is a booking change — not a
Special Charge two closes later.

The saving I can defend on my side is the day or two per close I spend
reconciling unbilled and contract-asset balances and explaining
balances that a timely flag would have prevented. I will not quote the
review teams' hours; those are not mine to give.

## What it doesn't solve

It does not review the contract — the local teams and revenue
accounting still do that. The memo is a first read with the judgment
calls marked, not an opinion: whether a term is enforceable, whether a
right is material, stays with them. The tool says where to look; it
does not answer.

## What it would take to run it in a real close

- **Data:** contracts in one readable, access-controlled repository.
  Contracts are confidential; access is the constraint, not the format.
- **Ownership:** someone owns the flag queue — the local teams or
  revenue accounting — and the discipline to clear it at booking time,
  not at close.
- **Controls:** the flags feed the consolidation I reconcile, under
  the same preparer/approver split the close already runs on.
