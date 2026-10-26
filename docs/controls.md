# Controls

What each control in the review is for, where the code enforces it, which
test proves it, and what a run writes that evidences it. A run is
`revrec review` on a folder: per contract, `<contract>.html`,
`<contract>.pdf` and `<contract>.json`; for the run, `index.html` and
`worklist.xlsx`. `revrec conclusions` on the filled-in worklist adds
`conclusions.json` and rewrites the memos and the index with it.

This is a portfolio project on a synthetic corpus. The matrix says what the
code does and how to check it, not that anyone has audited it.

Code paths are relative to `src/revrec_contract_reviewer/` unless they start
with `tests/`. `tests/test_controls_doc.py` checks that every file, function
and test named here exists, that every row names a test, and that every
evidence file is one a run writes.

| # | Control objective | Enforced in | Proved by | Evidence |
|---|---|---|---|---|
| 1 | No value without the words it was read from: a claim whose quote can't be found in the document is dropped, whoever made it. | `extract/grounding.py::Grounder` | `tests/test_grounding.py::test_a_claim_whose_quote_is_not_in_the_document_is_dropped`, `tests/test_llm_extractor.py::test_a_fabricated_quote_from_the_model_is_dropped` | `<contract>.html`, `<contract>.pdf` (quote, clause and page beside every value), `<contract>.json` |
| 2 | A quote too short to identify anything grounds nothing. | `extract/grounding.py::Grounder` | `tests/test_grounding.py::test_a_quote_too_short_to_identify_anything_is_refused` | `<contract>.json` (dropped for no evidence) |
| 3 | Two clauses that disagree are shown as a conflict with both passages, or not at all. | `extract/grounding.py::Grounder` | `tests/test_grounding.py::test_conflicting_claims_become_ambiguous_with_both_quotes`, `tests/test_grounding.py::test_a_conflict_with_one_passage_missing_is_dropped` | `<contract>.html`, `<contract>.pdf` |
| 4 | What wasn't found is reported as not found, never as what the contract says. | `report/memo.py::FactRow`, `assess/judgments.py::raise_flags` | `tests/test_grounding.py::test_a_missing_claim_is_absent_without_counting_as_a_drop`, `tests/test_assess.py::test_an_uncapped_term_is_described_as_not_found_not_as_unlimited` | `<contract>.html`, `<contract>.pdf` (supporting schedule) |
| 5 | The eight judgments a contract can't answer go to a person, each with the reason it isn't answered. | `assess/judgments.py::raise_flags`, `models/judgment.py::WHY_A_HUMAN` | `tests/test_assess.py::test_every_flag_carries_a_standing_reason_it_is_not_automated`, `tests/test_report_and_eval.py::test_every_judgment_in_the_memo_states_why_it_was_not_answered` | `<contract>.html`, `<contract>.pdf`, `worklist.xlsx` |
| 6 | Checks with a definite answer (the fee schedule foots, parties, effective date, currency, priced obligations, recognition pattern) are kept apart from judgments and fail on any difference. | `assess/checks.py::run_checks` | `tests/test_assess.py::test_footing_fails_on_any_difference_at_all`, `tests/test_assess.py::test_a_missing_currency_fails_its_check` | `<contract>.html`, `<contract>.pdf` (checks), `worklist.xlsx` (failed checks) |
| 7 | A file that can't be read is listed first, the rest of the folder is still reviewed, and the run exits 1. | `pipeline.py::review_directory`, `cli.py::review` | `tests/test_cli.py::test_one_unreadable_file_does_not_stop_the_rest_of_the_folder` | `index.html`, `worklist.xlsx` |
| 8 | Asking for the model without a key fails loudly, and every memo names the extractor that produced it. | `extract/__init__.py::extract_contract` | `tests/test_llm_extractor.py::test_asking_for_the_model_without_a_key_fails_loudly`, `tests/test_report_and_eval.py::test_the_memo_names_the_extractor_that_produced_it` | `<contract>.html`, `<contract>.pdf`, `<contract>.json` (extractor and model) |
| 9 | A model refusal isn't read as an empty extraction: asked for the model, the run stops; on auto, it falls back to the rules and says so. | `extract/llm.py::ModelDeclined` | `tests/test_llm_extractor.py::test_a_refusal_is_not_read_as_an_empty_extraction` | `<contract>.json` (extractor) |
| 10 | Every citation still resolves against its document when the run is scored, and one that doesn't fails the eval. | `cli.py::eval_command` | `tests/test_report_and_eval.py::test_the_eval_runs_end_to_end_and_every_citation_resolves` | `evals/results/rules.json` |
| 11 | Every open item in a run reaches the reviewer, contracts needing most attention first. | `report/memo.py::attention_order`, `report/worklist.py::worklist_rows` | `tests/test_report_and_eval.py::test_a_document_that_could_not_be_read_does_not_sink_to_the_bottom`, `tests/test_worklist_and_pdf.py::test_every_open_item_in_the_run_is_one_row` | `index.html`, `worklist.xlsx` |
| 12 | The memo filed as a PDF says what the review says, each quote with its clause and page. | `report/pdf.py::render_pdf_memo` | `tests/test_worklist_and_pdf.py::test_every_pdf_memo_says_what_its_review_says` | `<contract>.pdf` |
| 13 | A conclusion is the reviewer's, recorded not made: the worklist's reviewer columns are read back against the run row by row, a workbook from another run is refused, an edited or added row is reported with its row, and a conclusion without a reviewer or a date is not accepted. | `conclusions.py::collect_conclusions`, `report/worklist.py::run_id` | `tests/test_conclusions.py::test_a_workbook_from_another_run_is_refused`, `tests/test_conclusions.py::test_an_edited_row_is_reported_with_its_row`, `tests/test_conclusions.py::test_a_conclusion_without_a_reviewer_or_a_date_is_reported_not_accepted` | `conclusions.json`, `index.html`, `<contract>.html` (each item concluded, with who and when, or open) |
| 14 | Instruction-shaped text in a contract can't steer the review (prompt injection): the offline review of an injected document is exactly the clean document's review, a model complying with the injection can't produce a clean review, and the document reaches the model as data in the user message, not as instructions. | `extract/llm.py::USER_TEMPLATE`, `extract/grounding.py::Grounder`, `assess/judgments.py::raise_flags` | `tests/test_prompt_injection.py::test_the_offline_review_ignores_instruction_shaped_text`, `tests/test_prompt_injection.py::test_a_model_complying_with_extract_nothing_cannot_produce_a_clean_review`, `tests/test_prompt_injection.py::test_the_document_reaches_the_model_as_data_not_instructions` | `<contract>.html`, `<contract>.json` (the same review, injected document or not) |

## What this doesn't control

- **Whether a reading is right.** Grounding proves the quoted words are in
  the document, not that the value was read correctly from them
  (`tests/test_grounding.py::test_grounding_does_not_check_whether_the_value_is_right`).
  Accuracy is measured against the gold set, not asserted; see
  `docs/evaluation.md`.
- **A value quoted from injected text.** Injection text is document text, so
  a model that quotes it produces a citation that resolves
  (`tests/test_prompt_injection.py::test_a_quote_taken_from_the_injection_itself_can_ground`).
  The injection cannot silence the review -- control 14 -- but a value read
  from it can still be wrong, and the guard there is the reviewer, not the tool.
- **Whether a conclusion is right.** `conclusions.json` records who concluded
  what and when, exactly as typed, and the memos show it; the judgment itself
  stays the reviewer's. Rows about files the run could not read have no JSON
  to match against, so a conclusion on one is the reviewer's own record
  (`conclusions.py`, module docstring).
- **Scanned contracts.** A PDF with no text layer is reported as unreadable,
  not read.
