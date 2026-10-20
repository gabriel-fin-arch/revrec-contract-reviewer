"""The eval harness: run the pipeline over the corpus and score it against gold."""

from __future__ import annotations

from collections.abc import Callable
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
    partial_path,
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
from revrec_contract_reviewer.extract import ExtractorChoice, extract_with_claims, llm
from revrec_contract_reviewer.extract.metering import CallRecord
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
    "partial_path",
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
    checkpoint: Callable[[SavedRun], None] | None = None,
) -> tuple[EvalReport, SavedRun]:
    """Review every contract in the gold set, score it, and keep the run.

    Driven by the gold set rather than by the corpus directory: a PDF with no
    gold record is not silently skipped in a way that flatters the numbers, and
    a gold record with no PDF is an error rather than a quietly missing row.
    The SavedRun has every claim and its grounding, for `rescore`.

    `checkpoint` gets the run so far after every contract, and once more if an
    extraction raises, with `stopped` set, before the error goes on. A model
    run that stops half-way has already paid for the calls before it, and this
    is how they're kept.
    """
    gold = load_gold(gold_dir)
    scores: list[ContractScore] = []
    saved: list[SavedContract] = []
    extractor = "rules"
    model: str | None = None
    run_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    def so_far(stopped: str | None = None, unfinished: list[CallRecord] | None = None) -> SavedRun:
        calls = [contract.call for contract in saved if contract.call is not None] + (unfinished or [])
        efforts = {call.effort for call in calls}
        return SavedRun(
            extractor=extractor if saved or not calls else "llm",
            model=model or (calls[0].model if calls else None),
            run_at=run_at,
            effort=efforts.pop() if len(efforts) == 1 else None,
            contracts=list(saved),
            stopped=stopped,
            unfinished_calls=unfinished or [],
        )

    for doc_id, record in sorted(gold.items()):
        path = corpus_dir / f"{doc_id}.pdf"
        if not path.exists():
            raise FileNotFoundError(f"gold record {doc_id} has no contract at {path}")

        document = segmented(load_contract(path))
        try:
            claims, extraction, call = extract_with_claims(document, choice, client=client, effort=effort)
        except Exception as exc:
            if checkpoint is not None:
                billed = [exc.call] if isinstance(exc, llm.ModelDeclined) and exc.call is not None else []
                checkpoint(so_far(f"{doc_id}: {type(exc).__name__}: {exc}", billed))
            raise
        extractor = extraction.extractor
        model = extraction.model or model
        scores.append(score_contract(assess(extraction), document, record))
        saved.append(
            SavedContract(doc_id=doc_id, pdf_sha256=pdf_sha256(path), claims=claims, extraction=extraction, call=call)
        )
        if checkpoint is not None:
            checkpoint(so_far())

    return aggregate(scores, extractor=extractor, model=model), so_far()


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
