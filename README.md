# revrec-contract-reviewer

[![CI](https://github.com/gabriel-fin-arch/revrec-contract-reviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/gabriel-fin-arch/revrec-contract-reviewer/actions/workflows/ci.yml)

ASC 606 contract review for group-level revenue assurance. It reads executed
contract PDFs, extracts the facts that drive revenue recognition, tests them
against the five-step model, and writes a review memo in which **every value is
followed by the words it came from, the clause they sit in and the page**.

It does not conclude the accounting. What it does is put the eight judgments a
contract actually forces in front of the person who can make them, with the
evidence already pulled.

> **About the commit history.** I built this with Claude Code in September
> 2026, after intercompany-close-agent, and first published it that month under
> an earlier account. The commits were dated back to June–November 2025 to look
> like months of hand-written work, and while publishing here I rewrote the
> history several times, and added commits dated 2025, to hide that; it
> included relabelling the model run from Claude Opus 5 to Claude Opus 4 and
> moving a contract date in the corpus, both since reverted. On 15 October 2026
> I rewrote it one last time to put back the real times, taken from my Claude
> Code session logs: author dates are when each commit was made, committer
> dates are when the history was rebuilt. [PROVENANCE.md](PROVENANCE.md) lists
> every change and how to check it.

<!-- results-headline:start -->
**Results on the sample corpus** (12 synthetic contracts, scored against a
committed gold set; the tests check these figures against the saved runs and
repeat the rules run):

- Contract fields: precision 1.00 and recall 0.91 with the offline rules, 1.00
  and 0.97 with Claude Opus 5.
- Judgment flags: precision 0.95 and recall 0.83 with the rules, 0.76 and 0.96
  with the model.
- Citations re-resolved against the source: 210 of 210 with the rules, 325 of
  325 with the model. [Full results](#results).
<!-- results-headline:end -->

## Review in 5 minutes

- The business problem and the three places ASC 606 needs domain knowledge.
- The grounding rule: no citation, no field; nothing is concluded from outside
  the document.
- `docs/judgment-calls.md` for the eight decisions that stay with a human.
- The results table and `docs/evaluation.md`, including where the model loses.
- `docs/controls.md` for each control, the code and test behind it, and what a run
  writes as evidence.
- How I built this: which decisions are mine and what an AI assistant wrote.

![Review memo](docs/images/memo.png)

---

## The business problem

A group controller consolidating dozens of selling entities has a revenue
problem that has nothing to do with arithmetic. Each local team applies ASC 606
to its own contracts, on its own paper, and reports a number. By the time those
numbers arrive, the judgments behind them are invisible — a subsidiary that
treated a three-year subscription as three years of revenue and one that
treated the same clause as a rolling monthly contract both submit a clean
trial balance.

Nobody can read every contract. So the group asks for representations, samples
a handful at year end, and finds out about the interesting ones from the
auditors.

What is actually needed is narrower than "AI reads our contracts". It is a way
to open a folder of executed agreements and get back: which of these contain a
term that changes the accounting, where in the document it is, and which
question each one raises. That is a triage problem, and triage is a thing
software is good at.

## Why it needs domain knowledge

Three things in this repository would not be built this way by someone who
hadn't done the work.

**Standalone selling price is not in the contract.** Every schema I sketched
early on had an `ssp` field, and every one of them was quietly lying. SSP is
what the entity would charge selling separately; a contract is the price it
charged this customer on this deal. What the document does contain — the stated
price, the list rate on the order form, the renewal price — is captured, and
the SSP question is raised for someone with access to the entity's pricing
data. The same is true of the variable consideration constraint and of whether
a renewal discount is "incremental to the range typically given".

**A stated term and an enforceable term are different facts.** The corpus
contains a twenty-four month subscription that either party can exit on sixty
days' notice with an express statement that no further compensation is owed. If
that termination right is substantive, the enforceable contract is closer to
two months than to two years, and the transaction price the local team booked
is wrong by an order of magnitude. Both facts are extracted; neither is
resolved.

**The same clause type points in opposite directions.** Two contracts here
resell third-party goods. In one, the vendor grants the licence directly to the
customer, the cost is passed through without mark-up, and there is no warranty
obligation. In the other, the units are bought into inventory, priced at the
seller's discretion, installed and warranted by the seller. Every indicator
points one way in the first and the other way in the second. A rule keyed on
the phrase "third party" would get one of them badly wrong. Hence a flag and
not an answer.

## Architecture

```
ingest    PDF -> pages with character offsets            pdfplumber
segment   numbered clauses, deterministic
extract   structured claims, each carrying a quote       Claude, or offline rules
ground    every quote located in the document, or dropped
assess    five-step checks and the judgment taxonomy     deterministic
memo      HTML with the evidence inline, the same as a PDF, plus JSON
worklist  every open item in the run, one row each       xlsx
```

Four of the five stages are deterministic. A model is involved in exactly one
of them, and everything it produces passes through `ground` before anything
downstream can see it.

**The design principle, and it is enforced rather than intended: the extractor
does not assert anything it cannot point at, and nothing is concluded from
outside the four corners of the document.**

The first half is executable. An extractor returns a value together with a
verbatim quote; grounding searches the document for that quote (whitespace- and
case-insensitively, with no fuzzy matching anywhere) and builds a citation only
if it is found. If the quote isn't there, the field is **dropped** — not
downgraded, not flagged as low confidence. A fact with no evidence is not a
weak fact.

The second half is the judgment taxonomy in
[docs/judgment-calls.md](docs/judgment-calls.md): eight decisions that stay with
a human because answering them needs information the contract does not contain.
That is a stronger position than a confidence threshold, because it survives
being asked to tune it.

There is no confidence score anywhere in the codebase. Fields have one of three
states — `extracted`, `ambiguous`, `absent` — and each drives a different
action. `extracted` means read the citation and move on. `ambiguous` means two
clauses contradict each other and someone has to decide which governs. `absent`
means go and read the document yourself, because nothing here covers it. A
blended 0.4 would have hidden the difference between the last two.

`absent` is careful not to claim the contract is silent, and the memo words it
as "not found" for that reason. An extractor that never looks for a field
produces exactly the same absence as a contract that never mentions one, and the
tool cannot tell them apart.

More in [docs/architecture.md](docs/architecture.md).

## Where the human is, and why

The memo leads with the judgments because they are the reason anyone opened it.
Each one states the question, what in the document raised it, the evidence, and
a standing reason it was not answered:

| Judgment | Why it isn't answered here |
|---|---|
| Enforceable term | Whether a termination penalty is substantive is a legal reading of the words, not a fact stated by them |
| Distinct or not | Depends on how the work is actually delivered, which the contract describes only in general terms |
| Principal vs agent | Control before transfer depends on the operating arrangement — inventory risk, pricing discretion, fulfilment |
| Material right | Requires the entity's typical discount range, which is pricing data, not a contract term |
| Variable consideration constraint | Requires an estimate of the probability of a significant reversal, from the entity's own history |
| Significant financing | Depends on intent and on prevailing rates at inception; neither is stated |
| Standalone selling price | A contract records what was charged on this deal, not what the entity would charge separately |
| Contract modification | Depends on whether added goods are distinct and priced at SSP — the modified agreement is a separate document |

Two of the twelve contracts in the corpus raise **no** judgments at all, and
that is measured. A reviewer that flags something on every contract is not a
reviewer; it is a smoke alarm with a stuck button, and a controller stops
reading it inside a month.

Across a folder, the same output is a worklist — ordered by everything needing
attention, failed checks included, so a contract the pipeline could not read
does not sink to the bottom looking like a clean one:

![Run worklist](docs/images/worklist.png)

## Results

The pipeline is scored against a committed gold set. Full methodology, and an
honest account of what a synthetic corpus can and cannot tell you, in
[docs/evaluation.md](docs/evaluation.md).

Precision / recall. The offline regexes are the baseline the model has to beat;
a model extractor that can't beat regexes on a corpus this clean isn't earning
its cost.

**Development set**, the 12 contracts the regexes and the prompt were written
against:

<!-- results-table:start -->
| Measure | Rules | Claude Opus 5 |
|---|---|---|
| Contract fields | 1.00 / 0.91 | 1.00 / **0.97** |
| Unstated fields left blank | 21 of 21 | 21 of 21 |
| Performance obligations | 0.79 / 0.75 | **0.83** / **0.95** |
| Judgment flags | **0.95** / 0.83 | 0.76 / **0.96** |

Citations re-resolved against the source: **100%** on both runs (210 and 325).
Saved runs in [`evals/results/`](evals/results/).
<!-- results-table:end -->

That published model column is the September run. Every measured run on the
same set, the two of 19 October 2026 included:

| Measure | Rules | Claude Opus 5.5 | Claude Opus 5 | Claude Opus 5, September |
|---|---|---|---|---|
| Contract fields | 1.00 / 0.91 | 0.99 / 0.95 | 1.00 / 0.98 | 1.00 / 0.97 |
| Unstated fields left blank | 21 of 21 | 21 of 21 | 21 of 21 | 21 of 21 |
| Performance obligations | 0.79 / 0.75 | 0.95 / 0.95 | 0.83 / 0.95 | 0.83 / 0.95 |
| Judgment flags | 0.95 / 0.83 | 0.87 / 0.87 | 0.85 / 0.96 | 0.76 / 0.96 |

**Test set**, 7 contracts written afterwards the same way and committed with
their answers before anything ran on them ([`corpus/test/`](corpus/test/)):

| Measure | Rules | Claude Opus 5.5 | Claude Opus 5 |
|---|---|---|---|
| Contract fields | 1.00 / 0.89 | 0.98 / 0.97 | 0.98 / 0.97 |
| Unstated fields left blank | 8 of 8 | 8 of 8 | 8 of 8 |
| Performance obligations | 0.67 / 0.50 | 0.85 / 0.92 | 0.85 / 0.92 |
| Judgment flags | 1.00 / 0.42 | 0.85 / 0.92 | 0.65 / 0.92 |

The Claude Opus 5.5 and Claude Opus 5 columns are runs of 19 October 2026 at
effort `high`, costed at the published prices of 18 October: USD 0.66 and 0.34
for Opus 5.5 on the two sets, USD 0.72 and 0.33 for Opus 5, 16 to 21 seconds a
contract on average. Citations re-resolved against the source: 100% on every run. Saved
runs, with their claims and every model call, in
[`evals/results/`](evals/results/).

On the test set the regexes' recall falls apart, judgments at 0.42, and so does
Claude Opus 5's judgment precision, at 0.65: it raises questions the contracts
don't call for, among them the distinct-or-not question on Larkspur, whose
configuration services were written not to raise it. Claude Opus 5.5 holds at
0.85 there. It is the default, the cheaper per token, and on these numbers the
better of the two. Two disagreements with the test-set gold are open questions,
listed in [docs/evaluation.md](docs/evaluation.md#open-questions-about-the-test-gold).

The September column is the original model run, on Claude Opus 5
(`claude-opus-5`) at its default effort, which is high; it is already in the
version I pushed here on 1 October. The harness records the model it calls, and
`llm.json` said `claude-opus-5` until 13 October, when I relabelled it Claude
Opus 4 in a history rewrite to fit the backdated commits. An earlier version of
this note then called the Opus 5 label wrong. It wasn't
([PROVENANCE.md](PROVENANCE.md#the-model-run)). Repeated on 19 October, the
same model scores 0.85 on judgment precision instead of 0.76. The code has
changed since September and that run kept only its counts, so it can't be
scored again to say how much of the difference is the code and how much is
run-to-run variance.

In September the model won on recall everywhere, and it was not close — every gap the regexes
had closes. **It also drops judgment precision from 0.95 to 0.76**, mostly by
reading integration language more liberally than the taxonomy intends. That
trade is the wrong way round for this product: a reviewer's trust is spent by
false positives long before it is spent by misses. I would not ship the model
path to a controller without tightening that definition first, and
[docs/evaluation.md](docs/evaluation.md) says so at length rather than rounding
it off.

The harness also caught the failure worth knowing about. The first model run
reported a transaction price of 792,000 for a contract stating no total, and a
six-month term for one stating no term. Both were correct arithmetic — an annual
fee times a term, a start date to an end date — and both cited the figures they
were computed from, so every quote resolved and grounding passed them. **That is
the documented limit of grounding met in the wild: it catches invention, not
derivation.** A prompt rule against calculating values took the share of
unstated fields left blank from 0.90 back to 1.00.

```bash
uv run revrec eval --extractor rules --mistakes
```

## Quickstart

Runs with no API key. The offline extractor is the default when one isn't set.

```bash
uv sync --extra dev
uv run revrec generate-corpus
uv run revrec review --extractor rules
```

That writes a memo per contract to `out/`, as HTML and as PDF, with an index
of the run and `worklist.xlsx`, every open item on one sheet with blank
columns for the reviewer's conclusion. Open `out/index.html`.

To use the model extractor, set `ANTHROPIC_API_KEY` (copy `.env.example` to
`.env`) and drop the flag:

```bash
uv run revrec review
uv run revrec eval --save
```

## What this does not do

Stated plainly, because an honest scope is more credible than an inflated one.

- **No OCR.** Text-layer PDFs only. A scanned contract is refused rather than
  silently returning an empty review; in a folder, it is listed at the top of
  the index as not reviewed and the rest are reviewed as normal.
- **No revenue schedule.** It does not compute the journal entry or the
  period-by-period waterfall. It reviews the contract.
- **No IFRS 16, and no IFRS 15 beyond where it converges with ASC 606.**
- **No layout understanding.** The model is given extracted text, not the PDF —
  see [docs/architecture.md](docs/architecture.md) for why that trade is made
  deliberately. Anything carried by position on the page is gone before the
  model sees it.
- **It does not replace technical review.** It prioritises and evidences. It
  does not conclude.

## How I built this

With an AI coding assistant (Claude Code). The domain calls are mine: what
each contract in the corpus has to exercise, the eight judgments and why each
one stays with a person, "no citation, no field", three field states instead
of a confidence score, and how the evaluation is scored, silence included.
I worked them out in design notes I drafted with the help of an AI chat as
the build started. Claude Code wrote the code and the tests, and most of the
docs, to that design. I reviewed what it produced and sent back what was
wrong; every decision listed above is one I can walk you through. The commit
messages before 14 October 2026 are the assistant's too, written in a casual
first-person style I asked for; commits it drafts now carry a `Co-Authored-By`
line.

## The corpus

Twelve synthetic contracts: ten SaaS and software, two clinical services. Ten of
them are built around a specific ASC 606 question and two are deliberately built
around none. Every party, product, price and person is invented. See
[corpus/README.md](corpus/README.md) for what each one is there to exercise.

## Stack

Python 3.11+ · pydantic · pdfplumber · Anthropic SDK · jinja2 · typer ·
reportlab · openpyxl · pytest · ruff.

No agent framework. This is a pipeline with one model call in it, and wrapping
that in a graph would have added a dependency and a diagram without adding a
capability.

235 tests. CI runs the pre-commit hooks (ruff among them), the test suite,
and then the whole pipeline offline
over the corpus and the held-out set; the eval step exits non-zero if any
citation in any memo stops
resolving against its source document. That is the one regression that leaves
the tool untrustworthy while still looking like it worked.

```bash
uv run pytest -q

# install the git hooks once: ruff, whitespace and file checks, and a refusal
# to commit a .env or an API key; CI runs the same hooks on every file
uv run pre-commit install
```

Or without Python or uv, with Docker: the image reviews the committed corpus
offline and writes the memos to a folder you mount (on Linux, add
`--user "$(id -u):$(id -g)"`; see the `Dockerfile`).

```bash
docker build -t revrec-contract-reviewer .
docker run --rm -v "$PWD/out:/app/out" revrec-contract-reviewer
```

## Licence

MIT.
