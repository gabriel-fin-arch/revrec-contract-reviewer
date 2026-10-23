# ADR 0003: The rules extractor stays — as a baseline and as the offline path

- Status: Accepted, 23 October 2026
- Decision owner: proposed by Claude Code, accepted by Gabriel

## Context

Once the model extractor outperforms the rule-based one on most measures,
the rules look like dead weight. But they do two jobs the model can't: a
fresh clone runs end to end with no API key, and the eval harness gets a
floor to measure the model against — the specific places the rules lose are
a better argument for the model path than any headline number.

## Decision

The rule-based extractor stays in the repo permanently. It emits the same
wire format as the model and passes through the same grounding gate —
"nothing is asserted without evidence" applies to both. Asking for the
model path and not getting it is an error (`--extractor llm` raises rather
than falling back): silently handing someone regular expressions inside a
review that looks fine is the worst outcome available.

## Alternatives considered

- **Delete the rules once the model wins.** Rejected: CI and fresh clones
  would need secrets, and the eval would lose its baseline.
- **Silent fallback to rules on model failure.** Rejected for this
  pipeline: unlike intercompany (ADR 0003 there), a review memo built on
  regexes while looking model-made is a trap for the reviewer.

## Consequences

The offline path is honest about what it is, works because the corpus is
internally consistent, and stops working on anyone else's template — which
is the honest case for the model path. Its measured weaknesses (fees in
prose, termination rights that avoid the phrase) are documented in
`docs/evaluation.md` and drive the model extractor's requirements.
