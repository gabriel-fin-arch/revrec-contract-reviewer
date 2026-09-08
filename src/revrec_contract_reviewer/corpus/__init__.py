"""Synthetic contract corpus -- specs, renderer, and the index that documents it."""

from __future__ import annotations

from pathlib import Path

from revrec_contract_reviewer.corpus.library import CORPUS, spec_by_id
from revrec_contract_reviewer.corpus.render import render_contract
from revrec_contract_reviewer.corpus.spec import ContractSpec

__all__ = ["CORPUS", "ContractSpec", "generate_corpus", "render_contract", "spec_by_id"]

_INDEX_HEADER = """# The corpus

Twelve synthetic contracts. Every party, product, price and person here is
invented; nothing in this directory comes from any real agreement.

They are generated, not stored: `revrec generate-corpus` rebuilds every PDF from
`src/revrec_contract_reviewer/corpus/library.py`, and the output is
byte-reproducible so a rebuild never shows up as a diff.

The documents are compressed. A real master subscription agreement runs forty
pages, most of which is indemnity, data protection and export control language
that has no bearing on revenue. What is kept here is the part a revenue reviewer
reads: term, termination, fees, what was promised, and how it gets paid for.

The supplier changes from document to document -- a US parent, its UK and German
subsidiaries, and the group's clinical services arm in Spain. That is the point
of a group-level review. Each local team reaches its own conclusion on its own
paper, and the differences only become visible when someone reads all twelve
next to each other.

| Contract | Type | Currency | Judgments it should raise |
|---|---|---|---|
"""


def _index_rows() -> str:
    rows = []
    for spec in CORPUS:
        judgments = ", ".join(sorted(j.value for j in spec.truth.judgments)) or "_none_"
        rows.append(
            f"| `{spec.doc_id}` | {spec.truth.agreement_type.value} | {spec.truth.currency} | {judgments} |"
        )
    return "\n".join(rows)


def _index_commentary() -> str:
    blocks = []
    for spec in CORPUS:
        blocks.append(f"### `{spec.doc_id}`\n\n{spec.commentary}\n")
    return "\n".join(blocks)


def write_index(out_dir: Path) -> Path:
    """Write corpus/README.md -- the table plus the note on why each document exists.

    Generated rather than hand-written because the commentary lives next to the
    contract it describes in library.py, and a hand-kept copy of it in markdown
    would be wrong within two edits.
    """
    target = out_dir / "README.md"
    body = (
        _INDEX_HEADER
        + _index_rows()
        + "\n\n## What each one is for\n\n"
        + _index_commentary()
    )
    target.write_text(body, encoding="utf-8")
    return target


def generate_corpus(out_dir: Path) -> list[Path]:
    """Render every contract to `out_dir` and refresh the index."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = [render_contract(spec, out_dir) for spec in CORPUS]
    write_index(out_dir)
    return written
