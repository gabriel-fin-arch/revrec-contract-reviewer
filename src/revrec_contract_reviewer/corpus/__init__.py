"""Synthetic contract corpus -- specs, renderer, and the index that documents it.

Two sets. The development set is the twelve contracts in library.py, which
the rules and the prompt were written against. The test set is the seven in
heldout.py, written afterwards the same way and held out: results on it are
reported and never used to tune anything.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from revrec_contract_reviewer.corpus.heldout import HELD_OUT
from revrec_contract_reviewer.corpus.library import CORPUS, spec_by_id
from revrec_contract_reviewer.corpus.render import render_contract
from revrec_contract_reviewer.corpus.spec import ContractSpec
from revrec_contract_reviewer.fileio import write_lf

__all__ = [
    "CORPUS",
    "HELD_OUT",
    "ContractSpec",
    "CorpusSet",
    "generate_corpus",
    "render_contract",
    "spec_by_id",
    "specs_for",
]


class CorpusSet(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"


def specs_for(corpus_set: CorpusSet) -> list[ContractSpec]:
    return CORPUS if corpus_set is CorpusSet.DEVELOPMENT else HELD_OUT


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

_HELD_OUT_HEADER = """# The held-out test set

Seven synthetic contracts, made the same way as the twelve in `corpus/` and
just as invented: nothing here comes from any real agreement.

They were written on 18 October 2026, after the rules extractor and the
prompt, and committed with their gold records before either extractor had been
run on them. `revrec generate-corpus --set test` rebuilds them from
`src/revrec_contract_reviewer/corpus/heldout.py`, byte for byte.

Results on this set are reported separately and are not used: nothing seen
here goes back into the rules, the prompt or the scorer. A fix for something
this set shows is made against the development set, and this set measures it
again afterwards.

| Contract | Type | Currency | Judgments it should raise |
|---|---|---|---|
"""


def _index_rows(specs: list[ContractSpec]) -> str:
    rows = []
    for spec in specs:
        judgments = ", ".join(sorted(j.value for j in spec.truth.judgments)) or "_none_"
        rows.append(
            f"| `{spec.doc_id}` | {spec.truth.agreement_type.value} | {spec.truth.currency} | {judgments} |"
        )
    return "\n".join(rows)


def _index_commentary(specs: list[ContractSpec]) -> str:
    blocks = []
    for spec in specs:
        blocks.append(f"### `{spec.doc_id}`\n\n{spec.commentary}\n")
    return "\n".join(blocks)


def write_index(out_dir: Path, corpus_set: CorpusSet = CorpusSet.DEVELOPMENT) -> Path:
    """Write the set's README.md -- the table plus the note on why each document exists.

    Generated rather than hand-written because the commentary lives next to the
    contract it describes in library.py, and a hand-kept copy of it in markdown
    would be wrong within two edits.
    """
    specs = specs_for(corpus_set)
    header = _INDEX_HEADER if corpus_set is CorpusSet.DEVELOPMENT else _HELD_OUT_HEADER
    body = header + _index_rows(specs) + "\n\n## What each one is for\n\n" + _index_commentary(specs)
    return write_lf(out_dir / "README.md", body)


def generate_corpus(out_dir: Path, corpus_set: CorpusSet = CorpusSet.DEVELOPMENT) -> list[Path]:
    """Render every contract in the set to `out_dir` and refresh its index."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = [render_contract(spec, out_dir) for spec in specs_for(corpus_set)]
    write_index(out_dir, corpus_set)
    return written
