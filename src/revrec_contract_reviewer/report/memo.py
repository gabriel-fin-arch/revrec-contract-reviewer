"""The review memo.

Structured the way a reviewer works rather than the way the data is stored: the
judgments come first, because they are the reason anyone opened the file, and the
extracted facts come last as the supporting schedule. Every value that made it
into the memo is followed by the words it came from and the page they are on, so
the memo can be checked against the PDF without opening the PDF.

The five-step grouping is not decoration. It is the order the standard asks the
questions in, and it is how a reviewer decides which of the flags they can
actually answer today.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from revrec_contract_reviewer.fileio import write_lf
from revrec_contract_reviewer.models.extraction import ContractExtraction
from revrec_contract_reviewer.models.fields import ExtractedField, FieldStatus
from revrec_contract_reviewer.models.review import ContractReview

TEMPLATE_DIR = Path(__file__).parent / "templates"


@dataclass(frozen=True)
class FactRow:
    """One line of the supporting schedule."""

    label: str
    field: ExtractedField[Any]

    @property
    def display(self) -> str:
        if self.field.value is None:
            # "not found", not "not stated". The second is a claim about the
            # contract, and an absent field does not support it -- nothing here
            # can tell a silent document apart from one nobody read properly.
            # Same mistake as a check that reported green because a value was
            # grounded, without asking what the value said.
            return "not found"
        value = self.field.value
        if isinstance(value, bool):
            return "yes" if value else "no"
        return str(getattr(value, "value", value))

    @property
    def status(self) -> str:
        return self.field.status.value

    @property
    def is_absent(self) -> bool:
        return self.field.status is FieldStatus.ABSENT


@dataclass(frozen=True)
class FactGroup:
    step: str
    title: str
    rows: list[FactRow]


def _fact_groups(extraction: ContractExtraction) -> list[FactGroup]:
    term = extraction.term
    payment = extraction.payment
    renewal = extraction.renewal

    return [
        FactGroup(
            step="Step 1",
            title="Is there a contract, and for how long?",
            rows=[
                FactRow("Customer", extraction.customer),
                FactRow("Supplier", extraction.supplier),
                FactRow("Agreement type", extraction.agreement_type),
                FactRow("Amends", extraction.amends),
                FactRow("Effective date", term.effective_date),
                FactRow("Stated term (months)", term.stated_term_months),
                FactRow("Auto-renews", term.auto_renews),
                FactRow("Termination for convenience", term.termination_for_convenience),
                FactRow("Termination notice (days)", term.termination_notice_days),
                FactRow("Termination compensation", term.termination_compensation),
            ],
        ),
        FactGroup(
            step="Step 3",
            title="What is the transaction price?",
            rows=[
                FactRow("Currency", extraction.currency),
                FactRow("Total fixed consideration", extraction.total_fixed_consideration),
                FactRow("Payment terms (net days)", payment.net_days),
                FactRow("Billing frequency", payment.billing_frequency),
                FactRow("Upfront fee", payment.upfront_fee),
                FactRow("Upfront fee refundable", payment.upfront_fee_refundable),
                FactRow("Payment spread (months)", payment.payment_spread_months),
            ],
        ),
        FactGroup(
            step="Step 2 / 4",
            title="Options and third-party content",
            rows=[
                FactRow("Renewal term (months)", renewal.renewal_term_months),
                FactRow("Renewal price", renewal.renewal_price),
                FactRow("Renewal described as discounted", renewal.described_as_discounted),
                FactRow("Third-party components", extraction.third_party_components),
            ],
        ),
    ]


@dataclass(frozen=True)
class SiteNote:
    """A line at the top of every page, when the review is published as a site."""

    text: str
    link: str
    link_text: str


def _environment(site_note: SiteNote | None = None) -> Environment:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["excerpt"] = lambda citation: citation.excerpt()
    environment.globals["site_note"] = site_note
    return environment


def render_memo(review: ContractReview, site_note: SiteNote | None = None) -> str:
    """The memo for one contract, as a self-contained HTML document."""
    template = _environment(site_note).get_template("memo.html.j2")
    return template.render(
        review=review,
        extraction=review.extraction,
        groups=_fact_groups(review.extraction),
        flags=review.flags_in_review_order(),
    )


def attention_order(reviews: list[ContractReview]) -> list[ContractReview]:
    """Contracts in the order a reviewer should open them.

    Ordered by everything that needs attention, failed checks included, not by
    judgment count alone. A contract the pipeline could not read raises no
    judgments, so under the old ordering it sank to the bottom of the worklist
    and sat there looking exactly like the clean one -- "0 judgments" reads as
    nothing to do, whether that is because there is nothing to decide or
    because nobody managed to read the document. Failed checks break ties,
    because a failed check means everything else in that memo is built on a
    reading that did not hold up. The index and the worklist workbook both use
    this order.
    """
    return sorted(
        reviews,
        key=lambda review: (
            -(len(review.flags) + len(review.failed_checks())),
            -len(review.failed_checks()),
            review.doc_id,
        ),
    )


def render_index(
    reviews: list[ContractReview],
    unreadable: Sequence[tuple[str, str]] = (),
    site_note: SiteNote | None = None,
) -> str:
    """The run index -- one row per contract, for someone triaging a portfolio.

    Files that could not be read at all are listed first, above the worklist:
    they need a person more than anything the review found.
    """
    template = _environment(site_note).get_template("index.html.j2")
    return template.render(
        unreadable=list(unreadable),
        reviews=attention_order(reviews),
        total_flags=sum(len(review.flags) for review in reviews),
        total_failed=sum(len(review.failed_checks()) for review in reviews),
        clean=[review for review in reviews if not review.needs_review()],
    )


def write_review(review: ContractReview, out_dir: Path, site_note: SiteNote | None = None) -> tuple[Path, Path]:
    """Write the memo and the machine-readable form. Returns both paths."""
    out_dir.mkdir(parents=True, exist_ok=True)

    memo_path = write_lf(out_dir / f"{review.doc_id}.html", render_memo(review, site_note))
    json_path = write_lf(
        out_dir / f"{review.doc_id}.json",
        json.dumps(review.model_dump(mode="json"), indent=2, ensure_ascii=False),
    )
    return memo_path, json_path


def write_index(
    reviews: list[ContractReview],
    out_dir: Path,
    unreadable: Sequence[tuple[str, str]] = (),
    site_note: SiteNote | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    return write_lf(out_dir / "index.html", render_index(reviews, unreadable, site_note))
