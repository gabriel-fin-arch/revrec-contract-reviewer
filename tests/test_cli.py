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

    reviews = review_directory(workspace / "corpus")

    assert [review.doc_id for review in reviews] == sorted(review.doc_id for review in reviews)
    assert len(reviews) == 12


def test_reviewing_one_contract_directly(workspace: Path):
    runner.invoke(app, ["generate-corpus"])

    review = review_contract(workspace / "corpus" / "nimbus-of-helix.pdf")

    assert review.doc_id == "nimbus-of-helix"
    assert review.needs_review()
    assert "judgments" in review.summary_line()
