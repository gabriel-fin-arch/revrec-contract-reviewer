"""The review memo as a PDF, for filing.

Same content as the HTML memo, in the same order: the matters for judgment
with the words that raised them, the checks, the obligations, variable
consideration, and the supporting schedule with a quote and a page behind
every value. Laid out in one column rather than in tables, so the text reads
in order when it's copied or searched, and so a test can read it back out of
the PDF and compare it with the review it came from.

Built with reportlab, which the corpus generator already uses, with
`invariant` set so that the same review gives the same bytes.
"""

from __future__ import annotations

import io
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer

from revrec_contract_reviewer.models.citation import Citation
from revrec_contract_reviewer.models.review import ContractReview
from revrec_contract_reviewer.report.memo import _fact_groups

_BASE = getSampleStyleSheet()
STYLES = {
    "title": ParagraphStyle("title", parent=_BASE["Title"], alignment=0, fontSize=16, spaceAfter=4),
    "h2": ParagraphStyle("h2", parent=_BASE["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=4),
    "h3": ParagraphStyle("h3", parent=_BASE["Heading3"], fontSize=10, spaceBefore=6, spaceAfter=2),
    "body": ParagraphStyle("body", parent=_BASE["BodyText"], fontSize=9, leading=12),
    "small": ParagraphStyle("small", parent=_BASE["BodyText"], fontSize=8, leading=10, textColor=HexColor("#555555")),
    "quote": ParagraphStyle(
        "quote", parent=_BASE["BodyText"], fontSize=8.5, leading=11, leftIndent=8 * mm, textColor=HexColor("#333333")
    ),
}


def _p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(escape(text), STYLES[style])


def _bold_then(label: str, text: str, style: str = "body") -> Paragraph:
    return Paragraph(f"<b>{escape(label)}</b> {escape(text)}", STYLES[style])


def _quote(citation: Citation) -> Paragraph:
    return Paragraph(f"{escape(citation.excerpt())} <i>({escape(citation.label())})</i>", STYLES["quote"])


def _plural(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def memo_flowables(review: ContractReview) -> list[Flowable]:
    """The memo's content, in the HTML memo's order."""
    extraction = review.extraction
    flags = review.flags_in_review_order()
    failed = review.failed_checks()
    story: list[Flowable] = [
        _p(review.doc_id, "title"),
        _p(
            f"ASC 606 review. {_plural(len(flags), 'matter')} for judgment, {_plural(len(failed), 'failed check')}."
        ),
    ]

    meta = []
    for label, field in (
        ("Customer", extraction.customer),
        ("Supplier", extraction.supplier),
        ("Currency", extraction.currency),
    ):
        if field.is_known:
            meta.append(f"{label} {field.value}")
    meta.append(f"Extractor {extraction.extractor}" + (f" ({extraction.model})" if extraction.model else ""))
    if extraction.dropped_for_no_evidence:
        meta.append(f"Dropped for no evidence {extraction.dropped_for_no_evidence}")
    story.append(_p(" · ".join(meta), "small"))

    story.append(_p("Matters for judgment", "h2"))
    if not flags:
        story.append(_p("Nothing in this document requires a judgment that the document itself cannot settle."))
    for flag in flags:
        block: list[Flowable] = [
            _p(f"Step {flag.step} · {flag.judgment_type.value.replace('_', ' ')}", "small"),
            _p(flag.question, "h3"),
            _p(flag.trigger),
        ]
        if flag.affects:
            block.append(_bold_then("Affects:", "; ".join(flag.affects)))
        block.extend(_quote(citation) for citation in flag.evidence)
        block.append(_bold_then("Why this is not answered here:", flag.why_a_human))
        block.append(Spacer(1, 3 * mm))
        story.append(KeepTogether(block))

    story.append(_p("Checks", "h2"))
    for check in review.checks:
        outcome = check.outcome.value.replace("_", " ")
        story.append(KeepTogether([_bold_then(f"{check.name}: {outcome}.", check.detail)]))

    story.append(_p("Step 2 · Performance obligations", "h2"))
    if not extraction.obligations:
        story.append(_p("No performance obligations were identified in this document."))
    for obligation in extraction.obligations:
        stated = str(obligation.stated_price.value) if obligation.stated_price.is_known else "--"
        listed = str(obligation.list_price.value) if obligation.list_price.is_known else "--"
        recognition = (
            obligation.recognition.value.value.replace("_", " ")
            if obligation.recognition.is_known and obligation.recognition.value is not None
            else "not evidenced"
        )
        block = [_p(obligation.label, "h3")]
        block.extend(_quote(citation) for citation in obligation.evidence[:1])
        if obligation.integration_language.is_known:
            block.append(_p(str(obligation.integration_language.value), "quote"))
        block.append(
            _p(
                f"Type: {obligation.kind.value.replace('_', ' ')} · Stated price: {stated} · "
                f"List rate: {listed} · Recognition: {recognition}"
            )
        )
        story.append(KeepTogether(block))

    story.append(_p("Step 3 · Variable consideration", "h2"))
    if not extraction.variable_consideration:
        story.append(_p("The transaction price is fixed by the document."))
    for term in extraction.variable_consideration:
        cap = str(term.cap.value) if term.cap.is_known else "none stated"
        block = [_p(term.description, "h3")]
        block.extend(_quote(citation) for citation in term.evidence[:1])
        block.append(
            _p(
                f"Type: {term.kind.value.replace('_', ' ')} · Cap: {cap} · "
                f"Fixed by the contract: {'yes' if term.estimable_from_contract else 'no'}"
            )
        )
        story.append(KeepTogether(block))

    story.append(_p("Supporting schedule", "h2"))
    for group in _fact_groups(extraction):
        story.append(_p(f"{group.step} · {group.title}", "h3"))
        for row in group.rows:
            status = "" if row.is_absent else f" [{row.status}]"
            row_block: list[Flowable] = [_bold_then(f"{row.label}:", f"{row.display}{status}")]
            if row.field.note:
                row_block.append(_p(row.field.note, "small"))
            # Capped at three, as in the HTML memo: a phrase repeated six times
            # would otherwise read as six findings.
            row_block.extend(_quote(citation) for citation in row.field.citations[:3])
            if len(row.field.citations) > 3:
                row_block.append(
                    _p(f"and {len(row.field.citations) - 3} further occurrence(s) in the document", "small")
                )
            # A value and its quotes stay on one page, so a citation is never
            # split from its clause and page by a page break.
            story.append(KeepTogether(row_block))
    return story


def render_pdf_memo(review: ContractReview) -> bytes:
    """The memo for one contract, as PDF bytes."""
    buffer = io.BytesIO()

    def footer(canvas, document) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.drawString(18 * mm, 10 * mm, f"{review.doc_id} · ASC 606 review · page {document.page}")
        canvas.restoreState()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title=f"ASC 606 review -- {review.doc_id}",
        author="revrec-contract-reviewer",
        invariant=1,
    )
    document.build(memo_flowables(review), onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()


def write_pdf_memo(review: ContractReview, out_dir: Path) -> Path:
    """Write <doc_id>.pdf next to the HTML memo and return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{review.doc_id}.pdf"
    path.write_bytes(render_pdf_memo(review))
    return path
