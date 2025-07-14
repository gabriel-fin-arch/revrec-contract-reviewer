"""The pipeline, in one place.

Five stages, four of them deterministic:

    load -> segment -> extract -> assess

`extract` is the only stage that may call a model, and everything it returns has
already been through grounding by the time it leaves. So the interesting
property of this module is how boring it is -- there is no branch anywhere below
that depends on which extractor ran.
"""

from __future__ import annotations

from pathlib import Path

import anthropic

from revrec_contract_reviewer.assess import assess
from revrec_contract_reviewer.extract import ExtractorChoice, extract_contract
from revrec_contract_reviewer.ingest import load_contract
from revrec_contract_reviewer.models.review import ContractReview
from revrec_contract_reviewer.segment import segmented


def review_contract(
    path: Path,
    choice: ExtractorChoice = ExtractorChoice.AUTO,
    client: anthropic.Anthropic | None = None,
) -> ContractReview:
    """Review one contract PDF."""
    document = segmented(load_contract(path))
    extraction = extract_contract(document, choice, client=client)
    return assess(extraction)


def review_directory(
    corpus_dir: Path,
    choice: ExtractorChoice = ExtractorChoice.AUTO,
    client: anthropic.Anthropic | None = None,
) -> list[ContractReview]:
    """Review every PDF in `corpus_dir`, in filename order.

    Filename order rather than whatever the filesystem hands back, so two runs
    on the same directory produce the same worklist in the same sequence.
    """
    paths = sorted(corpus_dir.glob("*.pdf"))
    if not paths:
        raise FileNotFoundError(f"no PDFs in {corpus_dir}")
    return [review_contract(path, choice, client=client) for path in paths]
