"""The judgment flags a saved run got wrong, with the passages behind them.

A judgment is raised by a rule in `assess/judgments.py` from what the
extractor read, so a false positive is a passage the extractor reported and
the rule acted on. Listing those passages is how a change to the prompt or to
a rule gets argued from cases rather than from a score. No extraction and no
API call: the review is rebuilt from the saved extraction, against the
committed gold.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from revrec_contract_reviewer.assess import assess
from revrec_contract_reviewer.evaluate.gold import load_gold
from revrec_contract_reviewer.evaluate.runs import SavedRun


@dataclass(frozen=True)
class JudgmentMiss:
    doc_id: str
    judgment: str
    raised: bool  # True: raised and not in the gold; False: in the gold and not raised
    trigger: str = ""
    passages: tuple[str, ...] = ()


def judgment_misses(run: SavedRun, gold_dir: Path) -> list[JudgmentMiss]:
    gold = load_gold(gold_dir)
    saved = {contract.doc_id: contract for contract in run.contracts}
    missing = sorted(set(gold) - set(saved))
    if missing:
        raise ValueError(f"the saved run has no claims for {', '.join(missing)}")

    misses = []
    for doc_id, record in sorted(gold.items()):
        expected = set(record.judgments)
        flags = {flag.judgment_type.value: flag for flag in assess(saved[doc_id].extraction).flags}
        for judgment in sorted(set(flags) - expected):
            flag = flags[judgment]
            passages = tuple(f"{citation.label()}: {citation.excerpt(400)}" for citation in flag.evidence)
            misses.append(JudgmentMiss(doc_id, judgment, raised=True, trigger=flag.trigger, passages=passages))
        for judgment in sorted(expected - set(flags)):
            misses.append(JudgmentMiss(doc_id, judgment, raised=False))
    return misses


def report_lines(misses: list[JudgmentMiss]) -> list[str]:
    raised = [miss for miss in misses if miss.raised]
    missed = [miss for miss in misses if not miss.raised]
    lines = [f"Raised and not in the gold: {len(raised)}{_by_type(raised)}"]
    for miss in raised:
        lines.append(f"  {miss.doc_id}: {miss.judgment}")
        lines.append(f"    trigger: {miss.trigger}")
        lines.extend(f"    - {passage}" for passage in miss.passages)
    lines.append(f"In the gold and not raised: {len(missed)}{_by_type(missed)}")
    lines.extend(f"  {miss.doc_id}: {miss.judgment}" for miss in missed)
    return lines


def _by_type(misses: list[JudgmentMiss]) -> str:
    if not misses:
        return ""
    counts = Counter(miss.judgment for miss in misses)
    return " (" + ", ".join(f"{judgment} {count}" for judgment, count in sorted(counts.items())) + ")"
