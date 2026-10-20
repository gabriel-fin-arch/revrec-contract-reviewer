"""The held-out test set: generated like the corpus, kept apart from it.

Nothing here runs an extractor on the held-out contracts. These tests check
that the set is what was committed, that it is separate from the development
set, and that the code it is meant to measure doesn't know it exists.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from typer.testing import CliRunner

from revrec_contract_reviewer.cli import app
from revrec_contract_reviewer.corpus import CORPUS, HELD_OUT, CorpusSet, generate_corpus
from revrec_contract_reviewer.evaluate import build_gold

ROOT = Path(__file__).resolve().parent.parent
COMMITTED = ROOT / "corpus" / "test"
EXTRACTORS = ROOT / "src" / "revrec_contract_reviewer" / "extract"


def test_rebuilding_the_test_set_matches_the_repository(tmp_path: Path):
    written = generate_corpus(tmp_path, CorpusSet.TEST)

    assert len(written) == len(HELD_OUT) == 7
    for path in [*written, tmp_path / "README.md"]:
        assert path.read_bytes() == (COMMITTED / path.name).read_bytes(), path.name


def test_the_committed_test_gold_is_what_the_specs_say():
    committed = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in (ROOT / "evals" / "gold" / "test").glob("*.json")
    }

    assert committed == {record.doc_id: record.model_dump() for record in build_gold(CorpusSet.TEST)}


def test_the_two_sets_share_no_contract_and_no_customer():
    assert not {spec.doc_id for spec in CORPUS} & {spec.doc_id for spec in HELD_OUT}
    assert not {spec.customer for spec in CORPUS} & {spec.customer for spec in HELD_OUT}


def test_the_extractors_and_the_prompt_never_mention_a_held_out_contract():
    """A held-out contract the rules or the prompt had been written around
    would measure nothing. The prompt lives in extract/llm.py."""
    source = "\n".join(path.read_text(encoding="utf-8") for path in sorted(EXTRACTORS.glob("*.py"))).lower()

    for spec in HELD_OUT:
        name = spec.customer.split()[0].lower()
        assert spec.doc_id not in source
        # Whole words: "alder" is inside "calderwood", a development contract.
        assert not re.search(rf"\b{re.escape(name)}\b", source), f"{name} appears in the extractor code"


def test_every_held_out_contract_says_what_it_is_for():
    for spec in HELD_OUT:
        assert len(spec.commentary) > 80, spec.doc_id


def test_the_cli_keeps_the_test_set_in_its_own_folders(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    assert runner.invoke(app, ["generate-corpus", "--set", "test"]).exit_code == 0
    assert runner.invoke(app, ["build-gold", "--set", "test"]).exit_code == 0

    assert sorted(p.stem for p in (tmp_path / "corpus" / "test").glob("*.pdf")) == sorted(
        spec.doc_id for spec in HELD_OUT
    )
    assert len(list((tmp_path / "evals" / "gold" / "test").glob("*.json"))) == 7
    assert not list((tmp_path / "corpus").glob("*.pdf")), "the development folder stays empty"
