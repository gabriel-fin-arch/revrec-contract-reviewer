"""docs/controls.md names code, tests and output files; this keeps it honest.

A controls matrix that drifts from the code is worse than none: it reads as
assurance. Each row has to name things that exist, prove itself with at
least one test, and point at evidence a run actually writes.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from revrec_contract_reviewer.cli import app

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "src" / "revrec_contract_reviewer"
DOC = ROOT / "docs" / "controls.md"

REFERENCE = re.compile(r"`([\w./]+\.py)(?:::(\w+))?`")
EVIDENCE = re.compile(r"`([\w<>/.-]+\.(?:html|pdf|json|xlsx))`")


def _rows() -> list[list[str]]:
    rows = []
    for line in DOC.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells[0].isdigit():
            rows.append(cells)
    return rows


def _resolve(path: str) -> Path:
    for base in (ROOT, PACKAGE):
        if (base / path).is_file():
            return base / path
    raise AssertionError(f"docs/controls.md names {path}, which doesn't exist")


def test_the_matrix_has_rows():
    assert len(_rows()) >= 10


@pytest.mark.parametrize(
    ("path", "name"), REFERENCE.findall(DOC.read_text(encoding="utf-8")), ids=lambda value: value or ""
)
def test_every_file_and_name_it_cites_exists(path: str, name: str):
    source = _resolve(path).read_text(encoding="utf-8")
    if name:
        assert re.search(rf"^\s*(?:def|class)\s+{name}\b|^{name}\s*[:=]", source, re.MULTILINE), (
            f"docs/controls.md cites {path}::{name}, which isn't defined there"
        )


def test_every_control_is_proved_by_a_named_test():
    for number, _objective, _enforced, proved_by, _evidence in _rows():
        tests = [path for path, name in REFERENCE.findall(proved_by) if path.startswith("tests/") and name]
        assert tests, f"control {number} names no test"


def test_every_evidence_file_it_cites_is_one_a_run_writes(tmp_path: Path, monkeypatch):
    """Run the review the way the README does, and read off what it wrote."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    runner = CliRunner()
    assert runner.invoke(app, ["generate-corpus"]).exit_code == 0
    assert runner.invoke(app, ["review", "--extractor", "rules"]).exit_code == 0
    contracts = {path.stem for path in (tmp_path / "corpus").glob("*.pdf")}

    written = set()
    for path in (tmp_path / "out").iterdir():
        written.add(f"<contract>{path.suffix}" if path.stem in contracts else path.name)
    written.add("evals/results/rules.json")  # what `eval --save` writes; it's committed
    written.add("conclusions.json")  # what `conclusions` writes beside the memos, once a reviewer fills the worklist
    cited = {name for row in _rows() for name in EVIDENCE.findall(row[4])}

    assert cited
    assert cited <= written, f"not written by a run: {sorted(cited - written)}"
    assert (ROOT / "evals" / "results" / "rules.json").is_file()
