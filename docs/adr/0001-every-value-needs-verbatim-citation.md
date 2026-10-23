# ADR 0001: Every value needs a verbatim citation; what can't be cited is dropped

- Status: Accepted, 23 October 2026
- Decision owner: Gabriel

## Context

A review memo full of plausible numbers is worse than useless if a reviewer
can't check any of them: a wrong term length gets caught by reading the
clause, but an invented one sends the reviewer looking for a clause that
doesn't exist. The entire value of the tool is that every figure can be
traced back to the words it came from.

## Decision

An extractor's entire vocabulary is a `Claim`: a value as a string, plus
the words in the document it came from. Only the grounding step can
construct a `Citation`, and only after locating the quote in the document —
matching is exact, modulo whitespace, case and typographic variants, with
no fuzzy matching and a twelve-character minimum. A claim whose quote can't
be located is dropped, and drops are counted on the face of the memo
(`dropped_for_no_evidence`), not swallowed. The rule binds the rule-based
extractor exactly as it binds the model: "nothing is asserted without
evidence" is not a rule about language models.

## Alternatives considered

- **Fuzzy quote matching.** Rejected: a matcher that tolerates a few wrong
  characters tolerates a quote that was never in the document. The entire
  value of grounding is that it can say no.
- **Trust the model's citations.** Rejected: an extractor marking its own
  homework is not a thing the type system permits.

## Consequences

Invention is structurally unpublishable; the eval re-resolves every
citation of every finished review and fails below 100%. The documented
limit is derivation, not invention — a value the model computed from
figures it cited passes grounding — and that limit is stated in
`docs/architecture.md` and watched by the eval harness.
