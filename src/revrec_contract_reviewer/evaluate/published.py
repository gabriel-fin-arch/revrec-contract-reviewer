"""The numbers the README publishes, rendered from the saved runs.

Two blocks in the README come from `evals/results/rules.json` and
`evals/results/llm.json` rather than from a keyboard: the three results near
the top and the Results table. tests/test_published_results.py fails if the
README and the saved runs disagree, and reruns the rules evaluation to check
that `rules.json` is still what the code produces. After a deliberate change,

    uv run python -m revrec_contract_reviewer.evaluate.published --write

rewrites both blocks. Nothing here calls the API.
"""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

from revrec_contract_reviewer.evaluate.score import EvalReport, Tally

ROOT = Path(__file__).resolve().parents[3]
README = ROOT / "README.md"
RESULTS = ROOT / "evals" / "results"
BLOCKS = ("results-headline", "results-table")


def load(extractor: str, results_dir: Path = RESULTS) -> EvalReport:
    return EvalReport.model_validate_json((results_dir / f"{extractor}.json").read_text(encoding="utf-8"))


def _model_label(report: EvalReport) -> str:
    # The saved run records the model string it called; the README names it.
    names = {"claude-opus-5": "Claude Opus 5"}
    return names.get(report.model or "", report.model or "the model")


def _pair(a: float, b: float) -> tuple[str, str]:
    """Two values to two decimals, the higher one in bold; a tie stays plain."""
    sa, sb = f"{a:.2f}", f"{b:.2f}"
    if sa == sb:
        return sa, sb
    return (f"**{sa}**", sb) if a > b else (sa, f"**{sb}**")


def _cells(rules: Tally, model: Tally) -> tuple[str, str]:
    rp, mp = _pair(rules.precision, model.precision)
    rr, mr = _pair(rules.recall, model.recall)
    return f"{rp} / {rr}", f"{mp} / {mr}"


def _blank(report: EvalReport) -> str:
    s = report.silence
    return f"{s.true_positives} of {s.true_positives + s.false_positives}"


def results_table(rules: EvalReport, model: EvalReport) -> str:
    label = _model_label(model)
    rows = [
        f"| Measure | Rules | {label} |",
        "|---|---|---|",
        "| Contract fields | {} | {} |".format(*_cells(rules.fields, model.fields)),
        f"| Unstated fields left blank | {_blank(rules)} | {_blank(model)} |",
        "| Performance obligations | {} | {} |".format(*_cells(rules.obligations, model.obligations)),
        "| Judgment flags | {} | {} |".format(*_cells(rules.judgments, model.judgments)),
    ]
    if rules.citation_rate == model.citation_rate:
        cites = (
            f"Citations re-resolved against the source: **{rules.citation_rate:.0%}** on both runs "
            f"({rules.citations_total} and {model.citations_total})."
        )
    else:
        cites = (
            f"Citations re-resolved against the source: **{rules.citation_rate:.0%}** with the rules "
            f"({rules.citations_total}) and **{model.citation_rate:.0%}** with the model ({model.citations_total})."
        )
    return "\n".join(rows + ["", *textwrap.wrap(cites, 80), "Saved runs in [`evals/results/`](evals/results/)."])


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
    rules, model = load("rules", results_dir), load("llm", results_dir)
    return {"results-headline": headline(rules, model), "results-table": results_table(rules, model)}


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
