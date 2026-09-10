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

## Model extractor — Claude Opus 5

Same 12 contracts, same gold set.

| Measure | Precision | Recall | F1 |
|---|---|---|---|
| Contract fields | 1.00 | 0.97 | 0.98 |
| Silence on unstated fields | 1.00 | 1.00 | 1.00 |
| Performance obligations | 0.83 | 0.95 | 0.88 |
| Judgment flags | 0.76 | 0.96 | 0.85 |

Citations re-resolved: 325/325 (100%). Claims dropped for no evidence: 2.

Saved run: [`evals/results/llm.json`](../evals/results/llm.json). Reproduce with
`ANTHROPIC_API_KEY` set and `uv run revrec eval --extractor llm --save --mistakes`
— about four minutes and a couple of dollars.

### Against the baseline

| Measure | Rules | Model |
|---|---|---|
| Contract fields | 1.00 / 0.91 | 1.00 / **0.97** |
| Silence | 1.00 / 1.00 | 1.00 / 1.00 |
| Performance obligations | 0.79 / 0.75 | **0.83** / **0.95** |
| Judgment flags | **0.95** / 0.83 | 0.76 / **0.96** |

The model wins on recall everywhere and it is not close: obligations from 0.75
to 0.95, judgments from 0.83 to 0.96. Every gap the regexes had — fees stated in
prose, a termination right that never says "for convenience", integration
language buried in a scope clause — closes.

**And judgment precision drops from 0.95 to 0.76.** Seven of the twelve
contracts get a flag they should not. Six of those seven are
`distinct_uncertain` or a second-order effect of finding an extra obligation:
the model reads integration language more liberally than the taxonomy intends,
and every extra obligation it finds also raises the allocation question.

That trade is the wrong way round for this product and I would not ship the
model path as-is to a controller. A reviewer's trust is spent by false positives
long before it is spent by misses, and a tool that raises a spurious judgment on
more than half the portfolio gets ignored inside a month — which is the same
argument the corpus's two deliberately quiet contracts exist to test. The fix is
not a threshold; it is a tighter definition of what counts as integration
language, and that is a domain question, not a prompting one.

### The most useful thing the harness found

The first model run reported a transaction price of 792,000 for the Vantage
master agreement, which states no total, and a six-month term for the Tessellate
statement of work, which states no term.

Both numbers are correct arithmetic. Vantage states an annual fee of 264,000
over thirty-six months; Tessellate runs from 1 September 2025 to 28 February
2026. The model multiplied, and counted, and then cited the figures it had
worked from — so the quotes resolved, grounding passed them, and two invented
values went into the memo with evidence attached.

This is the documented limit of grounding, met in the wild: **it catches
invention, not derivation.** The citation was real. What was manufactured was
the inference drawn from it, and no amount of quote-checking can see that.

The fix was one paragraph in the system prompt saying, in effect, report a
number only where the document prints that number, and that quoting the figures
you multiplied does not make the product something the contract says. Silence
precision went from 0.90 back to 1.00, and Tessellate additionally started
getting its effective date and total right.

Worth being clear that it is a mitigation and not a guarantee. Nothing
structural prevents a derived value; the schema cannot express "this number was
printed" as distinct from "this number is true", and the eval is what would
catch the next one.

### Two claims were dropped on the real run

`dropped_for_no_evidence: 2` — one on Beacon, one on Pinegrove. The model
proposed a fact, the quote it offered could not be located in the document, and
the field was discarded rather than downgraded. The control is not theoretical
and it is not only exercised by a stub in the test suite.

### Run-to-run variance

Two full runs of the same corpus, on the same model, did not agree exactly. The
significant financing flag was a false positive on one contract in one run and a
false negative on a different contract in the other. Sampling is not fixed and
the current models take no temperature parameter, so the honest reading of any
single figure above is roughly ±0.05 on the judgment row. Twelve contracts is
too few for it to be tighter, which is one more reason not to defend a second
decimal place.

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
