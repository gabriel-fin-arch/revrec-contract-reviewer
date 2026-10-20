"""The commands, end to end.

A clone-and-run check as much as a unit test: the README's quickstart is these
four commands in this order, and it has to work from an empty directory.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from revrec_contract_reviewer.cli import app
from revrec_contract_reviewer.pipeline import review_contract, review_directory

runner = CliRunner()


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return tmp_path


def test_every_command_prints_its_help():
    """typer below 0.16 renders help through a click API that changed in 8.2, and
    `revrec review --help` died with a traceback while the rest of this file
    passed -- nothing else here asks a subcommand for help."""
    for command in ([], ["generate-corpus"], ["review"], ["build-gold"], ["eval"]):
        result = CliRunner().invoke(app, [*command, "--help"])

        assert result.exit_code == 0, result.output
        assert "Usage" in result.output


def test_the_readme_quickstart_works_from_an_empty_directory(workspace: Path):
    assert runner.invoke(app, ["generate-corpus"]).exit_code == 0
    assert (workspace / "corpus" / "nimbus-of-helix.pdf").exists()
    assert (workspace / "corpus" / "README.md").exists()

    review = runner.invoke(app, ["review", "--extractor", "rules"])
    assert review.exit_code == 0
    assert "need a reviewer" in review.stdout
    assert (workspace / "out" / "index.html").exists()

    assert runner.invoke(app, ["build-gold"]).exit_code == 0

    evaluation = runner.invoke(app, ["eval", "--extractor", "rules"])
    assert evaluation.exit_code == 0
    assert "Precision" in evaluation.stdout
    assert "(100%)" in evaluation.stdout


def test_reviewing_a_single_contract_writes_one_memo(workspace: Path):
    runner.invoke(app, ["generate-corpus"])

    result = runner.invoke(
        app, ["review", "corpus/nimbus-of-pinegrove.pdf", "--extractor", "rules"]
    )

    assert result.exit_code == 0
    assert "0 judgments" in result.stdout
    assert (workspace / "out" / "nimbus-of-pinegrove.html").exists()
    assert not (workspace / "out" / "index.html").exists()


def test_eval_can_save_its_report_as_an_artifact(workspace: Path):
    """A published number should have a run behind it that someone can open."""
    runner.invoke(app, ["generate-corpus"])
    runner.invoke(app, ["build-gold"])

    result = runner.invoke(app, ["eval", "--extractor", "rules", "--save", "--mistakes"])

    assert result.exit_code == 0
    saved = workspace / "evals" / "results" / "rules.json"
    assert saved.exists()
    assert '"extractor": "rules"' in saved.read_text(encoding="utf-8")


def test_asking_for_the_model_extractor_without_a_key_fails(workspace: Path):
    runner.invoke(app, ["generate-corpus"])

    result = runner.invoke(app, ["review", "--extractor", "llm"])

    assert result.exit_code != 0


def test_reviewing_an_empty_directory_says_so(workspace: Path):
    empty = workspace / "nothing"
    empty.mkdir()

    with pytest.raises(FileNotFoundError):
        review_directory(empty)


def test_the_pipeline_returns_reviews_in_filename_order(workspace: Path):
    runner.invoke(app, ["generate-corpus"])

    reviews, unreadable = review_directory(workspace / "corpus")

    assert unreadable == []
    assert [review.doc_id for review in reviews] == sorted(review.doc_id for review in reviews)
    assert len(reviews) == 12


def test_reviewing_one_contract_directly(workspace: Path):
    runner.invoke(app, ["generate-corpus"])

    review = review_contract(workspace / "corpus" / "nimbus-of-helix.pdf")

    assert review.doc_id == "nimbus-of-helix"
    assert review.needs_review()
    assert "judgments" in review.summary_line()


def _scanned(path: Path) -> Path:
    from reportlab.pdfgen import canvas

    page = canvas.Canvas(str(path))
    page.rect(50, 50, 200, 200, fill=1)
    page.showPage()
    page.save()
    return path


def test_one_unreadable_file_does_not_stop_the_rest_of_the_folder(workspace: Path):
    """It used to: one scanned contract and the run ended in a traceback before
    a single memo was written. Triage wants the opposite -- review what can be
    read, and put what can't at the top of the index."""
    runner.invoke(app, ["generate-corpus"])
    folder = workspace / "mixed"
    folder.mkdir()
    for name in ("nimbus-of-helix.pdf", "nimbus-of-pinegrove.pdf"):
        (folder / name).write_bytes((workspace / "corpus" / name).read_bytes())
    _scanned(folder / "aaa-scanned.pdf")
    (folder / "not-really.pdf").write_text("this is not a pdf", encoding="utf-8")

    result = runner.invoke(app, ["review", str(folder), "--extractor", "rules", "--out", "mixed-out"])

    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert (workspace / "mixed-out" / "nimbus-of-helix.html").exists()
    assert (workspace / "mixed-out" / "nimbus-of-pinegrove.html").exists()
    index = (workspace / "mixed-out" / "index.html").read_text(encoding="utf-8")
    assert "2 could not be read" in index
    assert index.index("aaa-scanned.pdf") < index.index("nimbus-of-helix")
    assert "OCR" in index


def test_a_single_unreadable_file_is_one_line_not_a_traceback(workspace: Path):
    _scanned(workspace / "scanned.pdf")

    for target in ("scanned.pdf", "missing.pdf"):
        result = runner.invoke(app, ["review", target, "--extractor", "rules"])

        assert result.exit_code == 1
        assert "Cannot review" in result.output
        assert "Traceback" not in result.output


def test_a_folder_review_writes_a_pdf_per_memo_and_a_worklist(workspace: Path):
    runner.invoke(app, ["generate-corpus"])

    result = runner.invoke(app, ["review", "--extractor", "rules"])

    assert result.exit_code == 0
    out = workspace / "out"
    memos = sorted(path.stem for path in out.glob("*.html") if path.stem != "index")
    assert sorted(path.stem for path in out.glob("*.pdf")) == memos
    assert len(memos) == 12
    assert (out / "worklist.xlsx").is_file()
    assert f"Worklist: {Path('out') / 'worklist.xlsx'}" in result.stdout


def test_a_single_contract_gets_its_pdf_and_no_worklist(workspace: Path):
    runner.invoke(app, ["generate-corpus"])

    result = runner.invoke(app, ["review", "corpus/nimbus-of-pinegrove.pdf", "--extractor", "rules"])

    assert result.exit_code == 0
    assert (workspace / "out" / "nimbus-of-pinegrove.pdf").is_file()
    assert not (workspace / "out" / "worklist.xlsx").exists()
