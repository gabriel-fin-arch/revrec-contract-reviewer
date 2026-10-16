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
