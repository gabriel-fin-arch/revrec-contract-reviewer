# The judgment calls

Eight decisions this tool raises and refuses to answer.

They share one property, and it is the property that justifies the list
existing: **answering them requires information that is not in the contract.**
Not "the model isn't confident enough" — genuinely not in the document. An
entity's typical discount range, its estimate of how much variable
consideration will reverse, its assessment of whether it controls a third-party
service before transfer: none of that is written on the paper, so no amount of
better reading gets you there.

That is a much stronger position than a confidence threshold. A threshold
invites "can you tune it up a bit?" and has no answer. This one does: the
information lives somewhere else.

The flags are ordered by the step of the five-step model they belong to, and
the ordering is not cosmetic. You cannot sensibly allocate a transaction price
until you have settled what the obligations are, so working the list top-down
is working it in the only order that doesn't make you redo things.

---

## Step 1

### Enforceable term

**Raised when** the contract grants a termination right without cause, or two
clauses disagree about whether it does.

**Why a human.** Whether a termination penalty is substantive turns on how
enforceable the compensation clause is in the governing jurisdiction. That is a
legal reading of the words, not a fact stated by them.

The corpus has both interesting shapes. The Helix order form runs twenty-four
months and either party may leave on sixty days' notice, with an express
statement that no further compensation is owed — about as clean a
non-substantive penalty as you will see, and if the enforceable term really is
two months, the transaction price the local team booked is wrong by an order of
magnitude. The Meridian clinical services agreement grants termination on
thirty days' notice with a close-out fee of 15% of unearned service fees, which
is the genuinely hard case: a penalty that exists and may or may not be enough.

The Vantage master agreement is the third shape. Section 3.2 grants a
termination right for convenience; section 5.1 says none is granted; the
boilerplate that would normally break the tie only says the parties will
negotiate in good faith. This is not a trick — it is what negotiating from the
customer's paper produces when two people redline different sections. The right
machine answer is `ambiguous` with both clauses cited. Not a coin flip, and not
silence.

### Contract modification

**Raised when** the document amends an existing agreement rather than standing
alone.

**Why a human.** Whether a modification is a separate contract, a prospective
change, or a cumulative catch-up depends on whether the added goods are
distinct and priced at their standalone selling price. The agreement being
modified is a different document, so this one cannot be assessed from the paper
in front of it at all.

The two amendments in the corpus are there to make that concrete. The Orchid
amendment adds two separately-sold modules with no implementation work — plainly
distinct, so the only question is the pricing. The Meridian change order adds
eight more sites to an engagement that is a single performance obligation, so it
cannot be a separate contract and the question is prospective versus cumulative
catch-up. Same flag, entirely different answer, and nothing in either document
says which.

---

## Step 2

### Distinct or not

**Raised when** the contract describes one promise as customising, integrating
with, or depending on another.

**Why a human.** Whether a service significantly customises or is highly
interdependent with another promise depends on how the work is actually
delivered, which the contract describes only in general terms.

The Calderwood order form is the standard trap: implementation services
described as developing custom connectors, with an explicit acknowledgement that
the contracted analytics cannot be produced from the standard platform alone.
That is strong language and it still is not the answer, because the question is
about the delivery, not the drafting.

### Material right

**Raised when** the contract grants a renewal and describes its price as a
discount.

**Why a human.** A renewal discount is a material right only if it is
incremental to the range the entity typically grants. That range is pricing
data held by the entity, not a term of this contract.

The Pinegrove contract is the control: it renews automatically at the
then-current list rate. That is not a material right, no flag is raised, and
the absence is measured.

### Principal vs agent

**Raised when** the contract includes goods or services supplied by an
unaffiliated third party.

**Why a human.** Control of a third-party good or service before transfer
depends on the operating arrangement behind the contract — inventory risk,
pricing discretion, who is responsible for fulfilment.

The two contracts here are deliberate mirror images. Beacon: the Cartos licence
is granted directly by the vendor to the customer, passed through at cost with
no mark-up, with no warranty or support obligation on the seller, and the vendor
sets the price. Quarry: gateway units bought into the seller's own inventory,
priced at the seller's discretion, with risk of loss until delivery, installed
by the seller, warranted by the seller, and the customer's sole recourse is to
the seller.

Every indicator points one way in the first and the other way in the second. A
rule that keyed on the phrase "third party" would have got one of them badly
wrong. That is the case for raising the question rather than answering it,
made in two documents.

---

## Step 3

### Variable consideration constraint

**Raised when** the contract contains any term that makes the transaction price
something other than a fixed number.

**Why a human.** How much to include requires an estimate of the probability of
a significant reversal, which draws on the entity's own history with similar
contracts.

The Helix overage clause is instructive about a specific temptation: it
discloses that the customer's average monthly volume over the preceding six
months ran below the included allowance. That looks like the input to an
estimate and it isn't — the clause immediately says volumes may vary materially
with the customer's deployment schedule, which is a fact about the customer's
plans, not about the contract. There is no cap.

Milestone fees count too. The Meridian agreement pays on site activation,
enrolment, last-subject-last-visit and database lock, each earned only on
achievement and not payable in part. An invoicing schedule that looks
deterministic does not make the consideration fixed.

### Significant financing

**Raised when** payment of the fixed consideration is spread over more than
twelve months.

**Why a human.** Whether extended payment terms convey financing depends on the
intent behind them and on prevailing rates at inception, neither of which the
contract states.

Twelve months is the one number in the taxonomy, and it is not tuned — it is
the period ASC 606-10-32-18's practical expedient uses.

The Northgate order form spreads USD 1.2m over five years and states expressly
that the aggregate is the same whatever the schedule and that no interest is
charged. That sentence reads as reassurance and is close to the opposite: the
customer is receiving credit, and the contract saying "no interest" is part of
what raises the question rather than an answer to it.

---

## Step 4

### Standalone selling price

**Raised when** a contract contains more than one performance obligation, so
the transaction price has to be allocated.

**Why a human.** SSP is what the entity would charge selling separately. A
contract records what it charged this customer on this deal. The two coincide
only by accident.

This is the flag that shaped the schema. Every early version had an `ssp` field
on the obligation, and every one of them was a lie about where the number comes
from. What the model carries instead is `stated_price` and `list_price` — the
rate card figure where the order form prints one, clearly labelled as an input
and never as the answer.

Note the trigger: more than one obligation, full stop. Not "a discount was
detected". If there are two promises the price must be allocated, and
allocation needs SSP, whether or not anyone gave a discount.

---

## What is deliberately not on this list

**Whether the contract exists and collection is probable.** Step 1's
collectibility assessment is a credit judgment about the customer, and nothing
in this pipeline looks at a customer's credit.

**Recognition over time versus at a point in time.** This is a check, not a
flag. Where the contract contains language about how control transfers, that
language is extracted and cited; where it contains none, the check *fails* and
says so. That is a finding about the drafting rather than a judgment call — a
local team's over-time conclusion may well be right, but this document does not
support it, and the difference between "unsupported" and "requires judgment" is
worth keeping.
