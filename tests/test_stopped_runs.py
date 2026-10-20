"""A model run that stops half-way keeps the calls it paid for. No test here reaches the API."""

from __future__ import annotations

import shutil
from decimal import Decimal
from pathlib import Path

import anthropic
import pytest
from anthropic import _exceptions
from typer.testing import CliRunner

from revrec_contract_reviewer.cli import app
from revrec_contract_reviewer.evaluate import SavedRun, evaluate, partial_path, write_gold
from revrec_contract_reviewer.extract import ExtractorChoice, llm
from revrec_contract_reviewer.extract.metering import CallRecord
from revrec_contract_reviewer.extract.schema import ContractField, FieldClaim, WireExtraction

PAYLOAD = WireExtraction(
    fields=[FieldClaim(field=ContractField.CURRENCY, value="GBP", quotes=["All amounts are stated in Pounds Sterling"])]
)
THREE = ("nimbus-msa-vantage.json", "nimbus-of-helix.json", "nimbus-of-pinegrove.json")


def _credit_error() -> anthropic.BadRequestError:
    """The 400 the API returns when the balance runs out. Older SDKs build
    their errors on httpx and newer ones on httpx2, so take whichever it uses."""
    http = getattr(_exceptions, "httpx2", None) or _exceptions.httpx
    request = http.Request("POST", "https://api.anthropic.com/v1/messages")
    return anthropic.BadRequestError(
        "Your credit balance is too low to access the Anthropic API.",
        response=http.Response(400, request=request),
        body=None,
    )


def _call(effort: str | None = None) -> CallRecord:
    return CallRecord(model="claude-opus-5-5", effort=effort or "high", seconds=20.0, cost_usd=Decimal("0.05"))


def _failing_on(nth: int, error):
    """An extractor that answers until its nth call, which raises error()."""
    calls = {"n": 0}

    def extract(document, client=None, effort=None):
        calls["n"] += 1
        if calls["n"] == nth:
            raise error()
        return PAYLOAD, _call(effort)

    return extract


@pytest.fixture
def three_contracts(tmp_path: Path) -> Path:
    full = tmp_path / "all"
    write_gold(full)
    gold = tmp_path / "gold"
    gold.mkdir()
    for name in THREE:
        shutil.copy(full / name, gold)
    return gold


def test_a_run_that_stops_hands_over_the_calls_it_had_paid_for(corpus_dir, three_contracts, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    monkeypatch.setattr(llm, "extract_measured", _failing_on(3, _credit_error))
    checkpoints: list[SavedRun] = []

    with pytest.raises(anthropic.BadRequestError):
        evaluate(corpus_dir, three_contracts, ExtractorChoice.LLM, effort="high", checkpoint=checkpoints.append)

    assert [len(run.contracts) for run in checkpoints] == [1, 2, 2]
    assert [run.stopped is None for run in checkpoints] == [True, True, False]
    last = checkpoints[-1]
    assert last.stopped.startswith("nimbus-of-pinegrove: BadRequestError")
    assert "credit balance is too low" in last.stopped
    assert (last.model, last.effort, len(last.calls()), last.unfinished_calls) == ("claude-opus-5-5", "high", 2, [])
    assert "2 calls" in last.summary() and "USD 0.10" in last.summary()


def test_a_billed_refusal_travels_with_the_run_that_stopped(corpus_dir, three_contracts, monkeypatch):
    """A refusal or an answer cut off at max_tokens was paid for and gave no extraction."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    monkeypatch.setattr(llm, "extract_measured", _failing_on(2, lambda: llm.ModelDeclined("refused", _call())))
    checkpoints: list[SavedRun] = []

    with pytest.raises(llm.ModelDeclined):
        evaluate(corpus_dir, three_contracts, ExtractorChoice.LLM, checkpoint=checkpoints.append)

    last = checkpoints[-1]
    assert (len(last.contracts), len(last.unfinished_calls), len(last.calls())) == (1, 1, 2)
    assert SavedRun.model_validate_json(last.model_dump_json()) == last


def test_a_finished_run_is_the_same_with_or_without_checkpoints(corpus_dir, three_contracts, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    monkeypatch.setattr(llm, "extract_measured", _failing_on(0, _credit_error))
    checkpoints: list[SavedRun] = []

    report, run = evaluate(corpus_dir, three_contracts, ExtractorChoice.LLM, checkpoint=checkpoints.append)
    plain_report, plain_run = evaluate(corpus_dir, three_contracts, ExtractorChoice.LLM)

    assert len(checkpoints) == 3 and checkpoints[-1].contracts == run.contracts
    assert (run.stopped, run.unfinished_calls) == (None, [])
    assert report == plain_report
    assert run.model_dump(exclude={"run_at"}) == plain_run.model_dump(exclude={"run_at"})


def test_eval_save_keeps_a_stopped_run_and_says_what_it_cost(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    runner = CliRunner()
    runner.invoke(app, ["generate-corpus"])
    runner.invoke(app, ["build-gold"])
    results = tmp_path / "evals" / "results"
    monkeypatch.setattr(llm, "extract_measured", _failing_on(3, _credit_error))

    stopped = runner.invoke(app, ["eval", "--extractor", "llm", "--save", "--name", "llm-after"])

    assert stopped.exit_code == 1
    assert "The run stopped: BadRequestError" in stopped.output
    assert "2 contract(s) were extracted" in stopped.output and "USD 0.10" in stopped.output
    partial = SavedRun.model_validate_json(partial_path(results, "llm-after").read_text(encoding="utf-8"))
    assert (len(partial.contracts), len(partial.calls())) == (2, 2)
    assert partial.stopped is not None
    assert not (results / "llm-after.json").exists()

    monkeypatch.setattr(llm, "extract_measured", _failing_on(0, _credit_error))
    finished = runner.invoke(app, ["eval", "--extractor", "llm", "--save", "--name", "llm-after"])

    assert finished.exit_code in (0, 1), finished.output
    assert (results / "llm-after.json").is_file()
    assert not partial_path(results, "llm-after").exists(), "a finished run replaces the partial one"


def test_a_run_stopped_before_any_call_says_nothing_was_billed(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    runner = CliRunner()
    runner.invoke(app, ["generate-corpus"])
    runner.invoke(app, ["build-gold"])
    monkeypatch.setattr(llm, "extract_measured", _failing_on(1, _credit_error))

    result = runner.invoke(app, ["eval", "--extractor", "llm", "--save"])

    assert result.exit_code == 1
    assert "No model call had been billed." in result.output
    assert not list((tmp_path / "evals" / "results").glob("*.partial.claims.json"))
