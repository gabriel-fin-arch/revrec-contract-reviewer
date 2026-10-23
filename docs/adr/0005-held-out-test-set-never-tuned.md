# ADR 0005: A held-out test set, committed before any run, that nothing is ever tuned on

- Status: Accepted, 23 October 2026
- Decision owner: Gabriel

## Context

Any metric you tune against stops measuring what you care about. If prompt
changes and thresholds are adjusted until the evaluation improves, the
evaluation becomes a description of the tuning, not of the extractor. The
project needs one set of contracts whose answers existed before anything
ran on them and that no change is ever fitted to.

## Decision

The held-out test set was written and committed with its answers before
anything ran on it, and nothing is tuned on it. Prompt and extractor
changes are argued from the development set, then measured on both sets. A
change that improves development and not test is dropped — that rule was
set before seeing results, and it held when the result was disappointing
(revrec #20). Correcting test-set answers after seeing results is only
legitimate for an authoring error, and doubtful cases stay as documented
open questions instead of touching the gold.

## Alternatives considered

- **Tune on everything and report the best run.** Rejected: the number
  would be un-defendable in a review meeting, which is the whole point of
  having one.
- **Cross-validation over a pooled set.** Rejected for this size: twelve
  contracts is not a benchmark, and the honest reading of any figure is
  already ±0.05 on the judgment row.

## Consequences

The held-out results mean what they appear to mean. The discipline is
visible in the history: the two test-gold disagreements (Wexford,
Harbourline) were kept as open questions when first seen, and the
Harbourline gold was only corrected later, as its own reviewed commit, once
the owner was sure it was an authoring error.
