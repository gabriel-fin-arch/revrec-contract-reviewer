"""Command line interface.

Seven commands, in the order you'd use them: build the corpus, review it,
refresh the gold set, score against it, score a saved run again without
extracting, list the judgments a saved run got wrong with the passages behind
them, and estimate what a model run would cost before making one. `demo`
runs the first, second and fourth with the offline rules, in one go, and
`site` writes the rules review as the static pages CI publishes.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import anthropic
import typer
from dotenv import load_dotenv

from revrec_contract_reviewer.corpus import CorpusSet, generate_corpus
from revrec_contract_reviewer.evaluate import (
    CorpusChanged,
    SavedRun,
    claims_path,
    evaluate,
    markdown_table,
    partial_path,
    rescore,
    run_eval,
    write_gold,
)
from revrec_contract_reviewer.evaluate.estimate import estimate_run
from revrec_contract_reviewer.evaluate.misses import judgment_misses, report_lines
from revrec_contract_reviewer.extract import ExtractorChoice, llm
from revrec_contract_reviewer.fileio import write_lf
from revrec_contract_reviewer.ingest import UnreadableContract
from revrec_contract_reviewer.pipeline import review_contract, review_directory
from revrec_contract_reviewer.report import (
    SiteNote,
    write_index,
    write_pdf_memo,
    write_review,
    write_worklist,
)

load_dotenv()

app = typer.Typer(
    add_completion=False,
    help="ASC 606 contract review with cited evidence.",
    no_args_is_help=True,
)

DEFAULT_CORPUS = Path("corpus")
DEFAULT_OUT = Path("out")
DEFAULT_GOLD = Path("evals/gold")
DEFAULT_SITE = Path("site")
REPO = "https://github.com/gabriel-fin-arch/revrec-contract-reviewer"

# Where each set lives: its PDFs, its gold records, its saved runs. The test
# set sits one level down, so a review or an eval of corpus/ never picks it up.
SET_DIRS: dict[CorpusSet, tuple[Path, Path, Path]] = {
    CorpusSet.DEVELOPMENT: (DEFAULT_CORPUS, DEFAULT_GOLD, Path("evals/results")),
    CorpusSet.TEST: (DEFAULT_CORPUS / "test", DEFAULT_GOLD / "test", Path("evals/results/test")),
}
RUN_NAME = re.compile(r"[a-z0-9][a-z0-9.-]*")
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


@app.command()
def demo() -> None:
    """Build the corpus, review it and score it with the offline rules, in one command."""
    # Every step is pinned to the rules extractor, which never calls out, so
    # this makes no API call whatever key is in the environment or in .env.
    generate_corpus_command(DEFAULT_CORPUS, CorpusSet.DEVELOPMENT)
    typer.echo("")
    review(DEFAULT_CORPUS, DEFAULT_OUT, ExtractorChoice.RULES)
    if not DEFAULT_GOLD.exists():  # a clone has it committed; an empty directory doesn't
        write_gold(DEFAULT_GOLD)
    typer.echo("")
    typer.echo(markdown_table(run_eval(DEFAULT_CORPUS, DEFAULT_GOLD, ExtractorChoice.RULES)))
    typer.echo("")
    typer.echo(
        f"Open {DEFAULT_OUT / 'index.html'} for the worklist and a memo per contract. The contracts are "
        "synthetic, and this run used the offline rules, not a model."
    )


@app.command()
def site(
    out_dir: Path = typer.Option(DEFAULT_SITE, "--out", help="Where to write the pages."),
) -> None:
    """The corpus reviewed with the offline rules, as static pages (what CI publishes to GitHub Pages)."""
    generate_corpus(DEFAULT_CORPUS)
    reviews, unreadable = review_directory(DEFAULT_CORPUS, ExtractorChoice.RULES)
    # GITHUB_SHA is set in Actions; the pages say which commit they were built from.
    commit = os.environ.get("GITHUB_SHA")
    note = SiteNote(
        text=(
            f"These {len(reviews)} contracts are synthetic, from the repo's corpus, and were reviewed with the offline "
            "rules extractor, not a model" + (f", at commit {commit[:7]}." if commit else ".")
        ),
        link=REPO,
        link_text="Source on GitHub",
    )
    for result in reviews:
        write_review(result, out_dir, note)
    index = write_index(reviews, out_dir, unreadable, note)
    typer.echo(f"Wrote {len(reviews)} memos and {index}")
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
    effort: str | None = typer.Option(
        None,
        "--effort",
        help="Effort for the model extractor: low, medium, high, xhigh or max. Defaults to high, or REVREC_EFFORT.",
    ),
    name: str | None = typer.Option(
        None,
        "--name",
        help="With --save, the file name to save under instead of the extractor's, so a run made after a change "
        "sits beside the one before it.",
    ),
) -> None:
    """Score the pipeline against the gold set."""
    default_corpus, default_gold, results_dir = SET_DIRS[corpus_set]
    if effort is not None and effort not in llm.EFFORTS:
        typer.echo(f"--effort must be one of {', '.join(llm.EFFORTS)}", err=True)
        raise typer.Exit(code=2)
    if name is not None and not RUN_NAME.fullmatch(name):
        typer.echo("--name takes lower-case letters, digits, dots and hyphens", err=True)
        raise typer.Exit(code=2)
    # With --save, the run so far is written after every contract, so a run
    # that stops half-way keeps the calls it has already paid for. A run that
    # finishes replaces it with the report and the claims.
    so_far: list[SavedRun] = []

    def checkpoint(partial: SavedRun) -> None:
        so_far[:] = [partial]
        if save and partial.calls():
            results_dir.mkdir(parents=True, exist_ok=True)
            write_lf(partial_path(results_dir, _run_name(partial, name)), partial.model_dump_json(indent=2) + "\n")

    try:
        report, run = evaluate(
            corpus_dir or default_corpus, gold_dir or default_gold, extractor, effort=effort, checkpoint=checkpoint
        )
    except Exception as exc:
        _report_stopped(exc, so_far[0] if so_far else None, results_dir, name, save)
        if isinstance(exc, (anthropic.APIError, llm.ModelDeclined, RuntimeError)):
            raise typer.Exit(code=1) from exc
        raise
    typer.echo(markdown_table(report))
    summary = run.summary()
    if summary:
        typer.echo(f"\n{summary}")

    if save:
        results_dir.mkdir(parents=True, exist_ok=True)
        # A model run is named for its model and effort, so a new run sits next
        # to the published one instead of replacing it.
        target = write_lf(results_dir / f"{_run_name(run, name)}.json", report.model_dump_json(indent=2) + "\n")
        # The run behind the counts: every claim and what grounding did with
        # it, so `rescore` can score it again without extracting again.
        claims = write_lf(claims_path(target), run.model_dump_json(indent=2) + "\n")
        partial_path(results_dir, _run_name(run, name)).unlink(missing_ok=True)
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


def _run_name(run: SavedRun, name: str | None) -> str:
    """--name if given; otherwise the extractor, or llm-<model>-<effort> for a model run."""
    if name is not None:
        return name
    return run.extractor if not run.calls() else f"llm-{run.model}-{run.effort}"


def _report_stopped(exc: Exception, partial: SavedRun | None, results_dir: Path, name: str | None, save: bool) -> None:
    typer.echo(f"The run stopped: {type(exc).__name__}: {exc}", err=True)
    if partial is None or not partial.calls():
        typer.echo("No model call had been billed.", err=True)
        return
    typer.echo(f"Before it stopped, {len(partial.contracts)} contract(s) were extracted. {partial.summary()}", err=True)
    if save:
        path = partial_path(results_dir, _run_name(partial, name))
        typer.echo(f"Their claims and calls are saved in {path}.", err=True)
    else:
        typer.echo("Nothing was saved: without --save the run is only printed.", err=True)


@app.command("estimate")
def estimate_command(
    corpus_set: CorpusSet = SET_OPTION,
    model: str | None = typer.Option(None, "--model", help="The model to cost. Defaults to the extractor's."),
) -> None:
    """Estimate the tokens and cost of a model run over a set, without calling the API."""
    corpus_dir, _, results_dir = SET_DIRS[corpus_set]
    try:
        estimate = estimate_run(corpus_dir, model or llm.model_name(), rules_claims=results_dir / "rules.claims.json")
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(f"Cannot estimate: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    for line in estimate.lines(f"{corpus_set.value} set"):
        typer.echo(line)


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


@app.command("judgment-misses")
def judgment_misses_command(
    saved: Path = typer.Argument(..., help="A saved run, evals/results/<extractor>.claims.json."),
    corpus_set: CorpusSet = SET_OPTION,
    gold_dir: Path | None = typer.Option(None, "--gold", help="Where the gold records are. Defaults to the set's."),
) -> None:
    """List the judgments a saved run raised or missed against the gold, with the passages behind them."""
    _, default_gold, _ = SET_DIRS[corpus_set]
    try:
        run = SavedRun.model_validate_json(saved.read_text(encoding="utf-8"))
        misses = judgment_misses(run, gold_dir or default_gold)
    except (OSError, ValueError) as exc:
        typer.echo(f"Cannot list the misses: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    for line in report_lines(misses):
        typer.echo(line)


if __name__ == "__main__":
    app()
