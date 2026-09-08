"""The memo, and the harness that scores the whole thing."""

from __future__ import annotations

from pathlib import Path

from revrec_contract_reviewer.assess import assess
from revrec_contract_reviewer.evaluate import load_gold, markdown_table, run_eval, write_gold
from revrec_contract_reviewer.evaluate.score import Tally
from revrec_contract_reviewer.extract import ExtractorChoice, extract_contract
from revrec_contract_reviewer.models.document import ContractDocument
from revrec_contract_reviewer.report import render_memo, write_index, write_review


def _review(document: ContractDocument):
    return assess(extract_contract(document, ExtractorChoice.RULES))


def test_the_memo_shows_the_words_behind_every_value(helix: ContractDocument):
    html = render_memo(_review(helix))

    assert "Total committed tees" not in html
    assert "GBP 312,000" in html
    assert "p.1" in html


def test_the_memo_names_the_extractor_that_produced_it(helix: ContractDocument):
    """A memo built from the offline fallback must say so on its face."""
    assert "rules" in render_memo(_review(helix))


def test_every_judgment_in_the_memo_states_why_it_was_not_answered(helix: ContractDocument):
    review = _review(helix)
    html = render_memo(review)

    assert review.flags
    for flag in review.flags:
        assert flag.question in html
    assert "Why this is not answered here" in html


def test_a_contract_with_nothing_to_say_says_so(pinegrove: ContractDocument):
    html = render_memo(_review(pinegrove))

    assert "Nothing in this document requires a judgment" in html


def test_writing_a_review_produces_a_memo_and_a_json(helix: ContractDocument, tmp_path: Path):
    memo_path, json_path = write_review(_review(helix), tmp_path)

    assert memo_path.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
    assert '"doc_id": "nimbus-of-helix"' in json_path.read_text(encoding="utf-8")


def test_the_index_orders_the_worklist_by_how_much_needs_deciding(documents, tmp_path: Path):
    reviews = [_review(document) for document in documents.values()]

    index = write_index(reviews, tmp_path).read_text(encoding="utf-8")

    assert "matters for judgment" in index
    busiest = max(reviews, key=lambda review: len(review.flags)).doc_id
    quietest = min(reviews, key=lambda review: len(review.flags)).doc_id
    assert index.index(busiest) < index.index(quietest)


def test_tally_rates():
    tally = Tally(true_positives=3, false_positives=1, false_negatives=1)

    assert tally.precision == 0.75
    assert tally.recall == 0.75
    assert round(tally.f1, 2) == 0.75


def test_an_empty_tally_does_not_divide_by_zero():
    assert Tally().precision == 1.0
    assert Tally().recall == 1.0


def test_gold_records_round_trip(tmp_path: Path):
    write_gold(tmp_path)

    records = load_gold(tmp_path)

    assert len(records) == 12
    assert records["nimbus-of-helix"].fields["stated_term_months"] == 24
    # A field the contract does not state is recorded as null and scored.
    assert records["nimbus-msa-calderwood"].fields["stated_term_months"] is None


def test_the_eval_runs_end_to_end_and_every_citation_resolves(corpus_dir: Path, tmp_path: Path):
    """The independent check that the grounding invariant actually held --
    re-resolving each citation in the finished review against the document."""
    gold_dir = tmp_path / "gold"
    write_gold(gold_dir)

    report = run_eval(corpus_dir, gold_dir, ExtractorChoice.RULES)

    assert report.citations_total > 100
    assert report.citations_resolved == report.citations_total
    assert report.dropped_for_no_evidence == 0
    assert "Precision" in markdown_table(report)


def test_inventing_a_value_where_the_contract_is_silent_is_scored_separately(
    corpus_dir: Path, tmp_path: Path
):
    gold_dir = tmp_path / "gold"
    write_gold(gold_dir)

    report = run_eval(corpus_dir, gold_dir, ExtractorChoice.RULES)

    # Silence is its own tally, so a run can have good field recall and still be
    # caught making things up about clauses that aren't there.
    assert report.silence.true_positives > 0
    assert report.silence.precision == 1.0


def test_a_gold_record_with_no_contract_is_an_error(corpus_dir: Path, tmp_path: Path):
    gold_dir = tmp_path / "gold"
    write_gold(gold_dir)
    (gold_dir / "nimbus-of-helix.json").write_text(
        (gold_dir / "nimbus-of-helix.json").read_text(encoding="utf-8").replace(
            "nimbus-of-helix", "contract-that-does-not-exist"
        ),
        encoding="utf-8",
    )

    try:
        run_eval(corpus_dir, gold_dir, ExtractorChoice.RULES)
    except FileNotFoundError as error:
        assert "contract-that-does-not-exist" in str(error)
    else:
        raise AssertionError("a gold record with no PDF should not be silently skipped")
