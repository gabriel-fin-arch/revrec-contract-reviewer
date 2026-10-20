"""Listing the judgments a saved run got wrong. No test here reaches the API."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from revrec_contract_reviewer.cli import app
from revrec_contract_reviewer.evaluate import SavedRun, rescore
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
        ("nimbus-sow-tessellate", "distinct_uncertain"),
        ("nimbus-sow-tessellate", "variable_consideration_constraint"),
    }


def test_the_report_counts_the_misses_by_type():
    lines = report_lines(judgment_misses(_run(OPUS_5_5), GOLD))

    assert lines[0] == "Raised and not in the gold: 3 (distinct_uncertain 2, variable_consideration_constraint 1)"
    assert (
        "In the gold and not raised: 4 (distinct_uncertain 1, significant_financing 1, ssp_not_observable 1, "
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


def _section() -> str:
    doc = (ROOT / "docs" / "evaluation.md").read_text(encoding="utf-8")
    return doc.split("## Judgment precision: one change")[1].split("\n## ")[0]


def test_the_evaluation_doc_quotes_the_passages_and_the_prompt_is_back_to_its_old_text():
    """The change was dropped: the doc keeps what was tried, the prompt doesn't."""
    section = _section()
    quoted = " ".join(line.removeprefix(">").strip() for line in section.splitlines() if line.startswith(">"))
    prompt = " ".join(llm.SYSTEM.split())

    assert quoted.startswith("Only report integration_language")
    assert "related, not integrated" in quoted and "related, not integrated" not in prompt
    assert (
        "Only report integration_language where the contract actually describes one promise as customising, "
        "integrating with, or depending on another. Do not supply it because the arrangement looks like it "
        "might be."
    ) in prompt
    passages = [miss.passages[0] for miss in judgment_misses(_run(OPUS_5_5), GOLD) if miss.raised]
    for passage in passages:
        assert f'"{passage.split(": ", 1)[1]}"' in section, passage


def _pr(tp: int, fp: int, fn: int) -> str:
    return f"{tp / (tp + fp):.2f} / {tp / (tp + fn):.2f}"


def test_the_before_and_after_table_is_what_the_saved_runs_score():
    section = _section()
    sets = {
        "Development": (RESULTS, ROOT / "corpus", GOLD),
        "Test": (RESULTS / "test", ROOT / "corpus" / "test", GOLD / "test"),
    }
    for label, (results, corpus, gold) in sets.items():
        cells = []
        without_aster = []
        for name in ("llm-claude-opus-5-5-high", "llm-claude-opus-5-5-high-integration"):
            report = rescore(_run(results / f"{name}.claims.json"), corpus, gold)
            judgments = report.judgments
            cells.append(_pr(judgments.true_positives, judgments.false_positives, judgments.false_negatives))
            rest = [score.judgments for score in report.per_contract if score.doc_id != "meridian-msa-aster"]
            without_aster.append(
                _pr(
                    sum(t.true_positives for t in rest),
                    sum(t.false_positives for t in rest),
                    sum(t.false_negatives for t in rest),
                )
            )
        assert f"| {label} | {cells[0]} | {cells[1]} |" in section, (label, cells)
        if label == "Development":
            assert f"| Development without Aster | {without_aster[0]} | {without_aster[1]} |" in section


def test_the_after_runs_are_published_with_their_tokens_cost_and_latency():
    section = _section()
    for label, results in (("development", RESULTS), ("test", RESULTS / "test")):
        calls = _run(results / "llm-claude-opus-5-5-high-integration.claims.json").calls()
        tokens_in = sum(c.input_tokens + c.cache_creation_input_tokens + c.cache_read_input_tokens for c in calls)
        row = (
            f"| After, {label} | {len(calls)} | {tokens_in:,} | {sum(c.output_tokens for c in calls):,} | "
            f"{sum(c.cost_usd for c in calls if c.cost_usd):.2f} | {sum(c.seconds for c in calls):.1f} | "
            f"{max(c.seconds for c in calls):.1f} s |"
        )
        assert row in section, row
        assert {c.stop_reason for c in calls} == {"end_turn"}
