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

It is reported as a count, unstated fields left blank out of all of them, and
not as precision and recall. Each unstated field is either left blank or
invented; there is no third outcome to call a miss, so a recall would read
1.00 whatever the extractor did. An earlier version of this table printed one
anyway.

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
| Performance obligations | 0.79 | 0.75 | 0.77 |
| Judgment flags | 0.95 | 0.83 | 0.88 |

Unstated fields left blank: 21/21. Citations re-resolved: 210/210 (100%). Claims
dropped for no evidence: 0.

Saved run: [`evals/results/rules.json`](../evals/results/rules.json), and the
run behind it in
[`evals/results/rules.claims.json`](../evals/results/rules.claims.json): for
each contract, the PDF's SHA-256, every claim the extractor returned with its
quotes, and the extraction grounding made of them.
`uv run revrec rescore evals/results/rules.claims.json` scores that run again
without extracting, and refuses if a PDF has changed since; a test checks it
gives `rules.json`.

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

Same 12 contracts. Run on Claude Opus 5 (`claude-opus-5`) on 10 September 2026.
For a few days this file called it a Claude Opus 4 run from November 2025,
after I relabelled it in a history rewrite to fit the backdated commits (see
[PROVENANCE.md](../PROVENANCE.md#the-model-run)). The corpus PDFs and the gold
set are the ones the run was saved with. `llm.json` keeps only the counts, so
the run can't be re-scored against later changes to the code. The extractor now
defaults to Claude Opus 5.5, measured with Claude Opus 5 again on 19 October:
see [the runs of 19 October](#claude-opus-55-and-claude-opus-5-19-october-2026).

| Measure | Precision | Recall | F1 |
|---|---|---|---|
| Contract fields | 1.00 | 0.97 | 0.98 |
| Performance obligations | 0.83 | 0.95 | 0.88 |
| Judgment flags | 0.76 | 0.96 | 0.85 |

Unstated fields left blank: 21/21. Citations re-resolved: 325/325 (100%). Claims
dropped for no evidence: 2.

Saved run: [`evals/results/llm.json`](../evals/results/llm.json). Claude Opus 5
is still available, so it can be repeated with `ANTHROPIC_MODEL=claude-opus-5`.
To measure the current default, set `ANTHROPIC_API_KEY` and run
`uv run revrec eval --extractor llm --effort high --mistakes --save`.

### How a model run is measured

The request sets the effort explicitly, `high` unless `--effort` or
`REVREC_EFFORT` says otherwise: Claude Opus 5.5 defaults to `medium` and Claude
Opus 5 to `high`, so leaving it out would make two runs differ in more than
the model. Every call is recorded with the run (`extract/metering.py`): model,
effort, stop reason, input, output and cache tokens as the API reports them,
wall-clock seconds, and the cost at Anthropic's published prices, which the
code holds with the date they were read. Thinking is billed as output and is
inside the output count. `eval` prints the totals, and `--save` writes the
report as `llm-<model>-<effort>.json` with its claims and calls beside it, so a
new run sits next to `llm.json` instead of replacing it. A call that returns
nothing usable, a refusal or a response cut off at `max_tokens`, raises with
its record attached, since its tokens were spent either way.

With `--save`, the run so far is also written after every contract, to
`<name>.partial.claims.json`, and removed when the run finishes and the report
and claims are written. A run that stops part-way, on a refused key or a
balance that has run out, keeps there the claims and calls it had already
paid for, with the reason it stopped, and `eval` says how many calls that was
and what they cost.

`uv run revrec estimate --set development --model claude-opus-5-5` says what a
run would cost before it is made, without calling the API: input from the
character counts of the instructions, the schema and each contract, output
between the claims alone and `max_tokens` on every call, which no call can
exceed. No model run is made without that estimate and my approval first.

### Against the baseline

| Measure | Rules | Model |
|---|---|---|
| Contract fields | 1.00 / 0.91 | 1.00 / **0.97** |
| Unstated fields left blank | 21 of 21 | 21 of 21 |
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
more than half the portfolio gets ignored inside a month. The corpus's two
deliberately quiet contracts exist to test exactly that. The fix is
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
you multiplied does not make the product something the contract says. The
share of unstated fields left blank went from 0.90 back to 1.00, and Tessellate
additionally started getting its effective date and total right.

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

## Development and test sets

The twelve contracts above are the development set. The regexes and the
prompt were written against them, so every number in the sections above is
on data the tool was shaped by.

Seven more are held out in [`corpus/test/`](../corpus/test/), with their gold
records in [`evals/gold/test/`](../evals/gold/test/). They were written on
18 October 2026, after the rules and the prompt, the same way as the twelve,
and committed with their gold before either extractor had been run on them
(commit `8258bb6`; the first results are in the commit after it).
`corpus/test/README.md` says what each one is for.

**The rule.** Results on the test set are reported and not used. Nothing seen
there goes back into the rules, the prompt or the scorer. A fix for something
it shows is made against the development set, and the test set measures it
again afterwards.

### Rules extractor, both sets

| Measure | Development (12) | Test (7) |
|---|---|---|
| Contract fields | 1.00 / 0.91 | 1.00 / 0.89 |
| Performance obligations | 0.79 / 0.75 | 0.67 / 0.50 |
| Judgment flags | 0.95 / 0.83 | 1.00 / 0.42 |

Precision / recall. On the test set: unstated fields left blank 8/8, citations
re-resolved 96/96 (100%), claims dropped for no evidence 0. Saved run:
[`evals/results/test/rules.json`](../evals/results/test/rules.json), with its
claims in `rules.claims.json` beside it.

Precision holds and recall falls, most of all on judgments: 5 of the 12
expected were raised, and none was raised that shouldn't have been. What was
missed, contract by contract, as `eval --set test --mistakes` lists it:

- **Fenwick** and **Wexford** state their fees in sentences; neither total was
  read, nor the obligation it prices. Fenwick's service credits were not raised
  as variable consideration, nor Wexford's allocation question.
- **Harbourline**'s fixed fee, in a milestone table, was not read as a total,
  and its late-delivery reduction was not raised as variable consideration.
- **Larkspur**, **Tamarind** and **Harbourline** say there is no termination
  for convenience in three different ways ("may not be terminated for
  convenience", "non-cancellable", "only for ... material breach"), and none
  was read.
- Larkspur's configuration services and Tamarind's customisation were read as
  `other` rather than implementation, and Saltmarsh's third-party feed as
  `other` rather than resale; Saltmarsh's principal-versus-agent question,
  Tamarind's distinct-or-not and financing questions and Larkspur's renewal
  discount were not raised.
- **Alder**, the control, raised nothing, which is right.

That is the shape of a rule set fitted to the phrasing of the documents it was
written on. It is reported here and not fixed here.

## Claude Opus 5.5 and Claude Opus 5, 19 October 2026

Both models, at effort `high`, on both sets, with the harness described under
[How a model run is measured](#how-a-model-run-is-measured). Run after a cost
estimate (`revrec estimate`: USD 1.71 to 14.45 for the four) and my approval.

| Run | Calls | Input tokens | Output tokens | Cost (USD) | Seconds in calls | Longest call |
|---|---|---|---|---|---|---|
| Claude Opus 5.5, development | 12 | 66,539 | 28,781 | 0.66 | 243.7 | 25.5 s |
| Claude Opus 5.5, test | 7 | 37,309 | 15,383 | 0.34 | 127.8 | 23.9 s |
| Claude Opus 5, development | 12 | 66,515 | 24,361 | 0.72 | 248.3 | 46.8 s |
| Claude Opus 5, test | 7 | 37,295 | 11,355 | 0.33 | 112.4 | 24.1 s |

USD 2.04 in all, at the published prices of 18 October. Input counts include the
instructions read from the prompt cache. All 38 calls ended `end_turn`; the
largest produced 4,001 output tokens, against a `max_tokens` of 16,000. Saved
runs: `evals/results/llm-claude-opus-5-5-high.json` and
`llm-claude-opus-5-high.json`, the same names under `evals/results/test/`,
each with its claims and calls in `.claims.json` beside it. A test scores each
one again from its claims and checks it gives its report.

### Development set

| Measure | Rules | Claude Opus 5.5 | Claude Opus 5 | Claude Opus 5, 10 September |
|---|---|---|---|---|
| Contract fields | 1.00 / 0.91 | 0.99 / 0.95 | 1.00 / 0.98 | 1.00 / 0.97 |
| Performance obligations | 0.79 / 0.75 | 0.95 / 0.95 | 0.83 / 0.95 | 0.83 / 0.95 |
| Judgment flags | 0.95 / 0.83 | 0.87 / 0.87 | 0.85 / 0.96 | 0.76 / 0.96 |

Unstated fields left blank: 21/21 on every run. Citations re-resolved: 300/300
for Opus 5.5, 335/335 for Opus 5. Claims dropped for no evidence: 6 and 3.

Claude Opus 5.5 raised three judgments the gold doesn't expect (distinct-or-not
on the Meridian change order and on Beacon, variable consideration on the
Calderwood master agreement) and missed three (the allocation question on
Orchid, financing on Northgate, variable consideration on Tessellate). Claude
Opus 5 raised four it shouldn't have and missed one, Northgate's financing.

The same model at the same effort scored 0.76 on judgment precision in
September and 0.85 now. The code has changed in between, and the September run
kept only its counts, so it can't be scored again to separate the code from the
run-to-run variance described above.

### Test set

| Measure | Rules | Claude Opus 5.5 | Claude Opus 5 |
|---|---|---|---|
| Contract fields | 1.00 / 0.89 | 0.98 / 0.97 | 0.98 / 0.97 |
| Performance obligations | 0.67 / 0.50 | 0.85 / 0.92 | 0.85 / 0.92 |
| Judgment flags | 1.00 / 0.42 | 0.85 / 0.92 | 0.65 / 0.92 |

Unstated fields left blank: 8/8 on every run. Citations re-resolved: 173/173
for Opus 5.5, 180/180 for Opus 5. Claims dropped for no evidence: 2 and 3.

Both models find 11 of the 12 expected judgments. What separates them is what
else they raise. Claude Opus 5.5 raised two more: variable consideration on
Saltmarsh, and the allocation question on Harbourline. Claude Opus 5 raised six:
the distinct-or-not question and principal versus agent on Larkspur, the first
of them on configuration services the contract says the customer can use the
platform without; distinct-or-not and variable consideration on Saltmarsh; a
material right on Wexford, which has no renewal; and the allocation question on
Harbourline. On contracts nobody tuned against, the older model reads the
taxonomy more liberally, which is the failure the September run already showed.

### Open questions about the test gold

Two places where both models disagree with the gold in the same way. Neither is
changed here: correcting the test set's answers after seeing results is right
only for an authoring error, and a change would be recorded in the CHANGELOG
with its reason.

- **Wexford.** Both models read the stated term as 24 months and price the
  obligation at EUR 102,000. The gold has 36 months and EUR 306,000, which is
  what the amendment prints for the period it covers ("thirty-six months",
  "EUR 306,000"); 24 months is the extension, and EUR 102,000 the annual fee.
  Whether a reviewer would read it as the models do is open.
- **Harbourline.** Both models find a training obligation in the handover
  workshop, which the gold doesn't list, and raise the allocation question
  because of it. The workshop is named among the deliverables, so the gold may
  be the one that's incomplete.

## Judgment precision: one change, argued from the development set, and dropped

A judgment is raised by a rule in `assess/judgments.py` from what the
extractor read, so every false positive has a passage behind it.
`revrec judgment-misses` lists them from a saved run, with no extraction and
no API call. On the development set, the Claude Opus 5.5 run of 19 October:

| Judgment raised, not in the gold | Contract | The passage behind it |
|---|---|---|
| distinct-or-not | Meridian change order 03 | "The additional services are of the same nature as those already being provided under the Agreement and are delivered by the same study team as part of the same integrated engagement." |
| distinct-or-not | Beacon | "The Software requires the Cartos Spatial Database" |
| variable consideration | Calderwood master agreement | "termination of the affected Order Form and a refund of prepaid fees for the unused portion of the Subscription Term." |

Claude Opus 5 raised the first and the third too, plus the allocation question
on Aster, through a second obligation it built from the pass-through costs,
and distinct-or-not on Tessellate.

Two of the three come from `integration_language`, the passage the
distinct-or-not rule acts on. Neither describes promises the customer can't
benefit from separately. The change order adds more of a service that, by the
corpus's own account, is a single performance obligation; "the same nature",
"the same study team" and "the same integrated engagement" say the new
services are related to the old ones, and the question that does arise, how
to account for the modification, is already flagged. Beacon's licence needs a
database that Cartos, an unaffiliated third party, licenses at a price it
sets: a product sold separately. The questions it does raise, principal or
agent on the database and the allocation, are already flagged.

So the change was one paragraph of the prompt's guidance on
`integration_language`, which read:

> Only report integration_language where the contract actually describes one
> promise as customising, integrating with, or depending on another, so that
> the customer cannot benefit from one without the other. Do not supply it
> because the arrangement looks like it might be. Services being of the same
> nature as others, delivered by the same team, or part of the same
> engagement are related, not integrated; and a product that needs another
> product sold separately, by the supplier or anyone else, does not depend on
> it in this sense.

The first two sentences were there before, less the clause about benefit.
It was the tighter definition the comment on `_distinct_uncertain` names as
the real fix, inseparable rather than related, written into the prompt
rather than tuned into a rule. That comment also says where to draw the line
is a risk-appetite call for whoever owns the review, so the line drawn here
is one for review, and the test set decides whether it stays.

What it leaves alone: the refund on the Calderwood master agreement. It is
the remedy for a breach of warranty, and whether a breach remedy belongs with
variable consideration is a question about the taxonomy rather than about
reading the contract. The issue asks for one change.

What could go the wrong way: Aster says its activities are "provided as an
integrated service" and that the sponsor gets no "separately usable
deliverable" from any one of them, and the gold expects distinct-or-not there.
That is integration in the new sense, so it should still be reported. If it
isn't, the change costs a true positive.

**An open question about the development gold.** Tessellate says almost the
same as Aster: "a single integrated engagement", phases "not separately
saleable", "no usable output until cutover". The gold expects distinct-or-not
on Aster and not on Tessellate. Under the new guidance the two read the same
way. The gold is not changed here.

The test set's misses on 19 October were already published in the section
above when this was written. The change is argued from the development cases
only, and the test set decides whether it stays: if test-set precision
doesn't improve, this file says so and the change is dropped.

### Before and after

Same model and effort as the runs of 19 October, Claude Opus 5.5 at `high`;
those runs are the before. The after runs were made on 20 October, after an
estimate of USD 0.77 to 6.44 for the two (`revrec estimate`) and my approval,
and are saved beside them as `llm-claude-opus-5-5-high-integration.json`
(`eval --save --name`): 19 calls, USD 0.60 and 0.34, all ending `end_turn`.
Earlier attempts that day and the day before stopped when the API refused
requests for lack of credit; nothing from them is used here.

Judgment flags, precision / recall:

| Set | Before | After |
|---|---|---|
| Development | 0.87 / 0.87 | 0.89 / 0.74 |
| Development without Aster | 0.84 / 0.84 | 0.89 / 0.89 |
| Test | 0.85 / 0.92 | 0.85 / 0.92 |

**On the test set, nothing changed.** The same eleven judgments found, the same
one missed (the allocation question on Wexford), the same two raised against
the gold (variable consideration on Saltmarsh, the allocation question on
Harbourline). Claude Opus 5.5 raised no distinct-or-not question on the test
set it shouldn't have, before or after, so there was nothing there for this
change to fix. Performance obligations moved from 0.85 / 0.92 to 0.77 / 0.83,
on Harbourline, where the after run split the work into more promises.

**On the development set, the change did what it was for and one thing it
wasn't.** The two false positives it was aimed at are gone: no distinct-or-not
on the Meridian change order or on Beacon. A new one appeared on Tessellate,
"a single integrated engagement ... not separately saleable", which is the
open question above: under the new guidance Tessellate reads like Aster. The
refund on the Calderwood master agreement is still raised, as expected.

And Aster came back nearly empty. The model returned one claim, that the
document is a master agreement, and nothing else: no parties, no fees, no
obligation, none of its four judgments. Before, the same contract gave
twelve fields, the obligation and all four judgments. The call ended
normally (`end_turn`, 1,127 output tokens against 3,027 before). Nothing in
the change is about the agreement type, and one run can't say whether the
change or run-to-run variance did it. Without Aster, the development set went
from 0.84 / 0.84 to 0.89 / 0.89.

**The change is dropped.** The rule set before the runs was that the test set
decides, and the test set didn't improve. The prompt is back to its 19
October text, so the published numbers above are still those of the model
that runs by default. The after runs stay in `evals/results/` as the record
of what was tried, and a test scores each one again from its claims.

What the measurement can't separate: one run per set, and a ±0.05 variance on
the judgment row (see Run-to-run variance), against a change that moved two
flags out of twenty-three. A larger test set with distinct-or-not questions
in it is what would decide this kind of change; this one has none that
Claude Opus 5.5 gets wrong.

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
