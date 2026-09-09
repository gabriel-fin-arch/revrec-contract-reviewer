# Evaluation

Most portfolio projects that extract things from documents do not say how well
they extract them. This one does, including where it is bad.

```bash
uv run revrec eval --extractor rules --mistakes
```

## What is measured

Four things, kept apart because they fail for different reasons and get fixed
in different places.

**Contract fields.** Precision and recall over ten scalar terms: the parties,
the agreement type, currency, effective date, stated term, termination for
convenience and its notice period, payment terms, and the total fixed
consideration.

**Silence.** Scored separately, and this is the measure I would most want to be
asked about. Where the gold record says a contract does not state something,
reporting a value for it is counted as an **invention**, not as a wrong answer.
The two feel similar in a spreadsheet and are not similar at all in a review: a
wrong term length gets caught by the reviewer reading the clause, an invented
one sends them looking for a clause that does not exist. A tool that quietly
fills gaps with plausible values is worse than one that leaves them empty,
because the gaps are where the interesting contracts are.

**Performance obligations.** Matched as a multiset of (kind, price). Not by
label — labels are free text, and a fair scorer should not reward one wording of
"Premium Support, 36 months" over another.

**Judgment flags.** Set comparison per contract. The number that matters most
for the product: a reviewer's trust is spent by false positives long before it
is spent by misses.

**Citations.** Every citation in every finished review is re-resolved against
the document text. This should always be 100%, because grounding already
refused anything that failed — so it is really an independent check that the
invariant held, rather than a measure of the extractor. It is here because "the
control is enforced" is a claim worth being able to prove after the fact rather
than by reading the code. `revrec eval` exits non-zero if it ever drops below
100%.

## Baseline results — offline rule-based extractor

12 contracts.

| Measure | Precision | Recall | F1 |
|---|---|---|---|
| Contract fields | 1.00 | 0.91 | 0.95 |
| Silence on unstated fields | 1.00 | 1.00 | 1.00 |
| Performance obligations | 0.79 | 0.75 | 0.77 |
| Judgment flags | 0.95 | 0.83 | 0.88 |

Citations re-resolved: 210/210 (100%). Claims dropped for no evidence: 0.

Saved run: [`evals/results/rules.json`](../evals/results/rules.json).

### Where it loses, specifically

Field precision is 1.00 and recall is 0.91, which is the signature of an
extractor built out of narrow patterns: when it fires it is right, and it
declines to fire more often than it should. Every miss is in one of two places.

**Contracts that state fees in prose.** The rules extractor reads fee tables,
scoped between the header row and the total row. The Tessellate statement of
work says "The fixed fee for the work described in Section 1 is USD 240,000",
the Orchid amendment says "the fee ... is EUR 48,000 in aggregate", and the
Vantage master agreement says "an annual subscription fee of USD 264,000". None
is in a table, so all three lose their total and their obligation. That is four
of the six obligation misses and three of the field misses.

An earlier version did read amounts out of prose, and it was worse. "The
balance of USD 900,000 in four (4) equal annual instalments of USD 225,000"
parses as a perfectly good fee line, and it produced a performance obligation
labelled `USD 900,000 in four (4) equal annual i` priced at 225,000 — which is
not a promise to a customer and never was. Restricting to the table lost recall
and bought precision, and on a reviewer's worklist that is the right side of
the trade.

**Termination rights that avoid the phrase.** The Meridian agreement says
"Sponsor may terminate this Agreement or the Study at any time on thirty (30)
days' written notice". It never says "for convenience", so the pattern misses
it — and with it the `enforceable_term` flag, which is one of the two judgment
recall misses.

The other judgment misses are `distinct_uncertain` on two contracts, which
requires reading integration language out of prose; and one false positive,
`ssp_not_observable` on the Meridian agreement, where the rules extractor reads
the four milestone rows as four obligations when the agreement describes a
single integrated service. A milestone table is a payment schedule, not a list
of promises, and telling those apart needs the clause above the table.

Every one of these is a case for the model extractor, and they are a better
argument for it than a headline number would be.

## Running the model extractor

**As published, only the offline baseline has been measured.** The model path is
covered by unit tests against a stub client — that it is handed the same text
grounding will search, that its output goes through the same gate, that a
fabricated quote from it is dropped exactly like one from a rule — but its
accuracy on this corpus is not yet a number I have run, so there is no table for
it here. An unmeasured claim is worse than an absent one, and the absence is the
honest state of it.

To produce the model figures:

```bash
export ANTHROPIC_API_KEY=...
uv run revrec eval --extractor llm --save --mistakes
```

That writes `evals/results/llm.json`. Publishing a number without a saved run
behind it is how benchmark tables become fiction, so the artifact is the
deliverable, not the table.

## What this harness cannot tell you

Stated plainly, because the limitations are more interesting than the scores.

**The corpus is synthetic and the generator wrote the gold set.** That is
legitimate — the generator knows the answers because it authored the
questions — and it means the numbers measure whether the extractor reads fields
it was pointed at. They say nothing about a badly scanned sixty-page master
agreement with a rider taped to the back.

**The documents are clean.** One font, one column, consistent clause numbering,
no handwriting, no stamps, no signature pages photographed at an angle. Real
executed contracts are a different problem and a harder one.

**Twelve contracts is not a benchmark.** It is enough to catch a regression and
to make the failure modes legible. It is not enough for the second decimal
place of any of these numbers to mean anything, and I would not defend one.

**The judgment gold set is my opinion.** The flags each contract "should" raise
are the ones I wrote it to raise. That is circular in a way the field scores are
not — it measures whether the rules implement the taxonomy, not whether the
taxonomy is right. The taxonomy is defended in
[judgment-calls.md](judgment-calls.md) by argument, which is the only way it can
be defended.

**Nothing here measures whether a reviewer is faster.** That would need real
contracts, real reviewers and a before-and-after, and it is the measurement that
would actually matter.
