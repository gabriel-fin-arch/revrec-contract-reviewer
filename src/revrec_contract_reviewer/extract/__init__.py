"""Extraction: claims in, grounded facts out.

The choice between the two extractors is made here and nowhere else, so the rest
of the pipeline never has to know which one ran.
"""

from __future__ import annotations

from enum import StrEnum

import anthropic

from revrec_contract_reviewer.extract import llm, rules
from revrec_contract_reviewer.extract.assemble import assemble
from revrec_contract_reviewer.extract.grounding import Grounder
from revrec_contract_reviewer.models.document import ContractDocument
from revrec_contract_reviewer.models.extraction import ContractExtraction

__all__ = ["ExtractorChoice", "Grounder", "assemble", "extract_contract", "llm", "rules"]


class ExtractorChoice(StrEnum):
    AUTO = "auto"
    LLM = "llm"
    RULES = "rules"


def extract_contract(
    document: ContractDocument,
    choice: ExtractorChoice = ExtractorChoice.AUTO,
    client: anthropic.Anthropic | None = None,
) -> ContractExtraction:
    """Extract `document`, picking an extractor according to `choice`.

    AUTO uses the model when an API key is available and the rules otherwise,
    which is what makes a fresh clone runnable. LLM is explicit and raises
    rather than falling back -- when someone asks for the model path, silently
    giving them regular expressions and a review that looks fine is the worst
    possible outcome. That exact failure is why this argument exists.
    """
    if choice is ExtractorChoice.RULES or (choice is ExtractorChoice.AUTO and not llm.available()):
        return assemble(document, rules.extract(document), extractor="rules")

    if choice is ExtractorChoice.LLM and not llm.available():
        raise RuntimeError(
            "The model extractor was requested but ANTHROPIC_API_KEY is not set. "
            "Set it, or pass --extractor rules to run offline."
        )

    try:
        wire, model = llm.extract(document, client=client)
    except anthropic.APIError:
        if choice is ExtractorChoice.LLM:
            raise
        # AUTO asked for the best extractor available, and right now the API
        # isn't it. Falling back keeps the run going, and `extractor` on the
        # result records which one actually produced it -- so a memo built this
        # way says "rules" on its face and nobody has to guess afterwards.
        return assemble(document, rules.extract(document), extractor="rules")

    return assemble(document, wire, extractor="llm", model=model)
