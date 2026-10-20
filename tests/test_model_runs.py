"""How a model run is measured and costed. No test here reaches the API."""

from __future__ import annotations

import shutil
from decimal import Decimal
from pathlib import Path

import anthropic
import pytest
from typer.testing import CliRunner

from revrec_contract_reviewer.cli import app
from revrec_contract_reviewer.evaluate import SavedRun, evaluate, write_gold
from revrec_contract_reviewer.evaluate.estimate import estimate_run
from revrec_contract_reviewer.extract import ExtractorChoice, llm
from revrec_contract_reviewer.extract.metering import PRICES_AS_OF, CallRecord, cost_usd
from revrec_contract_reviewer.extract.schema import ContractField, FieldClaim, WireExtraction
from revrec_contract_reviewer.models.document import ContractDocument

ROOT = Path(__file__).resolve().parent.parent


class _Usage:
    def __init__(self, input_tokens=5000, output_tokens=3000, cache_creation_input_tokens=0, cache_read_input_tokens=0):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_creation_input_tokens = cache_creation_input_tokens
        self.cache_read_input_tokens = cache_read_input_tokens


class _Messages:
    def __init__(self, payload, stop_reason, usage, recorder):
        self._payload, self._stop_reason, self._usage, self._recorder = payload, stop_reason, usage, recorder

    def parse(self, **kwargs):
        self._recorder.update(kwargs)
        return type(
            "Response", (), {"parsed_output": self._payload, "stop_reason": self._stop_reason, "usage": self._usage}
        )()


class _Client:
    def __init__(self, payload, stop_reason="end_turn", usage=None):
        self.calls: dict = {}
        self.messages = _Messages(payload, stop_reason, usage or _Usage(), self.calls)


PAYLOAD = WireExtraction(
    fields=[FieldClaim(field=ContractField.CURRENCY, value="GBP", quotes=["All amounts are stated in Pounds Sterling"])]
)


def test_a_call_is_costed_at_the_published_price_of_each_kind_of_token():
    million = 1_000_000

    assert cost_usd("claude-opus-5-5", million, 0) == Decimal("4")
    assert cost_usd("claude-opus-5-5", 0, million) == Decimal("20")
    assert cost_usd("claude-opus-5-5", 0, 0, cache_creation_input_tokens=million) == Decimal("5")
    assert cost_usd("claude-opus-5-5", 0, 0, cache_read_input_tokens=million) == Decimal("0.2")
    assert cost_usd("claude-opus-5", million, million) == Decimal("30")
    assert cost_usd("a-model-with-no-published-price", million, million) is None


def test_the_request_sets_the_effort_and_the_record_keeps_what_the_api_reported(helix: ContractDocument):
    client = _Client(PAYLOAD, usage=_Usage(input_tokens=1200, output_tokens=800, cache_read_input_tokens=3000))

    claims, call = llm.extract_measured(helix, client=client)

    assert claims == PAYLOAD
    assert client.calls["output_config"] == {"effort": "high"}
    assert client.calls["thinking"] == {"type": "adaptive"}
    assert (call.model, call.effort, call.stop_reason) == (llm.model_name(), "high", "end_turn")
    assert (call.input_tokens, call.output_tokens, call.cache_read_input_tokens) == (1200, 800, 3000)
    assert call.cost_usd == cost_usd(llm.model_name(), 1200, 800, cache_read_input_tokens=3000)
    assert call.seconds >= 0
    assert call.prices_as_of == PRICES_AS_OF


def test_the_effort_comes_from_the_argument_then_the_environment(helix: ContractDocument, monkeypatch):
    monkeypatch.setenv("REVREC_EFFORT", "medium")
    assert llm.extract_measured(helix, client=_Client(PAYLOAD))[1].effort == "medium"
    assert llm.extract_measured(helix, client=_Client(PAYLOAD), effort="xhigh")[1].effort == "xhigh"

    monkeypatch.setenv("REVREC_EFFORT", "extreme")
    with pytest.raises(ValueError, match="REVREC_EFFORT must be one of"):
        llm.extract_measured(helix, client=_Client(PAYLOAD))


@pytest.mark.parametrize(("payload", "stop_reason"), [(None, "refusal"), (None, "max_tokens")])
def test_a_call_that_returns_no_extraction_still_reports_what_it_cost(helix, payload, stop_reason):
    """The tokens were spent either way, so the record travels with the error."""
    with pytest.raises(llm.ModelDeclined) as raised:
        llm.extract_measured(helix, client=_Client(payload, stop_reason=stop_reason))

    assert raised.value.call is not None
    assert raised.value.call.stop_reason == stop_reason
    assert raised.value.call.output_tokens == 3000


def test_a_saved_model_run_keeps_every_call_and_sums_them(corpus_dir: Path, tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    full = tmp_path / "all"
    write_gold(full)
    gold = tmp_path / "gold"
    gold.mkdir()
    for name in ("nimbus-of-helix.json", "nimbus-of-pinegrove.json"):
        shutil.copy(full / name, gold)

    _, run = evaluate(corpus_dir, gold, ExtractorChoice.LLM, client=_Client(PAYLOAD), effort="high")

    assert [c.doc_id for c in run.contracts] == ["nimbus-of-helix", "nimbus-of-pinegrove"]
    assert len(run.calls()) == 2
    assert (run.model, run.effort) == (llm.model_name(), "high")
    assert run.run_at and run.run_at.endswith("Z")
    summary = run.summary()
    assert summary is not None
    assert "2 calls" in summary and "effort high" in summary
    assert f"USD {2 * cost_usd(llm.model_name(), 5000, 3000):.2f}" in summary
    assert SavedRun.model_validate_json(run.model_dump_json()) == run


def test_a_rules_run_has_no_calls_and_no_cost_line(corpus_dir: Path, tmp_path: Path):
    write_gold(tmp_path)

    _, run = evaluate(corpus_dir, tmp_path, ExtractorChoice.RULES)

    assert run.calls() == []
    assert run.summary() is None


def test_a_saved_model_run_is_named_for_its_model_and_effort(tmp_path: Path, monkeypatch):
    """So the September run in llm.json is never overwritten by a new one."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    runner = CliRunner()
    runner.invoke(app, ["generate-corpus"])
    runner.invoke(app, ["build-gold"])

    def stubbed(document, client=None, effort=None):
        call = CallRecord(model=llm.model_name(), effort=effort or "high", seconds=0.5, cost_usd=Decimal("0.1"))
        return PAYLOAD, call

    monkeypatch.setattr(llm, "extract_measured", stubbed)

    result = runner.invoke(app, ["eval", "--extractor", "llm", "--effort", "high", "--save"])

    assert result.exit_code in (0, 1), result.output
    results = tmp_path / "evals" / "results"
    assert (results / f"llm-{llm.model_name()}-high.json").is_file()
    assert (results / f"llm-{llm.model_name()}-high.claims.json").is_file()
    assert not (results / "llm.json").exists()
    assert "Model run:" in result.output and "USD 1.20" in result.output


def test_a_run_after_a_change_can_be_saved_beside_the_one_before_it(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    runner = CliRunner()
    runner.invoke(app, ["generate-corpus"])
    runner.invoke(app, ["build-gold"])

    def stubbed(document, client=None, effort=None):
        call = CallRecord(model=llm.model_name(), effort=effort or "high", seconds=0.5, cost_usd=Decimal("0.1"))
        return PAYLOAD, call

    monkeypatch.setattr(llm, "extract_measured", stubbed)

    named = runner.invoke(app, ["eval", "--extractor", "llm", "--save", "--name", "llm-after-change"])
    refused = runner.invoke(app, ["eval", "--extractor", "llm", "--save", "--name", "../elsewhere"])

    assert named.exit_code in (0, 1), named.output
    results = tmp_path / "evals" / "results"
    assert (results / "llm-after-change.json").is_file()
    assert (results / "llm-after-change.claims.json").is_file()
    assert not (results / f"llm-{llm.model_name()}-high.json").exists()
    assert refused.exit_code == 2
    assert "--name takes" in refused.output


def test_an_unknown_effort_is_refused_before_anything_runs(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["eval", "--extractor", "llm", "--effort", "extreme"])

    assert result.exit_code == 2
    assert "--effort must be one of" in result.output


def test_the_estimate_needs_no_client_and_its_ceiling_is_max_tokens(monkeypatch):
    def no_client(*args, **kwargs):
        raise AssertionError("the estimate must not construct an API client")

    monkeypatch.setattr(anthropic, "Anthropic", no_client)

    estimate = estimate_run(ROOT / "corpus", "claude-opus-5-5", ROOT / "evals" / "results" / "rules.claims.json")

    assert estimate.contracts == 12
    assert estimate.output_ceiling_tokens == 12 * llm.MAX_TOKENS
    assert 0 < estimate.output_floor_tokens < estimate.output_ceiling_tokens
    assert estimate.cost_floor_usd < estimate.cost_ceiling_usd
    assert estimate.cost_ceiling_usd == (estimate.input_tokens * 4 + estimate.output_ceiling_tokens * 20) / Decimal(
        1_000_000
    )


def test_the_estimate_command_prints_bounds_for_a_set():
    result = CliRunner().invoke(app, ["estimate", "--set", "test", "--model", "claude-opus-5"])

    assert result.exit_code == 0, result.output
    assert result.output.startswith("Estimate for claude-opus-5 on the test set (7 contracts), without calling the API")
    assert f"at the prices of {PRICES_AS_OF}" in result.output


def test_a_model_without_a_published_price_is_not_estimated():
    result = CliRunner().invoke(app, ["estimate", "--model", "claude-unknown"])

    assert result.exit_code == 1
    assert "no published price" in result.output
