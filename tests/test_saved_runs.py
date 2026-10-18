"""Saved runs: the claims behind a score, and scoring them again."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from revrec_contract_reviewer.cli import app
from revrec_contract_reviewer.evaluate import (
    CorpusChanged,
    EvalReport,
    SavedRun,
    evaluate,
    rescore,
    write_gold,
)
from revrec_contract_reviewer.extract import ExtractorChoice
from revrec_contract_reviewer.extract.schema import ContractField, FieldClaim, WireExtraction

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def gold_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    target = tmp_path_factory.mktemp("gold")
    write_gold(target)
    return target


@pytest.fixture(scope="module")
def rules_run(corpus_dir: Path, gold_dir: Path) -> tuple[EvalReport, SavedRun]:
    return evaluate(corpus_dir, gold_dir, ExtractorChoice.RULES)


def test_a_saved_run_scores_again_to_the_same_report(rules_run, corpus_dir: Path, gold_dir: Path):
    report, run = rules_run
    from_file = SavedRun.model_validate_json(run.model_dump_json())

    assert len(run.contracts) == 12
    assert rescore(from_file, corpus_dir, gold_dir) == report


def test_the_committed_rules_run_rescores_to_the_committed_report():
    """evals/results/rules.json is a published number; rules.claims.json is
    the run behind it, and scoring that run again has to give that number."""
    results = ROOT / "evals" / "results"
    run = SavedRun.model_validate_json((results / "rules.claims.json").read_text(encoding="utf-8"))
    saved = EvalReport.model_validate_json((results / "rules.json").read_text(encoding="utf-8"))

    assert rescore(run, ROOT / "corpus", ROOT / "evals" / "gold") == saved


def test_a_run_is_not_scored_against_a_pdf_it_did_not_read(rules_run, corpus_dir: Path, gold_dir: Path):
    _, run = rules_run
    tampered = run.model_copy(deep=True)
    tampered.contracts[0].pdf_sha256 = "0" * 64

    with pytest.raises(CorpusChanged, match=tampered.contracts[0].doc_id):
        rescore(tampered, corpus_dir, gold_dir)


def test_a_run_missing_a_contract_is_not_scored_as_if_complete(rules_run, corpus_dir: Path, gold_dir: Path):
    _, run = rules_run
    short = run.model_copy(update={"contracts": run.contracts[1:]})

    with pytest.raises(ValueError, match=f"no claims for {run.contracts[0].doc_id}"):
        rescore(short, corpus_dir, gold_dir)


class _StubMessages:
    def __init__(self, payload: WireExtraction) -> None:
        self._payload = payload

    def parse(self, **kwargs):
        return type("Response", (), {"parsed_output": self._payload, "stop_reason": "end_turn"})()


class _StubClient:
    def __init__(self, payload: WireExtraction) -> None:
        self.messages = _StubMessages(payload)


def test_a_claim_grounding_dropped_is_still_in_the_saved_run(corpus_dir: Path, gold_dir: Path, tmp_path, monkeypatch):
    """The point of keeping claims: what the model said, including what was
    thrown out, not only what survived. A stub stands in for the API."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    one_contract = tmp_path / "gold"
    one_contract.mkdir()
    shutil.copy(gold_dir / "nimbus-of-helix.json", one_contract)
    invented = "invoices are payable within ninety (90) days of the invoice date"
    payload = WireExtraction(fields=[FieldClaim(field=ContractField.NET_DAYS, value="90", quotes=[invented])])

    _, run = evaluate(corpus_dir, one_contract, ExtractorChoice.LLM, client=_StubClient(payload))

    [contract] = run.contracts
    assert contract.claims.fields[0].quotes == [invented]
    assert contract.extraction.dropped_for_no_evidence == 1
    assert contract.extraction.payment.net_days.value is None
    assert run.extractor == "llm"


def test_eval_save_writes_the_claims_and_rescore_reads_them(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    runner = CliRunner()
    runner.invoke(app, ["generate-corpus"])
    runner.invoke(app, ["build-gold"])

    evaluated = runner.invoke(app, ["eval", "--extractor", "rules", "--save"])
    claims = tmp_path / "evals" / "results" / "rules.claims.json"
    rescored = runner.invoke(app, ["rescore", str(claims)])

    assert evaluated.exit_code == rescored.exit_code == 0
    assert claims.is_file()
    table = evaluated.stdout.split("\n\nSaved to")[0]
    assert rescored.stdout.strip() == table.strip()

    (tmp_path / "corpus" / "nimbus-of-helix.pdf").write_bytes(b"%PDF-1.4 not the same contract")
    refused = runner.invoke(app, ["rescore", str(claims)])
    assert refused.exit_code == 1
    assert "Cannot rescore" in refused.output
    assert "Traceback" not in refused.output


def test_the_committed_test_set_run_rescores_to_its_committed_report():
    results = ROOT / "evals" / "results" / "test"
    run = SavedRun.model_validate_json((results / "rules.claims.json").read_text(encoding="utf-8"))
    saved = EvalReport.model_validate_json((results / "rules.json").read_text(encoding="utf-8"))

    assert len(run.contracts) == 7
    assert rescore(run, ROOT / "corpus" / "test", ROOT / "evals" / "gold" / "test") == saved
