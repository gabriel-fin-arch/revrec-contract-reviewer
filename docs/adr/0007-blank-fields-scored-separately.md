# ADR 0007: Leaving blank what the contract doesn't say is scored separately

- Status: Accepted, 23 October 2026
- Decision owner: proposed by Claude Code, accepted by Gabriel

## Context

A tool that quietly fills gaps with plausible values is worse than one that
leaves them empty, because the gaps are where the interesting contracts
are. If silence is folded into ordinary precision and recall, an extractor
that invents a value for an unstated field loses the same fractional points
as one that misreads a stated one — and the two failures are not similar at
all in a review.

## Decision

Where the gold record says a contract does not state something, reporting a
value for it is counted as an **invention**, not a wrong answer. Silence is
reported as a count — unstated fields left blank out of all of them — and
deliberately not as precision and recall: each unstated field is either
left blank or invented, there is no third outcome to call a miss, so a
recall would read 1.00 whatever the extractor did. Blank is a state
(`absent`), not an omission: an `absent` field may not carry a value, and
the schema enforces it.

## Alternatives considered

- **Fold unstated fields into field precision/recall.** Rejected: it hides
  the most dangerous failure inside an average.
- **Score inventions as ordinary errors.** Rejected: a wrong term length is
  caught by the reviewer reading the clause; an invented one sends them
  looking for a clause that does not exist.

## Consequences

Both extractors kept all 21 unstated fields blank in the published runs,
and the corpus's deliberately quiet contracts exist to test exactly this.
The measure is the one the owner most wants to be asked about, and it sits
on the face of `docs/evaluation.md`.
