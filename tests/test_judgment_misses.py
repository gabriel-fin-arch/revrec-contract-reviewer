"""Listing the judgments a saved run got wrong. No test here reaches the API."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from revrec_contract_reviewer.cli import app
from revrec_contract_reviewer.evaluate import SavedRun
from revrec_contract_reviewer.evaluate.misses import judgment_misses, report_lines
from revrec_contract_reviewer.extract import llm

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "evals" / "results"
GOLD = ROOT / "evals" / "gold"
OPUS_5_5 = RESULTS / "llm-claude-opus-5-5-high.claims.json"


def _run(path: Path) -> SavedRun:
    return SavedRun.model_validate_json(path.read_text(encoding="utf-8"))


def test_the_opus_5_5_development_run_shows_its_false_positives_with_the_passages_behind_them():
    """The cases the prompt change in docs/evaluation.md is argued from."""
    misses = judgment_misses(_run(OPUS_5_5), GOLD)
    raised = {(miss.doc_id, miss.judgment): miss for miss in misses if miss.raised}

    assert set(raised) == {
        ("meridian-change-order-03", "distinct_uncertain"),
        ("nimbus-of-beacon", "distinct_uncertain"),
        ("nimbus-msa-calderwood", "variable_consideration_constraint"),
    }
    assert "same integrated engagement" in raised[("meridian-change-order-03", "distinct_uncertain")].passages[0]
    assert "requires the Cartos Spatial Database" in raised[("nimbus-of-beacon", "distinct_uncertain")].passages[0]
    refund = raised[("nimbus-msa-calderwood", "variable_consideration_constraint")]
    assert "refund of prepaid fees" in refund.passages[0]
    assert {(miss.doc_id, miss.judgment) for miss in misses if not miss.raised} == {
        ("nimbus-amendment-orchid", "ssp_not_observable"),
        ("nimbus-of-northgate", "significant_financing"),
        ("nimbus-sow-tessellate", "variable_consideration_constraint"),
    }


def test_the_report_counts_the_misses_by_type():
    lines = report_lines(judgment_misses(_run(OPUS_5_5), GOLD))

    assert lines[0] == "Raised and not in the gold: 3 (distinct_uncertain 2, variable_consideration_constraint 1)"
    assert (
        "In the gold and not raised: 3 (significant_financing 1, ssp_not_observable 1, "
        "variable_consideration_constraint 1)"
    ) in lines


def test_a_run_missing_a_contract_is_refused():
    run = _run(OPUS_5_5)
    run.contracts = run.contracts[1:]

    with pytest.raises(ValueError, match="no claims for"):
        judgment_misses(run, GOLD)


def test_the_command_reads_a_saved_run_without_extracting(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")

    result = CliRunner().invoke(app, ["judgment-misses", str(OPUS_5_5)])

    assert result.exit_code == 0, result.output
    assert "Raised and not in the gold: 3" in result.output
    assert "nimbus-of-beacon: distinct_uncertain" in result.output


def test_the_evaluation_doc_quotes_the_prompt_and_the_passages_as_they_are():
    doc = (ROOT / "docs" / "evaluation.md").read_text(encoding="utf-8")
    section = doc.split("## Judgment precision: one change")[1].split("\n## ")[0]
    quoted = " ".join(line.removeprefix(">").strip() for line in section.splitlines() if line.startswith(">"))
    prompt = " ".join(llm.SYSTEM.split())

    assert quoted.startswith("Only report integration_language") and quoted in prompt
    passages = [miss.passages[0] for miss in judgment_misses(_run(OPUS_5_5), GOLD) if miss.raised]
    for passage in passages:
        assert f'"{passage.split(": ", 1)[1]}"' in section, passage
