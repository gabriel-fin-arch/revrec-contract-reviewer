"""Command line interface.

Four commands, in the order you'd use them: build the corpus, review it, refresh
the gold set, score against it.
"""

from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv

from revrec_contract_reviewer.corpus import generate_corpus
from revrec_contract_reviewer.evaluate import markdown_table, run_eval, write_gold
from revrec_contract_reviewer.extract import ExtractorChoice
from revrec_contract_reviewer.pipeline import review_contract, review_directory
from revrec_contract_reviewer.report import write_index, write_review

load_dotenv()

app = typer.Typer(
    add_completion=False,
    help="ASC 606 contract review with cited evidence.",
    no_args_is_help=True,
)

DEFAULT_CORPUS = Path("corpus")
DEFAULT_OUT = Path("out")
DEFAULT_GOLD = Path("evals/gold")


@app.command("generate-corpus")
def generate_corpus_command(
    out_dir: Path = typer.Option(DEFAULT_CORPUS, "--out", help="Where to write the PDFs."),
) -> None:
    """Rebuild the synthetic contract corpus."""
    written = generate_corpus(out_dir)
    typer.echo(f"Wrote {len(written)} contracts to {out_dir}/ and refreshed its index.")


@app.command()
def review(
    path: Path = typer.Argument(DEFAULT_CORPUS, help="A contract PDF, or a directory of them."),
    out_dir: Path = typer.Option(DEFAULT_OUT, "--out", help="Where to write memos."),
    extractor: ExtractorChoice = typer.Option(
        ExtractorChoice.AUTO,
        "--extractor",
        help="auto uses the model when an API key is present; rules never calls out; llm requires one.",
    ),
) -> None:
    """Review a contract, or every contract in a directory."""
    if path.is_dir():
        reviews = review_directory(path, extractor)
    else:
        reviews = [review_contract(path, extractor)]

    for result in reviews:
        write_review(result, out_dir)
        typer.echo(result.summary_line())

    if len(reviews) > 1:
        index = write_index(reviews, out_dir)
        needing = sum(1 for result in reviews if result.needs_review())
        typer.echo("")
        typer.echo(f"{needing} of {len(reviews)} contracts need a reviewer. Index: {index}")
    else:
        typer.echo(f"Memo written to {out_dir / (reviews[0].doc_id + '.html')}")


@app.command("build-gold")
def build_gold_command(
    out_dir: Path = typer.Option(DEFAULT_GOLD, "--out", help="Where to write the gold records."),
) -> None:
    """Regenerate the gold set from the corpus specs."""
    written = write_gold(out_dir)
    typer.echo(f"Wrote {len(written)} gold records to {out_dir}/.")


@app.command("eval")
def eval_command(
    corpus_dir: Path = typer.Option(DEFAULT_CORPUS, "--corpus", help="Where the contract PDFs are."),
    gold_dir: Path = typer.Option(DEFAULT_GOLD, "--gold", help="Where the gold records are."),
    extractor: ExtractorChoice = typer.Option(ExtractorChoice.AUTO, "--extractor"),
    show_mistakes: bool = typer.Option(False, "--mistakes", help="List every individual miss."),
    save: bool = typer.Option(
        False,
        "--save",
        help="Write the full report to evals/results/, so a published number has a run behind it.",
    ),
) -> None:
    """Score the pipeline against the gold set."""
    report = run_eval(corpus_dir, gold_dir, extractor)
    typer.echo(markdown_table(report))

    if save:
        results_dir = Path("evals/results")
        results_dir.mkdir(parents=True, exist_ok=True)
        target = results_dir / f"{report.extractor}.json"
        target.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
        typer.echo(f"\nSaved to {target}")

    if show_mistakes:
        typer.echo("")
        for score in report.per_contract:
            if not score.mistakes:
                continue
            typer.echo(score.doc_id)
            for mistake in score.mistakes:
                typer.echo(f"  - {mistake}")

    # A citation that no longer resolves means the grounding invariant has been
    # broken somewhere, which is a different order of problem from a low score.
    # Worth a non-zero exit so CI notices without anyone reading the table.
    if report.citations_resolved != report.citations_total:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
