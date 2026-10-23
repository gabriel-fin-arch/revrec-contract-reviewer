# ADR 0002: Judgments are raised to a person, never answered

- Status: Accepted, 23 October 2026
- Decision owner: Gabriel

## Context

ASC 606 review turns on judgment calls — whether a termination right makes
the term unenforceable, whether obligations are distinct, whether the price
carries a significant financing component. These are accounting decisions
with real revenue consequences. A model answering them would produce a memo
that looks finished and isn't.

## Decision

The pipeline flags each of the eight judgment calls with the evidence for
and against, and stops there. The memo presents the flag, the clauses it
rests on, and what a reviewer should read first. Concluding is the
reviewer's job, and the taxonomy behind the flags is defended by argument
in `docs/judgment-calls.md` — the only way a taxonomy can be defended.

## Alternatives considered

- **Let the model conclude with a confidence score.** Rejected: a
  conclusion with `0.72` attached invites exactly one question — "why
  0.72?" — and there is no honest answer.
- **Auto-conclude only the "easy" judgments.** Rejected: deciding which
  judgments are easy is itself the judgment.

## Consequences

There is no confidence score anywhere in the codebase; fields are
`extracted`, `ambiguous` or `absent`, three states that drive genuinely
different reviewer actions. The judgment flags are scored in the eval as
set comparison per contract, where false positives are the expensive ones:
a reviewer's trust is spent by spurious flags long before it is spent by
misses.
