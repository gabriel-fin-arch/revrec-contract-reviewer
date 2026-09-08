"""The model path.

Exercised with a stub client rather than left untested because there is no API
key in CI. The stub covers everything on this side of the network boundary: that
the model is handed the same text grounding will search, that its output is
grounded like anything else, and that a fabricated quote from a model is dropped
exactly as one from a rule would be.

What it deliberately does not do is assert anything about extraction quality.
That is measured, not asserted, and it is measured by the eval harness against a
real run.
"""

from __future__ import annotations

import anthropic
import pytest

from revrec_contract_reviewer.extract import ExtractorChoice, extract_contract, llm
from revrec_contract_reviewer.extract.schema import Claim, WireExtraction, WireObligation
from revrec_contract_reviewer.models.document import ContractDocument
from revrec_contract_reviewer.models.extraction import ObligationKind
from revrec_contract_reviewer.models.fields import FieldStatus


class StubMessages:
    def __init__(self, payload: WireExtraction, recorder: dict) -> None:
        self._payload = payload
        self._recorder = recorder

    def parse(self, **kwargs):
        self._recorder.update(kwargs)
        return type("Response", (), {"parsed_output": self._payload})()


class StubClient:
    def __init__(self, payload: WireExtraction) -> None:
        self.calls: dict = {}
        self.messages = StubMessages(payload, self.calls)


@pytest.fixture
def payload() -> WireExtraction:
    return WireExtraction(
        currency=Claim(value="GBP", quotes=["All amounts are stated in Pounds Sterling"]),
        stated_term_months=Claim(value="24", quotes=["for a term of twenty-four (24) months"]),
        total_fixed_consideration=Claim(value="312000", quotes=["Total committed fees GBP 312,000"]),
        obligations=[
            WireObligation(
                label="Telemetry Platform subscription",
                kind=ObligationKind.SAAS_SUBSCRIPTION,
                quotes=["Telemetry Platform subscription (24 months) GBP 288,000"],
                stated_price=Claim(value="288000", quotes=["Telemetry Platform subscription (24 months) GBP 288,000"]),
            )
        ],
    )


def test_the_model_is_sent_the_text_grounding_will_search(helix: ContractDocument, payload: WireExtraction):
    """Sending the PDF instead would have the model quoting a different rendering
    of the same pages, and every faithful quote would fail to ground."""
    client = StubClient(payload)

    llm.extract(helix, client=client)

    sent = client.calls["messages"][0]["content"]
    for page in helix.pages:
        assert page.text in sent
    assert "[page 2]" in sent


def test_the_request_asks_for_the_wire_schema(helix: ContractDocument, payload: WireExtraction):
    client = StubClient(payload)

    llm.extract(helix, client=client)

    assert client.calls["output_format"] is WireExtraction
    assert client.calls["model"] == llm.model_name()


def test_model_output_is_grounded_like_anything_else(helix: ContractDocument, payload: WireExtraction):
    wire, model = llm.extract(helix, client=StubClient(payload))
    from revrec_contract_reviewer.extract import assemble

    extraction = assemble(helix, wire, extractor="llm", model=model)

    assert extraction.currency.value == "GBP"
    citation = extraction.currency.citations[0]
    assert helix.text[citation.start : citation.end] == citation.quote
    assert citation.page == helix.page_for_offset(citation.start)
    assert str(extraction.obligations[0].stated_price.value) == "288000"
    assert extraction.dropped_for_no_evidence == 0


def test_a_fabricated_quote_from_the_model_is_dropped(helix: ContractDocument):
    """The single most important behaviour in the project."""
    from revrec_contract_reviewer.extract import assemble

    invented = WireExtraction(
        net_days=Claim(value="90", quotes=["invoices are payable within ninety (90) days of the invoice date"]),
    )

    extraction = assemble(helix, invented, extractor="llm", model="stub")

    assert extraction.payment.net_days.status is FieldStatus.ABSENT
    assert extraction.dropped_for_no_evidence == 1


def test_an_obligation_nobody_can_point_at_is_not_built(helix: ContractDocument):
    from revrec_contract_reviewer.extract import assemble

    invented = WireExtraction(
        obligations=[
            WireObligation(
                label="Onboarding workshop",
                kind=ObligationKind.TRAINING,
                quotes=["Nimbus will deliver a two day onboarding workshop"],
            )
        ]
    )

    extraction = assemble(helix, invented, extractor="llm", model="stub")

    assert extraction.obligations == []
    assert extraction.dropped_for_no_evidence == 1


def test_asking_for_the_model_without_a_key_fails_loudly(helix: ContractDocument, monkeypatch):
    """Silently handing back regular expressions, in a review that looks fine, is
    the worst available outcome."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        extract_contract(helix, ExtractorChoice.LLM)


def test_auto_falls_back_to_rules_when_the_api_fails(helix: ContractDocument, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")

    def explode(document, client=None):
        raise anthropic.APIConnectionError(request=None)

    monkeypatch.setattr(llm, "extract", explode)

    extraction = extract_contract(helix, ExtractorChoice.AUTO)

    assert extraction.extractor == "rules"
    assert extraction.model is None


def test_auto_without_a_key_uses_rules(helix: ContractDocument, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    assert extract_contract(helix, ExtractorChoice.AUTO).extractor == "rules"
