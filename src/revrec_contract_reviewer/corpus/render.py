"""Turn a contract spec into a PDF that reads like something a customer signed.

Layout only -- no contract wording lives here, that's all in specs.py. The
renderer's one real job beyond looking plausible is producing *reproducible*
files: the eval harness compares extraction against a gold set keyed by page
number, so a rebuild that reflowed a clause onto a different page would look
like a regression in the model rather than a change in the paper.
"""

from __future__ import annotations

from pathlib import Path

from reportlab import rl_config

# reportlab stamps a creation timestamp and a random document id into every file
# it writes, so two runs of the generator produce byte-different PDFs. `invariant`
# turns both off. Set before the platypus imports below pick up the config.
rl_config.invariant = 1

# And no compression, which is not about file size. reportlab deflates page
# streams through zlib, and zlib does not promise identical output across
# versions -- Python 3.11 and 3.14 compress the same page to 2050 and 2059
# bytes. Identical content, different file, and every contributor on a
# different interpreter sees twelve modified PDFs they never touched. Storing
# the streams uncompressed costs a few kilobytes each and makes the corpus
# genuinely reproducible rather than reproducible-on-my-machine.
rl_config.pageCompression = 0

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_JUSTIFY  # noqa: E402
from reportlab.lib.pagesizes import LETTER  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from revrec_contract_reviewer.corpus.spec import ContractSpec, FeeTable, Section  # noqa: E402


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ContractTitle",
            parent=base["Title"],
            fontName="Times-Bold",
            fontSize=14,
            leading=18,
            spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "ContractSubtitle",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=10,
            leading=14,
            alignment=1,
            textColor=colors.HexColor("#333333"),
            spaceAfter=14,
        ),
        "heading": ParagraphStyle(
            "ClauseHeading",
            parent=base["Normal"],
            fontName="Times-Bold",
            fontSize=10.5,
            leading=14,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "ClauseBody",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "cell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=9,
            leading=12,
        ),
        "cellhead": ParagraphStyle(
            "TableHead",
            parent=base["Normal"],
            fontName="Times-Bold",
            fontSize=9,
            leading=12,
        ),
    }


def _footer(canvas, doc) -> None:  # noqa: ANN001 -- reportlab hands us its own types
    canvas.saveState()
    canvas.setFont("Times-Roman", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawCentredString(LETTER[0] / 2.0, 0.55 * inch, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def _fee_table_flowable(table: FeeTable, styles: dict[str, ParagraphStyle]) -> Table:
    header = [Paragraph(col, styles["cellhead"]) for col in table.columns]
    body = [[Paragraph(str(cell), styles["cell"]) for cell in row] for row in table.rows]

    # Column widths: first column carries the description and needs the room,
    # the rest are amounts and periods.
    remaining = len(table.columns) - 1
    widths = [3.1 * inch] + [(3.0 / remaining) * inch] * remaining

    flowable = Table([header, *body], colWidths=widths, hAlign="LEFT", repeatRows=1)
    flowable.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#888888")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDEDED")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return flowable


def _section_flowables(section: Section, styles: dict[str, ParagraphStyle]) -> list:
    heading = Paragraph(f"{section.number}. {section.heading}", styles["heading"])
    paragraphs = [Paragraph(text, styles["body"]) for text in section.paragraphs]

    # Keep the heading with its first paragraph. A clause number stranded at the
    # foot of a page is the sort of thing that makes a citation's page number
    # look wrong to someone checking it by eye.
    flowables: list = [KeepTogether([heading, paragraphs[0]])] if paragraphs else [heading]
    flowables.extend(paragraphs[1:])

    if section.table is not None:
        flowables.append(Spacer(1, 4))
        flowables.append(_fee_table_flowable(section.table, styles))
        flowables.append(Spacer(1, 6))

    return flowables


def render_contract(spec: ContractSpec, out_dir: Path) -> Path:
    """Write `spec` to `out_dir/<doc_id>.pdf` and return the path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{spec.doc_id}.pdf"

    styles = _styles()
    doc = SimpleDocTemplate(
        str(target),
        pagesize=LETTER,
        leftMargin=1.0 * inch,
        rightMargin=1.0 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
        title=spec.title,
        author=spec.supplier,
        subject="Synthetic contract -- not a real agreement",
    )

    story: list = [
        Paragraph(spec.title, styles["title"]),
        Paragraph(spec.subtitle, styles["subtitle"]),
        Paragraph(spec.preamble, styles["body"]),
        Spacer(1, 8),
    ]

    for section in spec.sections:
        if section.page_break_before:
            story.append(PageBreak())
        story.extend(_section_flowables(section, styles))

    story.append(Spacer(1, 18))
    story.append(Paragraph(spec.signature_block, styles["body"]))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return target
