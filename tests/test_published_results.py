"""The numbers the README publishes have to be the saved runs, and the saved
rules run has to be what the code produces today.

No API call: the model column is checked against the saved `llm.json`, numbers
only. A failure here means a published number moved; regenerate the README
blocks with `uv run python -m revrec_contract_reviewer.evaluate.published
--write`, and the rules run with `uv run revrec eval --extractor rules --save`,
only once the change is meant.
"""

from __future__ import annotations

import difflib
from pathlib import Path

from revrec_contract_reviewer.evaluate import run_eval, write_gold
from revrec_contract_reviewer.evaluate.published import BLOCKS, README, load, readme_block, render
from revrec_contract_reviewer.extract import ExtractorChoice


def test_the_saved_rules_run_is_what_the_rules_produce_today(corpus_dir: Path, tmp_path: Path):
    gold_dir = tmp_path / "gold"
    write_gold(gold_dir)

    fresh = run_eval(corpus_dir, gold_dir, ExtractorChoice.RULES)
    saved = load("rules")

    moved = [
        f"{name}: saved {getattr(saved, name)} vs now {getattr(fresh, name)}"
        for name in ("fields", "silence", "obligations", "judgments", "citations_total", "citations_resolved",
                     "dropped_for_no_evidence")
        if getattr(saved, name) != getattr(fresh, name)
    ]
    assert not moved, "evals/results/rules.json no longer matches a rules run:\n" + "\n".join(moved)
    assert fresh.model_dump() == saved.model_dump(), "rules.json differs from a fresh run in its per-contract detail"


def test_the_readme_blocks_are_rendered_from_the_saved_runs():
    text = README.read_text(encoding="utf-8")
    expected = render()
    for name in BLOCKS:
        actual = readme_block(text, name)
        diff = "\n".join(
            difflib.unified_diff(actual.splitlines(), expected[name].splitlines(), "README", "saved runs", lineterm="")
        )
        assert actual == expected[name], f"README block {name} is out of date:\n{diff}"


def test_the_judgment_precision_drop_in_the_prose_matches_the_runs():
    rules, model = load("rules"), load("llm")
    sentence = f"drops judgment precision from {rules.judgments.precision:.2f} to {model.judgments.precision:.2f}"
    assert sentence in " ".join(README.read_text(encoding="utf-8").split())


TEST_RESULTS = README.parent / "evals" / "results" / "test"
EVALUATION = README.parent / "docs" / "evaluation.md"


def _test_runs():
    """The three published test-set runs: rules, Claude Opus 5.5, Claude Opus 5."""
    return (
        load("rules", TEST_RESULTS),
        load("llm-claude-opus-5-5-high", TEST_RESULTS),
        load("llm-claude-opus-5-high", TEST_RESULTS),
    )


def _flat(path: Path) -> str:
    """The file as one line: prose wraps, and a wrap must not hide a drift."""
    return " ".join(path.read_text(encoding="utf-8").split())


def test_the_test_set_prose_in_the_readme_matches_the_saved_runs():
    rules, opus55, opus5 = _test_runs()
    text = _flat(README)

    for figure, sentence in (
        (rules.judgments.recall, f"judgments at {rules.judgments.recall:.2f}"),
        (opus5.judgments.precision, f"Claude Opus 5's judgment precision drops to {opus5.judgments.precision:.2f}"),
        (opus55.judgments.precision, f"Claude Opus 5.5 holds at {opus55.judgments.precision:.2f}"),
    ):
        assert sentence in text, f"README prose no longer matches the saved test runs ({figure}): {sentence}"


def test_the_test_set_prose_in_the_evaluation_doc_matches_the_saved_runs():
    rules, opus55, opus5 = _test_runs()
    text = _flat(EVALUATION)

    assert (
        f"Citations re-resolved: {opus55.citations_resolved}/{opus55.citations_total} for Opus 5.5, "
        f"{opus5.citations_resolved}/{opus5.citations_total} for Opus 5." in text
    )
    assert (
        f"Claims dropped for no evidence: {opus55.dropped_for_no_evidence} "
        f"and {opus5.dropped_for_no_evidence}." in text
    )

    # "8/8 on every run" is only true if every run agrees on both numbers.
    blanks = {
        (run.silence.true_positives, run.silence.true_positives + run.silence.false_positives)
        for run in (rules, opus55, opus5)
    }
    assert len(blanks) == 1, f"the runs disagree on blank fields: {blanks}"
    (tp, total), = blanks
    assert f"Unstated fields left blank: {tp}/{total} on every run" in text

    found = {
        (run.judgments.true_positives, run.judgments.true_positives + run.judgments.false_negatives)
        for run in (opus55, opus5)
    }
    assert len(found) == 1, f"the models disagree on judgments found: {found}"
    (tp, total), = found
    assert f"Both models find {tp} of the {total} expected judgments" in text
