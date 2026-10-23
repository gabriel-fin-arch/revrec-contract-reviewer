# ADR 0004: The gold set is committed to the repo and read from disk, never regenerated

- Status: Accepted, 23 October 2026
- Decision owner: Gabriel

## Context

The gold set is the statement of what each contract requires — field
values, obligations, judgment flags, and which fields the contract leaves
unstated. It is an accounting judgment. A gold set that regenerates itself
from the code being evaluated can drift silently: change how a spec is
authored and "truth" moves with it, while every score stays flat.

## Decision

The gold set is written to `evals/gold/` and committed, and the eval reads
it from disk. It is never computed at run time and never produced by a
model. Changing it is a deliberate, reviewable act — the Harbourline and
Tessellate corrections were made that way, as their own commits with their
own review. Where the owner wasn't sure the gold was wrong, the disagreement
stayed as a documented open question rather than an edit after seeing
results.

## Alternatives considered

- **Regenerate gold from the corpus specs.** Rejected: truth would drift
  with the generator, and the eval would measure nothing.
- **Model-generated gold, human-reviewed.** Rejected: it would smuggle the
  model's reading into the yardstick the model is measured against.

## Consequences

The gold set is explicitly the owner's opinion — circular for the judgment
flags in a way the field scores are not, and `docs/evaluation.md` says so
plainly. The corpus PDFs are byte-reproducible (reportlab `invariant`, no
page compression, LF endings, `.gitattributes` for PDFs) so the gold, which
is keyed by page, isn't hiding inside regeneration noise.
