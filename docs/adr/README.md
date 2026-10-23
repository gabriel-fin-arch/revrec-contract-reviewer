# Architecture decision records

The main design decisions, one short record each: context, decision,
alternatives considered, consequences. Each was drafted from a sketch by the
project's owner and names its decision owner — his, or the assistant's that
he accepted.

| # | Decision | Decision owner |
|---|---|---|
| [0001](0001-every-value-needs-verbatim-citation.md) | Every value needs a verbatim citation; what can't be cited is dropped | Gabriel |
| [0002](0002-judgments-raised-never-answered.md) | Judgments are raised to a person, never answered | Gabriel |
| [0003](0003-rules-extractor-kept-as-baseline.md) | The rules extractor stays — as a baseline and as the offline path | Claude Code, accepted by Gabriel |
| [0004](0004-gold-set-committed-not-regenerated.md) | The gold set is committed to the repo and read from disk, never regenerated | Gabriel |
| [0005](0005-held-out-test-set-never-tuned.md) | A held-out test set, committed before any run, that nothing is ever tuned on | Gabriel |
| [0006](0006-explicit-effort-measured-calls.md) | Effort is set explicitly and every model call is measured | Claude Code, accepted by Gabriel |
| [0007](0007-blank-fields-scored-separately.md) | Leaving blank what the contract doesn't say is scored separately | Claude Code, accepted by Gabriel |

A candidate that was considered and not recorded as its own record: no
confidence thresholds — a consequence of ADRs 0001 and 0002, explained
inside them.
