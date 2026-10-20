"""Command line interface.

Five commands, in the order you'd use them: build the corpus, review it, refresh
the gold set, score against it, and score a saved run again without extracting.
"""

from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv

from revrec_contract_reviewer.corpus import CorpusSet, generate_corpus
from revrec_contract_reviewer.evaluate import (
    CorpusChanged,
    SavedRun,
    claims_path,
    evaluate,
    markdown_table,
    rescore,
    write_gold,
)
from revrec_contract_reviewer.extract import ExtractorChoice
from revrec_contract_reviewer.fileio import write_lf
from revrec_contract_reviewer.ingest import UnreadableContract
from revrec_contract_reviewer.pipeline import review_contract, review_directory
from revrec_contract_reviewer.report import write_index, write_pdf_memo, write_review, write_worklist

load_dotenv()

app = typer.Typer(
    add_completion=False,
    help="ASC 606 contract review with cited evidence.",
    no_args_is_help=True,
)

DEFAULT_CORPUS = Path("corpus")
DEFAULT_OUT = Path("out")
DEFAULT_GOLD = Path("evals/gold")

# Where each set lives: its PDFs, its gold records, its saved runs. The test
# set sits one level down, so a review or an eval of corpus/ never picks it up.
SET_DIRS: dict[CorpusSet, tuple[Path, Path, Path]] = {
    CorpusSet.DEVELOPMENT: (DEFAULT_CORPUS, DEFAULT_GOLD, Path("evals/results")),
    CorpusSet.TEST: (DEFAULT_CORPUS / "test", DEFAULT_GOLD / "test", Path("evals/results/test")),
}
SET_OPTION = typer.Option(
    CorpusSet.DEVELOPMENT,
    "--set",
    help="development: the twelve contracts the rules and prompt were written against. "
    "test: the seven held out, reported and never tuned on.",
)


@app.command("generate-corpus")
def generate_corpus_command(
    out_dir: Path | None = typer.Option(None, "--out", help="Where to write the PDFs. Defaults to the set's folder."),
    corpus_set: CorpusSet = SET_OPTION,
) -> None:
    """Rebuild the synthetic contract corpus."""
    out_dir = out_dir or SET_DIRS[corpus_set][0]
    written = generate_corpus(out_dir, corpus_set)
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
    """Review a contract, or every contract in a directory.

    Each contract gets an HTML memo, the same memo as a PDF, and a JSON file.
    A directory also gets an index and a worklist workbook with every open
    item in the run.
    """
    try:
        if path.is_dir():
            reviews, unreadable = review_directory(path, extractor)
        else:
            reviews, unreadable = [review_contract(path, extractor)], []
    except (FileNotFoundError, UnreadableContract) as exc:
        typer.echo(f"Cannot review: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    for result in reviews:
        write_review(result, out_dir)
        write_pdf_memo(result, out_dir)
        typer.echo(result.summary_line())
    for skipped in unreadable:
        typer.echo(f"{skipped.name}: not reviewed. {skipped.reason}", err=True)

    if len(reviews) > 1 or unreadable:
        index = write_index(reviews, out_dir, unreadable)
        needing = sum(1 for result in reviews if result.needs_review())
        typer.echo("")
        summary = f"{needing} of {len(reviews)} contracts need a reviewer"
        if unreadable:
            summary += f", and {len(unreadable)} could not be read"
        typer.echo(f"{summary}. Index: {index}")
        typer.echo(f"Worklist: {write_worklist(reviews, out_dir, unreadable)}")
    else:
        typer.echo(f"Memo written to {out_dir / (reviews[0].doc_id + '.html')}")

    # Some files were never reviewed. The memos and the index are still
    # written, but a script running this should not mistake it for a full run.
    if unreadable:
        raise typer.Exit(code=1)


@app.command("build-gold")
def build_gold_command(
    out_dir: Path | None = typer.Option(None, "--out", help="Where to write the gold records. Defaults to the set's."),
    corpus_set: CorpusSet = SET_OPTION,
) -> None:
    """Regenerate the gold set from the corpus specs."""
    out_dir = out_dir or SET_DIRS[corpus_set][1]
    written = write_gold(out_dir, corpus_set)
    typer.echo(f"Wrote {len(written)} gold records to {out_dir}/.")


@app.command("eval")
def eval_command(
    corpus_set: CorpusSet = SET_OPTION,
    corpus_dir: Path | None = typer.Option(None, "--corpus", help="Where the PDFs are. Defaults to the set's."),
    gold_dir: Path | None = typer.Option(None, "--gold", help="Where the gold records are. Defaults to the set's."),
    extractor: ExtractorChoice = typer.Option(ExtractorChoice.AUTO, "--extractor"),
    show_mistakes: bool = typer.Option(False, "--mistakes", help="List every individual miss."),
    save: bool = typer.Option(
        False,
        "--save",
        help="Write the report and its claims to the set's results folder, so a published number has a "
        "run behind it.",
    ),
) -> None:
    """Score the pipeline against the gold set."""
    default_corpus, default_gold, results_dir = SET_DIRS[corpus_set]
    report, run = evaluate(corpus_dir or default_corpus, gold_dir or default_gold, extractor)
    typer.echo(markdown_table(report))

    if save:
        results_dir.mkdir(parents=True, exist_ok=True)
        target = write_lf(results_dir / f"{report.extractor}.json", report.model_dump_json(indent=2) + "\n")
        # The run behind the counts: every claim and what grounding did with
        # it, so `rescore` can score it again without extracting again.
        claims = write_lf(claims_path(target), run.model_dump_json(indent=2) + "\n")
        typer.echo(f"\nSaved to {target}, and the claims behind it to {claims}")

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


@app.command("rescore")
def rescore_command(
    saved: Path = typer.Argument(..., help="A saved run, evals/results/<extractor>.claims.json."),
    corpus_set: CorpusSet = SET_OPTION,
    corpus_dir: Path | None = typer.Option(None, "--corpus", help="Where the PDFs are. Defaults to the set's."),
    gold_dir: Path | None = typer.Option(None, "--gold", help="Where the gold records are. Defaults to the set's."),
) -> None:
    """Score a saved run again from its claims, without extracting anything."""
    default_corpus, default_gold, _ = SET_DIRS[corpus_set]
    try:
        run = SavedRun.model_validate_json(saved.read_text(encoding="utf-8"))
        report = rescore(run, corpus_dir or default_corpus, gold_dir or default_gold)
    except (OSError, CorpusChanged, ValueError) as exc:
        typer.echo(f"Cannot rescore: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(markdown_table(report))

    if report.citations_resolved != report.citations_total:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
