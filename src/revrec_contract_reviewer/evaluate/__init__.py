"""The eval harness: run the pipeline over the corpus and score it against gold."""

from __future__ import annotations

from pathlib import Path

import anthropic

from revrec_contract_reviewer.assess import assess
from revrec_contract_reviewer.evaluate.gold import GoldRecord, build_gold, load_gold, write_gold
from revrec_contract_reviewer.evaluate.score import (
    ContractScore,
    EvalReport,
    Tally,
    aggregate,
    score_contract,
)
from revrec_contract_reviewer.extract import ExtractorChoice, extract_contract
from revrec_contract_reviewer.ingest import load_contract
from revrec_contract_reviewer.segment import segmented

__all__ = [
    "ContractScore",
    "EvalReport",
    "GoldRecord",
    "Tally",
    "aggregate",
    "build_gold",
    "load_gold",
    "markdown_table",
    "run_eval",
    "score_contract",
    "write_gold",
]


def run_eval(
    corpus_dir: Path,
    gold_dir: Path,
    choice: ExtractorChoice = ExtractorChoice.AUTO,
    client: anthropic.Anthropic | None = None,
) -> EvalReport:
    """Review every contract in the gold set and score the result.

    Driven by the gold set rather than by the corpus directory: a PDF with no
    gold record is not silently skipped in a way that flatters the numbers, and
    a gold record with no PDF is an error rather than a quietly missing row.
    """
    gold = load_gold(gold_dir)
    scores: list[ContractScore] = []
    extractor = "rules"
    model: str | None = None

    for doc_id, record in sorted(gold.items()):
        path = corpus_dir / f"{doc_id}.pdf"
        if not path.exists():
            raise FileNotFoundError(f"gold record {doc_id} has no contract at {path}")

        document = segmented(load_contract(path))
        extraction = extract_contract(document, choice, client=client)
        extractor = extraction.extractor
        model = extraction.model or model
        scores.append(score_contract(assess(extraction), document, record))

    return aggregate(scores, extractor=extractor, model=model)


def markdown_table(report: EvalReport) -> str:
    """The results as a markdown table, for pasting into the docs."""
    lines = [
        f"Extractor: **{report.extractor}**"
        + (f" ({report.model})" if report.model else "")
        + f" | contracts: {len(report.per_contract)}",
        "",
        "| Measure | Precision | Recall | F1 |",
        "|---|---|---|---|",
    ]
    for label, tally in (
        ("Contract fields", report.fields),
        ("Silence on unstated fields", report.silence),
        ("Performance obligations", report.obligations),
        ("Judgment flags", report.judgments),
    ):
        lines.append(
            f"| {label} | {tally.precision:.2f} | {tally.recall:.2f} | {tally.f1:.2f} |"
        )
    lines.extend(
        [
            "",
            f"Citations re-resolved against the source: **{report.citations_resolved}/{report.citations_total}** "
            f"({report.citation_rate:.0%}). "
            f"Claims dropped for no evidence: **{report.dropped_for_no_evidence}**.",
        ]
    )
    return "\n".join(lines)
