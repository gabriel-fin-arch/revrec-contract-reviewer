# Changelog

## Unreleased

- A `Dockerfile` that reviews the committed corpus offline with one command
  and writes the memos and the index to a mounted folder. Runtime
  dependencies only, a non-root user, no `.env` or API key in the image
  (`.dockerignore`). CI builds the image, runs the review in it and checks
  the memos reach the host. It runs `review` until the `demo` command lands.
- pre-commit: ruff, whitespace, end-of-file, YAML, TOML, merge-conflict and
  large-file checks, and two that refuse a commit holding a `.env` or
  anything shaped like an Anthropic API key. ruff runs at the project's own
  version through uv. CI's lint step is now `pre-commit run --all-files`, so
  the hooks and CI check the same things; `uv run pre-commit install` sets
  them up. Needs pre-commit 4.4 or later. Two test files lost a trailing blank
  line to the end-of-file check, in a commit of their own.
- A model run that stops part-way keeps what it paid for. `evaluate` hands
  over the run so far after every contract, and once more with the reason if
  an extraction raises; `eval --save` writes it to
  `<name>.partial.claims.json` as it goes and removes it when the run
  finishes. A stopped run says how many calls it made and what they cost, or
  that none was billed, and a refusal or a cut-off answer is kept with it.
  Before, the run was written only at the end, so the calls before a failure
  were paid for and lost: the runs of 19 October for the change below stopped
  when the API refused requests for lack of credit, and whatever went
  through before that wasn't kept.
- One change for judgment precision, argued from the development set,
  measured and dropped. The prompt's guidance on `integration_language` was
  tightened to promises the customer can't benefit from separately, since two
  of the three judgments Claude Opus 5.5 raised against the development gold
  came from passages that only say services are related. Measured on 20
  October with Claude Opus 5.5 at effort high (19 calls, USD 0.94): on the
  test set judgment precision / recall stayed at 0.85 / 0.92, with the same
  misses; on the development set the two targeted flags went, one appeared on
  Tessellate, and Aster came back nearly empty, 0.87 / 0.87 to 0.89 / 0.74.
  The test set decides, so the prompt is back to its 19 October text; the
  runs are kept in `evals/results/` with a test that rescores them.
  `revrec judgment-misses` lists the judgments a saved run raised or missed
  with the passages behind them, without calling the API, and
  `eval --save --name` saves a run beside the one before it.
  `docs/evaluation.md` has the cases, the change, the results and an open
  question about the development gold (Aster and Tessellate).
- Measured Claude Opus 5.5, the default model, at effort high on both sets, and
  repeated Claude Opus 5 the same way, on 19 October 2026: 38 calls, USD 2.04 at
  the published prices. Judgment precision / recall: Opus 5.5 0.87 / 0.87 on
  the development set and 0.85 / 0.92 on the test set; Opus 5 0.85 / 0.96 and
  0.65 / 0.92. The README and `docs/evaluation.md` show each run with its date,
  model, effort and cost; the September run in `llm.json` is unchanged, and
  the docs say why its 0.76 can't be compared with today's 0.85 more closely.
  Two places where both models disagree with the test-set gold (Wexford's term
  and price, Harbourline's handover workshop) are listed as open questions; the
  gold is unchanged.
- A model run is measured as well as scored. The request sets the effort
  explicitly (`high` by default; `eval --effort` or `REVREC_EFFORT`), and every
  call is saved with the run: model, effort, stop reason, tokens, seconds and
  cost at the published prices, dated (`extract/metering.py`). `eval` prints the
  totals, and `--save` names a model run `llm-<model>-<effort>.json`, so it no
  longer replaces `llm.json`. A refusal or a response cut off at `max_tokens`
  raises with its call record. `revrec estimate` gives the bounds on a run's
  tokens and cost without calling the API. No model run is included here.
- `anthropic>=0.77` was too low again: 0.77 types `output_config` with a format
  and no effort, so the effort the request now sets could be dropped without a
  word. The floor is 0.78, the first that takes it, and a test checks the
  installed SDK does.
- The first run on the held-out test set, rules extractor: fields 1.00 / 0.89,
  obligations 0.67 / 0.50, judgments 1.00 / 0.42, against 1.00 / 0.91,
  0.79 / 0.75 and 0.95 / 0.83 on the development set. Saved in
  `evals/results/test/` with its claims. The README and `docs/evaluation.md`
  now say which numbers are which, list what the rules missed on the test
  set, and state the rule that nothing seen there is used to tune the rules,
  the prompt or the scorer. CI also runs the test set offline and fails if a
  citation in it stops resolving.
- A held-out test set: seven synthetic contracts in `corpus/test/`, generated
  the same way as the twelve in `corpus/` from `corpus/heldout.py`, with their
  gold records in `evals/gold/test/`. They were written after the rules and the
  prompt and committed before either extractor ran on them. `generate-corpus`,
  `build-gold`, `eval` and `rescore` take `--set test`. Tests check that the
  set rebuilds byte for byte, that its gold matches its specs, that it shares
  no contract or customer with the development set, and that no extractor
  source or prompt names one of its contracts.
- A saved run keeps its claims. `eval --save` writes, next to the report,
  `<extractor>.claims.json`: for each contract, the PDF's SHA-256, every
  claim the extractor returned with its quotes, and the extraction grounding
  made of them. `revrec rescore` scores a saved run again from that file
  without extracting, and refuses if a PDF has changed since the run.
  `evals/results/rules.claims.json` is the run behind `rules.json`, and a
  test checks that rescoring it gives `rules.json`. The September model run
  was saved before this and still has only its counts.
- The memo as a PDF, for filing: `review` writes `<contract>.pdf` beside each
  HTML memo, with the same content in the same order, every quote with its
  clause and page. A test reads the PDF back with pdfplumber and checks each
  judgment's quotes inside that judgment, each check with its result and each
  value with its label, for all twelve contracts. Built with reportlab, with
  `invariant` set, so the same review gives the same bytes.
- `worklist.xlsx` for a folder review: every judgment, failed check and
  unreadable file in the run, one row each, in the index's order, with the
  quote, clause and page and blank columns for the reviewer's conclusion,
  plus a sheet listing every contract. The index and the workbook now share
  one ordering function. Needs openpyxl.
- `docs/controls.md`: twelve controls of the review, each with the code that
  enforces it, the test that proves it and the output that evidences it, and
  what the review doesn't control. A test fails if anything it names stops
  existing, or if it cites an output a run doesn't write.
- The published numbers are checked now. The Results table and a new
  three-line summary near the top of the README are rendered from
  `evals/results/` by `revrec_contract_reviewer.evaluate.published`, and the
  tests fail if the README and the saved runs disagree, if the prose's
  judgment-precision figures drift, or if a fresh rules run no longer matches
  `rules.json`. The table it renders is the one the README already had.
- The commit history has its real dates. Every commit's author date is now the
  time it was made, taken from my Claude Code session logs, and no file
  changed. The commits of 13 October are back as they were pushed that day,
  and what each publishing rewrite changed in the files is a bridge commit.
  `PROVENANCE.md` says how, with the full commit map and how to check it, and
  now also says how the history was first made: the first 47 commits by one
  script run, the dates set on 1 October by another.
- "How I built this" said the assistant drafted most of the code. It wrote all
  of it, and the tests; the design notes behind it I drafted with the help of
  an AI chat. The README says so now.
- The Meridian change order is dated 14 January 2026 again. `3616819` had moved
  it to 14 October 2025, saying it was dated after the study it amends had
  finished; that study runs to 2027, and the real reason was that a contract
  signed in 2026 didn't fit the backdated history. The corpus PDFs and the gold
  set are now byte-for-byte those of the commit that saved the model run.
  `docs/architecture.md` says again that intercompany-close-agent was the first
  project, which `8adaa13` had removed for the same reason. `PROVENANCE.md`
  lists both, with the design notes' plan for making the history look
  hand-written, and the README's note says the dates before 13 October are
  invented: the 13 October commits have their real times.
- The README's note on the commit history took up most of the first screen.
  It's shorter now and keeps every fact. It, `PROVENANCE.md`,
  `docs/evaluation.md` and the comment in `extract/llm.py` give the model run's
  date, 10 September 2026, and the README and `PROVENANCE.md` say this repo was
  first published under the earlier account, which they had left out.
- The model run is Claude Opus 5's, from September 2026, not Claude Opus 4's
  from November 2025. The harness wrote `claude-opus-5` into
  `evals/results/llm.json`; I relabelled it in the history rewrite of 13
  October to fit the backdated commits. `llm.json`, the README,
  `docs/evaluation.md`, `PROVENANCE.md` and the comment on the default model in
  `extract/llm.py` say Claude Opus 5 again. Three entries below said otherwise
  and have been corrected; their earlier wording is in the git history.
- The README's note on the commit history, and `PROVENANCE.md`, still said I
  built this in 2025 and rebuilt a lost git history when publishing. I built it
  in September 2026, and the commits were backdated as they were made. Both say
  so now, along with what I said earlier that wasn't true. The licence year is
  2026.
- `PROVENANCE.md` said my Anthropic Console usage for November 2025 shows the
  model run. There was no run in November 2025. That sentence is gone.
- The README's note on the commit history left out what the publishing
  rewrites actually did, including relabelling the model run. It says so now,
  and `PROVENANCE.md` lists every force-push and the deleted CI runs, with how
  to check each one.
- The history rewrite of 13 October 2026 (see `PROVENANCE.md`) also changed
  four things in the current files, and they are back to what they were before
  it. The corpus PDFs are rendered with reportlab 4.4.6 or later again (4.4.6
  through 5.0.1 produce identical bytes), so the floor is `reportlab>=4.4.6`
  instead of a cap below it. `extract/schema.py` gives the structured-outputs
  reason for the flat list of claims again. And the entries below about the
  anthropic and reportlab floors, and about the wire schema, say what they said
  before the rewrite.
- The default model was still Claude Opus 4, put there by the history rewrite
  of 13 October. It was retired on 15 June 2026 and supports neither adaptive
  thinking nor structured outputs, the two things the `messages.parse` call asks
  for. The stubbed tests could not see it and CI has no key. The default is
  Claude Opus 5.5 now. The published model numbers are still the Claude Opus 5
  run from September 2026, and the README and `docs/evaluation.md` say so rather
  than implying they were re-measured.
- A refusal arrives as a successful response with nothing parsed, and would have
  failed later in assembly with nothing pointing at the cause. It raises
  `ModelDeclined` now: `--extractor llm` stops, and AUTO falls back to the rules
  the same way it does on an API error.
- `anthropic>=0.40` was wrong. `messages.parse(output_format=...)` arrived in 0.77,
  and the stubbed tests could not notice. Raised the floor and added a test
  against the real client's signature.
- The other floors had the same problem: pydantic 2.6 rejects the generic
  `ExtractedField` the extractors build (35 tests fail; 2.10 is the first that
  passes), typer 0.12 crashes on `revrec review --help` against current click,
  and reportlab 4.1 renders a corpus that differs from the committed one in
  every file. Raised all three, checked by installing the lowest versions the
  constraints allow, and added tests for subcommand help and for rebuilding the
  corpus against the PDFs in the repo rather than against itself.
- The master agreement failed "Currency identified" with a detail about bare
  numbers that cannot be consolidated, in a document with no numbers in it. The
  corpus README says it should come out clean, and now it does: no amounts read
  means no currency to require. The rules run goes from 11 to 10 contracts
  needing a reviewer.
- The recognition check failed every subscription and support term the contract
  did not describe a control transfer for, which is all of them: in the model
  run, 11 of 12 contracts failed it and none needed no attention. Those are
  stand-ready promises, over time under 606-10-25-27(a) by what they are, and
  pass on the promise now. Implementation, training, clinical services and
  resale still fail on silence, since for them the contract's terms decide it.
- A claim marked conflicting became `ambiguous` as soon as one of its quotes
  grounded, so the memo could present a disagreement between two clauses while
  citing one. Both passages have to be found now, or the field is dropped and
  counted. `docs/architecture.md` also still described `absent` as "the document
  does not address this", which is the claim the memo stopped making.
- One unreadable PDF in a folder (scanned, damaged, or not a PDF) ended the
  whole run in a traceback before any memo was written. The rest of the folder
  is reviewed now, the unreadable files head the index with the reason, and the
  command exits 1 so a script can tell it wasn't a full run. Bad input on the
  command line is a one-line message instead of a traceback.
- The silence row printed a precision, a recall and an F1. Every unstated field
  is either left blank or invented, so nothing was ever counted as a miss and
  the recall was 1.00 by construction. It is reported as what it is now: 21 of
  21 unstated fields left blank, on both runs.
- The variable consideration flag said uncapped terms "state no ceiling" (with
  "1 of these terms state" for a single one). A cap nobody found is not a
  contract saying the amount is unlimited; it reads "no ceiling was found" now.
- Measured the model extractor against the gold set for the first time. It beats
  the regex baseline on recall everywhere and loses judgment precision, 0.95 to
  0.76; `docs/evaluation.md` has the comparison and does not round the loss off.
- The wire schema is a flat list of claims that name their own field. One named
  optional field per contract term does not compile as a strict output schema --
  twenty-one of them exceeded both the union-parameter cap and the grammar size
  limit, and splitting the request in two did not help either.
- Added a prompt rule against deriving values by calculation, after the first
  real run reported a transaction price it had multiplied out and a term it had
  counted between two dates, citing the inputs in both cases. Grounding cannot
  catch that: the citations resolve.

- Eval harness reports precision and recall for contract fields, silence on
  unstated fields, performance obligations and judgment flags, and re-resolves
  every citation against its source document.
- Review memo in HTML with the supporting quote and page beside every value,
  plus JSON for anything downstream.
- Eight-item judgment taxonomy, each with a standing reason it is not answered.
- Deterministic checks including a fee-schedule footing test.
- Model extraction via the Anthropic SDK, with an offline rule-based extractor
  behind the same grounding gate so a clone runs with no API key.
- Twelve-contract synthetic corpus, generated byte-reproducibly.

### Known gaps

- The rules extractor only reads fees laid out in a table; three contracts
  state theirs in prose and lose their totals. See `docs/evaluation.md`.
- `upfront_fee` and `upfront_fee_refundable` are in the schema and the memo, and
  only the model extractor fills them. The offline path leaves them empty, and
  the memo says "not found" rather than "not stated" for exactly this reason.
- Running headers are not detected, only page-number footers. No document in
  the corpus has one, and handling something untested would be a claim the
  tests could not back.
- The eval scores ten scalar fields. `billing_frequency`, `duration_months` and
  the renewal terms appear in the memo but are not scored, so their accuracy is
  asserted by tests rather than measured across the corpus.
