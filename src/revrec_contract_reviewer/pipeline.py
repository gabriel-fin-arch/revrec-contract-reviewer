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
from typing import NamedTuple

import anthropic

from revrec_contract_reviewer.assess import assess
from revrec_contract_reviewer.extract import ExtractorChoice, extract_contract
from revrec_contract_reviewer.ingest import UnreadableContract, load_contract
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


class Unreadable(NamedTuple):
    """A file in the folder that could not be reviewed, and why."""

    name: str
    reason: str


def review_directory(
    corpus_dir: Path,
    choice: ExtractorChoice = ExtractorChoice.AUTO,
    client: anthropic.Anthropic | None = None,
) -> tuple[list[ContractReview], list[Unreadable]]:
    """Review every PDF in `corpus_dir`, in filename order.

    Filename order rather than whatever the filesystem hands back, so two runs
    on the same directory produce the same worklist in the same sequence.

    A file that can't be read is set aside and returned with the reason, not
    raised. One scanned contract in a folder of forty used to stop the run
    before a single memo was written, which is the wrong trade for a tool whose
    job is triage: the other thirty-nine are still worth reviewing, and the
    scanned one is still worth listing, at the top.
    """
    paths = sorted(corpus_dir.glob("*.pdf"))
    if not paths:
        raise FileNotFoundError(f"no PDFs in {corpus_dir}")

    reviews: list[ContractReview] = []
    unreadable: list[Unreadable] = []
    for path in paths:
        try:
            reviews.append(review_contract(path, choice, client=client))
        except UnreadableContract as exc:
            unreadable.append(Unreadable(path.name, str(exc)))
    return reviews, unreadable
