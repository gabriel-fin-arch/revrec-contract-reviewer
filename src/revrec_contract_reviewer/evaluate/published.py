"""The numbers the README publishes, rendered from the saved runs.

Three blocks in the README come from the runs saved under `evals/results/`
rather than from a keyboard: the three results near the top, the development
table (every measured run on the 12-contract development set) and the test
table. tests/test_published_results.py fails if the README and the saved runs
disagree, and reruns the rules evaluation to check that `rules.json` is still
what the code produces. After a deliberate change,

    uv run python -m revrec_contract_reviewer.evaluate.published --write

rewrites the three blocks. Nothing here calls the API.
"""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

from revrec_contract_reviewer.evaluate.score import EvalReport, Tally

ROOT = Path(__file__).resolve().parents[3]
README = ROOT / "README.md"
RESULTS = ROOT / "evals" / "results"
BLOCKS = ("results-headline", "results-table", "test-table")

# The columns of each published table, as (saved-run name, column label).
# `llm` is the September run, kept as the last development column.
DEV_COLUMNS = (
    ("rules", "Rules"),
    ("llm-claude-opus-5-5-high", "Claude Opus 5.5"),
    ("llm-claude-opus-5-high", "Claude Opus 5"),
    ("llm", "Claude Opus 5, September"),
)
TEST_COLUMNS = DEV_COLUMNS[:3]


def load(extractor: str, results_dir: Path = RESULTS) -> EvalReport:
    return EvalReport.model_validate_json((results_dir / f"{extractor}.json").read_text(encoding="utf-8"))


def _model_label(report: EvalReport) -> str:
    # The saved run records the model string it called; the README names it.
    names = {"claude-opus-5": "Claude Opus 5"}
    return names.get(report.model or "", report.model or "the model")


def _blank(report: EvalReport) -> str:
    s = report.silence
    return f"{s.true_positives} of {s.true_positives + s.false_positives}"


def _cell(tally: Tally) -> str:
    return f"{tally.precision:.2f} / {tally.recall:.2f}"


def _table(reports: list[EvalReport], labels: list[str]) -> list[str]:
    """One precision / recall table, one column per run. No bold: with more
    than two columns there is no single winner a bold face could name."""
    rows = [
        "| Measure | " + " | ".join(labels) + " |",
        "|" + "---|" * (len(labels) + 1),
        "| Contract fields | " + " | ".join(_cell(r.fields) for r in reports) + " |",
        "| Unstated fields left blank | " + " | ".join(_blank(r) for r in reports) + " |",
        "| Performance obligations | " + " | ".join(_cell(r.obligations) for r in reports) + " |",
        "| Judgment flags | " + " | ".join(_cell(r.judgments) for r in reports) + " |",
    ]
    return rows


def _citations_line(reports: list[EvalReport]) -> str:
    rates = {round(r.citation_rate, 4) for r in reports}
    if len(rates) == 1:
        return f"Citations re-resolved against the source: **{reports[0].citation_rate:.0%}** on every run."
    per_run = ", ".join(f"{r.citation_rate:.0%} ({r.citations_total})" for r in reports)
    return f"Citations re-resolved against the source: {per_run}."


def results_table(reports: list[EvalReport], labels: list[str]) -> str:
    return "\n".join(
        _table(reports, labels)
        + ["", _citations_line(reports), "Saved runs in [`evals/results/`](evals/results/)."]
    )


def test_table(reports: list[EvalReport], labels: list[str]) -> str:
    return "\n".join(_table(reports, labels))


def headline(rules: EvalReport, model: EvalReport) -> str:
    label = _model_label(model)
    contracts = len(rules.per_contract)
    f_r, f_m, j_r, j_m = rules.fields, model.fields, rules.judgments, model.judgments
    intro = (
        f"**Results on the sample corpus** ({contracts} synthetic contracts, scored against a committed gold "
        "set; the tests check these figures against the saved runs and repeat the rules run):"
    )
    bullets = [
        f"Contract fields: precision {f_r.precision:.2f} and recall {f_r.recall:.2f} with the offline rules, "
        f"{f_m.precision:.2f} and {f_m.recall:.2f} with {label}.",
        f"Judgment flags: precision {j_r.precision:.2f} and recall {j_r.recall:.2f} with the rules, "
        f"{j_m.precision:.2f} and {j_m.recall:.2f} with the model.",
        f"Citations re-resolved against the source: {rules.citations_resolved} of {rules.citations_total} "
        f"with the rules, {model.citations_resolved} of {model.citations_total} with the model. "
        "[Full results](#results).",
    ]
    wrap = textwrap.TextWrapper(width=80, break_on_hyphens=False, break_long_words=False)
    lines = wrap.wrap(intro) + [""]
    for b in bullets:
        wrap.initial_indent, wrap.subsequent_indent = "- ", "  "
        lines += wrap.wrap(b)
    return "\n".join(lines)


def render(results_dir: Path = RESULTS) -> dict[str, str]:
    dev = [load(name, results_dir) for name, _ in DEV_COLUMNS]
    test = [load(name, results_dir / "test") for name, _ in TEST_COLUMNS]
    return {
        "results-headline": headline(dev[0], dev[-1]),
        "results-table": results_table(dev, [label for _, label in DEV_COLUMNS]),
        "test-table": test_table(test, [label for _, label in TEST_COLUMNS]),
    }


def _markers(name: str) -> tuple[str, str]:
    return f"<!-- {name}:start -->", f"<!-- {name}:end -->"


def readme_block(text: str, name: str) -> str:
    start, end = _markers(name)
    _, sep, rest = text.partition(start)
    body, sep2, _ = rest.partition(end)
    if not sep or not sep2:
        raise ValueError(f"README has no {start} ... {end} block")
    return body.strip("\n")


def write_readme(blocks: dict[str, str], path: Path = README) -> None:
    raw = path.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")
    for name, block in blocks.items():
        start, end = _markers(name)
        head, _, rest = text.partition(start)
        _, _, tail = rest.partition(end)
        text = f"{head}{start}\n{block}\n{end}{tail}"
    path.write_bytes(text.replace("\n", eol).encode("utf-8"))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="rewrite the blocks in README.md")
    args = parser.parse_args(argv)
    blocks = render()
    if args.write:
        write_readme(blocks)
    for name in BLOCKS:
        print(f"--- {name}\n{blocks[name]}")


if __name__ == "__main__":
    main()
