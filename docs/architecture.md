# Architecture

## The pipeline

```
load      PDF -> text with per-page character offsets
segment   numbered clauses
extract   structured claims, each carrying a verbatim quote
ground    every quote located in the document, or the claim is dropped
assess    deterministic checks + the judgment taxonomy
memo      HTML with evidence inline, plus JSON
```

`extract` is the only stage that may call a model. Every other stage is
deterministic and offline. Nothing below `ground` branches on which extractor
ran — `pipeline.py` is deliberately boring for that reason.

## Why there is no agent framework

The first project I built in this space is a LangGraph agent, and the graph
earned its place there: intercompany matching has a genuine human-in-the-loop
interrupt in the middle of it, where a reviewer's decision goes back into the
run and changes what happens next.

This is not that. It is a straight line: read a document, extract from it,
check the extraction, write a memo. There is no interrupt, no branch that
depends on a model's choice, no state that survives across turns. Adding a
graph would have added a dependency, a diagram and a vocabulary, and would not
have added a capability.

The reviewer is still in the loop. They are just at the end of it, which is
where a reviewer of contracts actually sits.

## Grounding

The control the whole project is built around.

An extractor's entire vocabulary is a `Claim`: a value written as a string, and
the words in the document it came from. It cannot construct a `Citation` — only
the grounding step can, and only after finding the quote. So an extractor
marking its own homework is not a thing the type system permits.

**Matching is exact, modulo whitespace, case and typographic variants.** Quotes
are searched against a normalised copy of the document with whitespace runs
collapsed, case folded, and curly quotes and dashes folded onto their ASCII
equivalents. Each fold maps one character to one character, so an index
alongside the normalised text maps every match back to raw offsets — citations
therefore always point at real characters in the original.

There is no fuzzy matching. No edit distance, no "close enough" threshold. The
entire value of grounding is that it can say no, and a matcher that tolerates a
few wrong characters tolerates a quote that was never in the document.

A quote must also be at least twelve normalised characters. `"30"` grounds
against forty places in a contract, which is evidence of nothing.

### What grounding does not do

It does not check whether the value is *right*. A real quote paired with a
misread number gets through. That is deliberate, and the failure modes are kept
apart because they are fixed in different places:

- an **ungrounded** field is a model asserting something the document never
  said, and no amount of prompting makes that acceptable;
- a **misread** field is an accuracy number you can watch move.

Conflating them would let a hallucinated citation hide inside an accuracy
percentage. Misreadings are measured by the eval harness; inventions are
structurally impossible to publish.

There is a third mode, and I did not anticipate it — the eval found it on the
first real model run. A **derived** field is a value the model computed from
figures it then cited. Asked for the transaction price of a contract that states
an annual fee and a term, it multiplied the two, reported the product, and
quoted the clause containing both. The quote resolves. Grounding passes it.
Nothing about the citation is false; what was manufactured is the inference
drawn from it.

So the honest statement of what this control does is narrower than "no
hallucinated facts": **it catches invention, not derivation.** A prompt rule
against calculating values mitigates it and does not close it, because the
schema has no way to express "this number was printed" as distinct from "this
number is true". The eval harness is what would catch the next one, which is
most of the argument for having one.

Drops are counted, not swallowed. `dropped_for_no_evidence` appears on the
extraction and on the face of the memo, because a run where it climbs needs
looking at before anyone trusts the output.

## Three states, no confidence score

There is no number like `0.72` anywhere in this codebase. It invites exactly one
question in a review meeting — "why 0.72?" — and there is no honest answer,
because nothing in a contract is 72% true.

| State | Meaning | What a reviewer does |
|---|---|---|
| `extracted` | the document says it, and here is where | reads the citation, moves on |
| `ambiguous` | it says it in more than one place, and they disagree | decides which clause governs |
| `absent` | the document does not address this | raises a drafting gap, or accepts the silence |

Those drive genuinely different actions. A single blended score would have
flattened `absent` and `ambiguous` into "0.4, take a look".

The invariant is enforced on the model itself: an `extracted` field must carry
a value and at least one citation, and an `absent` field may not carry a value.
Constructing an unsupported fact raises a validation error rather than
producing a plausible memo.

## Why the model is given text, not the PDF

The obvious implementation sends the PDF straight to the API. It quietly breaks
grounding.

The model would read the document through the API's own PDF handling, quote
what it saw there, and those quotes would be checked against pdfplumber's
rendering of the same pages — a different string, with different line breaks, a
different treatment of fee tables, and its own idea of where the footer went.
Perfectly faithful quotes would fail to ground, fields would drop, and the
failure would look exactly like the model hallucinating.

Feeding the model the same string grounding searches removes that entire class
of phantom failure.

The cost is real and worth naming: the model never sees the layout. A fee table
arrives as a run of lines, not a grid. Anything carried by position on the page
is gone before the model sees it. Given the alternative was a system whose
error rate depended on two PDF parsers agreeing with each other, it is the
right trade — but it is a trade.

## Two extractors, one gate

Both the model and the offline rule-based extractor emit the same wire format
and pass through the same grounding step. The rules extractor cites its
evidence exactly like the model does. "Nothing is asserted without evidence" is
not a rule about language models.

The rules extractor exists for two reasons: a fresh clone runs end to end with
no API key, and the eval harness gets a floor to measure against. It is not the
product. It works because the corpus is internally consistent, and it stops
working on anyone else's template — which is the honest argument for the model
path, and a better one than a benchmark number.

`--extractor llm` raises rather than falling back. Silently handing someone
regular expressions inside a review that looks fine is the worst outcome
available, so asking for the model path and not getting it is an error.

## The footing check

The deterministic checks include one that compares the sum of the priced
obligations to the stated contract total, at the cent, with no tolerance.

There is nothing for a tolerance to absorb. Both numbers are printed in the
same table, in the same currency, on the same page. A difference of any size
means a line was misread — so the check's failure message says the obligation
list should be treated as incomplete, rather than reporting a variance as
though the contract were wrong.

It is the cheapest available signal that everything below it in the memo is
built on an incomplete reading.

## Reproducibility

The corpus PDFs are generated, not stored by hand, and generation is
byte-reproducible. Two settings get it there, and the second one is the one I
did not expect to need.

`reportlab`'s `invariant` disables the creation timestamp and the random
document id, which is what makes two runs on one machine agree.

Page compression is then turned off as well. That is not about file size. The
page streams are deflated through zlib, and zlib makes no promise of identical
output across versions — Python 3.11 and 3.14 compress the same page to 2050 and
2059 bytes. Identical content, different file. Left on, every contributor
running a different interpreter opens a fresh clone, regenerates, and finds
twelve modified PDFs they never touched — and, because the gold set is keyed by
page, any real drift would be hiding inside that noise. Uncompressed streams
cost about three kilobytes a contract.

The same failure has a text-file twin, handled in `fileio.write_lf`: generated
files that are committed are written with explicit LF, because `Path.write_text`
emits CRLF on Windows. And a binary twin, handled in `.gitattributes`: with
`core.autocrlf=true`, git rewrites the LF bytes inside a committed PDF on
checkout. All three produce the same symptom — a clean clone that is
inexplicably dirty — and all three are silent until someone looks.

The gold set is written to `evals/gold/` and committed rather than computed at
run time. A gold set that regenerates itself from the code being evaluated can
drift silently — change how a spec is authored and "truth" moves with it, while
every score stays flat.
