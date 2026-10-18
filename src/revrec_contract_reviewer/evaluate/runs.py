"""Saved runs: every claim an extractor made, and what grounding did with it.

A saved report holds counts. That's enough to publish a number and not
enough to stand behind one: when the scorer changes, a report can't be
scored again, and a model run can't be repeated for free. So next to each
report, `eval --save` writes the run itself. For every contract, the PDF's
SHA-256, the claims exactly as the extractor returned them (values and
quotes, before grounding), and the extraction grounding made of them: what
was kept, with its citations, and how many were dropped.

`rescore()` scores a saved run again from that file, with the corpus and the
gold set but without extracting anything, and refuses if a PDF has changed
since the run, since then the saved citations no longer point at the same
document.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from pydantic import BaseModel

from revrec_contract_reviewer.assess import assess
from revrec_contract_reviewer.evaluate.gold import load_gold
from revrec_contract_reviewer.evaluate.score import EvalReport, aggregate, score_contract
from revrec_contract_reviewer.extract.schema import WireExtraction
from revrec_contract_reviewer.ingest import load_contract
from revrec_contract_reviewer.models.extraction import ContractExtraction
from revrec_contract_reviewer.segment import segmented


class SavedContract(BaseModel):
    doc_id: str
    pdf_sha256: str
    claims: WireExtraction
    extraction: ContractExtraction


class SavedRun(BaseModel):
    extractor: str
    model: str | None = None
    contracts: list[SavedContract] = []


class CorpusChanged(ValueError):
    """A contract's PDF is not the one the saved run read."""


def pdf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def claims_path(report_path: Path) -> Path:
    """Where a report's run is saved: rules.json next to rules.claims.json."""
    return report_path.with_name(f"{report_path.stem}.claims.json")


def rescore(run: SavedRun, corpus_dir: Path, gold_dir: Path) -> EvalReport:
    """Score a saved run against the gold set again, without extracting.

    The review is rebuilt from the saved extraction, so a change to the
    checks, the judgments or the scorer is applied to the old run; the
    citations are re-resolved against the corpus, which has to be the corpus
    the run read.
    """
    gold = load_gold(gold_dir)
    saved = {contract.doc_id: contract for contract in run.contracts}
    missing = sorted(set(gold) - set(saved))
    if missing:
        raise ValueError(f"the saved run has no claims for {', '.join(missing)}")

    scores = []
    for doc_id, record in sorted(gold.items()):
        contract = saved[doc_id]
        path = corpus_dir / f"{doc_id}.pdf"
        if not path.exists():
            raise FileNotFoundError(f"gold record {doc_id} has no contract at {path}")
        if pdf_sha256(path) != contract.pdf_sha256:
            raise CorpusChanged(f"{path} is not the PDF this run read (its SHA-256 has changed)")
        document = segmented(load_contract(path))
        scores.append(score_contract(assess(contract.extraction), document, record))

    return aggregate(scores, extractor=run.extractor, model=run.model)
