# ADR 0006: Effort is set explicitly and every model call is measured

- Status: Accepted, 23 October 2026
- Decision owner: proposed by Claude Code, accepted by Gabriel

## Context

Model spend is a decision, not a side effect. An evaluation that can't say
what it cost, or a run whose effort was whatever the API defaulted to that
month, can't be compared to anything — not to a rerun, not to a baseline,
not to a budget.

## Decision

Every model run fixes the effort explicitly rather than inheriting an API
default, and saves every call it made — tokens, cost, seconds — into
`evals/results/`. No run starts without a prior estimate (`revrec estimate`
works it out without calling the API), an approval, and a ceiling. A run
that stops mid-way keeps the calls it already paid for: that's money and
evidence, and it doesn't get thrown away. A score can be recomputed from a
saved run without calling the model again.

## Alternatives considered

- **Default effort.** Rejected: a default is a moving target controlled by
  the provider, and two "identical" runs would differ by an invisible
  setting.
- **Aggregate cost only.** Rejected: a total without per-call detail can't
  show where the money went or reproduce anything.

## Consequences

Every published model figure carries its run configuration and its cost
with it. The spend-control rule is documented in the profile's HOW_I_WORK:
estimate, approval, ceiling, and a per-run and per-month limit set by the
owner.
