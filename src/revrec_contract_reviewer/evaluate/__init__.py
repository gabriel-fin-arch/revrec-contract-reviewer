"""The eval harness: run the pipeline over the corpus and score it against gold."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import anthropic

from revrec_contract_reviewer.assess import assess
from revrec_contract_reviewer.evaluate.gold import GoldRecord, build_gold, load_gold, write_gold
from revrec_contract_reviewer.evaluate.runs import (
    CorpusChanged,
    SavedContract,
    SavedRun,
    claims_path,
    pdf_sha256,
    rescore,
)
from revrec_contract_reviewer.evaluate.score import (
    ContractScore,
    EvalReport,
    Tally,
    aggregate,
    score_contract,
)
from revrec_contract_reviewer.extract import ExtractorChoice, extract_with_claims
from revrec_contract_reviewer.ingest import load_contract
from revrec_contract_reviewer.segment import segmented

__all__ = [
    "ContractScore",
    "CorpusChanged",
    "EvalReport",
    "GoldRecord",
    "SavedContract",
    "SavedRun",
    "Tally",
    "aggregate",
    "build_gold",
    "claims_path",
    "evaluate",
    "load_gold",
    "markdown_table",
    "rescore",
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
    """Review every contract in the gold set and score the result. See evaluate()."""
    return evaluate(corpus_dir, gold_dir, choice, client=client)[0]


def evaluate(
    corpus_dir: Path,
    gold_dir: Path,
    choice: ExtractorChoice = ExtractorChoice.AUTO,
    client: anthropic.Anthropic | None = None,
    effort: str | None = None,
) -> tuple[EvalReport, SavedRun]:
    """Review every contract in the gold set, score it, and keep the run.

    Driven by the gold set rather than by the corpus directory: a PDF with no
    gold record is not silently skipped in a way that flatters the numbers, and
    a gold record with no PDF is an error rather than a quietly missing row.
    The SavedRun has every claim and its grounding, for `rescore`.
    """
    gold = load_gold(gold_dir)
    scores: list[ContractScore] = []
    saved: list[SavedContract] = []
    extractor = "rules"
    model: str | None = None
    run_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    for doc_id, record in sorted(gold.items()):
        path = corpus_dir / f"{doc_id}.pdf"
        if not path.exists():
            raise FileNotFoundError(f"gold record {doc_id} has no contract at {path}")

        document = segmented(load_contract(path))
        claims, extraction, call = extract_with_claims(document, choice, client=client, effort=effort)
        extractor = extraction.extractor
        model = extraction.model or model
        scores.append(score_contract(assess(extraction), document, record))
        saved.append(
            SavedContract(doc_id=doc_id, pdf_sha256=pdf_sha256(path), claims=claims, extraction=extraction, call=call)
        )

    efforts = {contract.call.effort for contract in saved if contract.call is not None}
    return aggregate(scores, extractor=extractor, model=model), SavedRun(
        extractor=extractor,
        model=model,
        run_at=run_at,
        effort=efforts.pop() if len(efforts) == 1 else None,
        contracts=saved,
    )


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
    # Silence is not in the table. Every field the contract leaves unstated is
    # either left blank or invented -- there is no third outcome to count as a
    # miss -- so a recall for it is 1.00 by construction and a precision is
    # just the blank rate under another name. It gets a count of its own.
    for label, tally in (
        ("Contract fields", report.fields),
        ("Performance obligations", report.obligations),
        ("Judgment flags", report.judgments),
    ):
        lines.append(
            f"| {label} | {tally.precision:.2f} | {tally.recall:.2f} | {tally.f1:.2f} |"
        )
    lines.extend(
        [
            "",
            f"Unstated fields left blank: **{report.silence.true_positives}/"
            f"{report.silence.true_positives + report.silence.false_positives}**. "
            f"Citations re-resolved against the source: **{report.citations_resolved}/{report.citations_total}** "
            f"({report.citation_rate:.0%}). "
            f"Claims dropped for no evidence: **{report.dropped_for_no_evidence}**.",
        ]
    )
    return "\n".join(lines)
