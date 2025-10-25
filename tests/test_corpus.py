"""The corpus generator.

The reproducibility tests are here because the gold set is keyed by page number
and the eval compares against committed PDFs. A generator whose output drifts
turns every environment difference into what looks like an extraction
regression.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from revrec_contract_reviewer.corpus import CORPUS, generate_corpus, spec_by_id


def test_rebuilding_the_corpus_produces_identical_bytes(tmp_path: Path):
    first = {p.name: p.read_bytes() for p in generate_corpus(tmp_path / "a")}
    second = {p.name: p.read_bytes() for p in generate_corpus(tmp_path / "b")}

    assert first.keys() == second.keys()
    for name in first:
        assert first[name] == second[name], name


def test_page_streams_are_not_compressed(tmp_path: Path):
    """zlib makes no promise of identical output across versions -- Python 3.11
    and 3.14 deflate the same page to different lengths. Uncompressed streams
    cost a few kilobytes and make the corpus reproducible off this machine."""
    for path in generate_corpus(tmp_path):
        if path.suffix == ".pdf":
            assert b"/FlateDecode" not in path.read_bytes(), path.name


def test_the_embedded_creation_date_is_frozen_not_todays(tmp_path: Path):
    """reportlab stamps the wall clock unless `invariant` is set, at which point
    it writes a fixed sentinel instead. Asserting the sentinel is there says
    more than asserting a date is absent -- the date is always present."""
    generate_corpus(tmp_path)
    body = (tmp_path / "nimbus-of-helix.pdf").read_bytes()

    stamped = re.search(rb"/CreationDate \(D:(\d{8})", body)
    assert stamped, "no creation date at all -- reportlab changed its output format"
    assert stamped.group(1) == b"20000101"
    assert date.today().strftime("%Y%m%d").encode() not in body


def test_every_contract_declares_what_it_is_for(tmp_path: Path):
    """The index is generated from the specs, so a contract with no commentary
    silently becomes a blank section in corpus/README.md."""
    for spec in CORPUS:
        assert spec.commentary.strip(), spec.doc_id

    index = (generate_corpus(tmp_path).pop().parent / "README.md").read_text(encoding="utf-8")
    for spec in CORPUS:
        assert spec.doc_id in index


def test_spec_lookup_rejects_an_unknown_id():
    assert spec_by_id("nimbus-of-helix").truth.currency == "GBP"
    try:
        spec_by_id("no-such-contract")
    except KeyError as error:
        assert "no-such-contract" in str(error)
    else:
        raise AssertionError("expected a KeyError")
