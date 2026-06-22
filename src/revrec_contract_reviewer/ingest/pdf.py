"""Read a contract PDF into addressable text.

Text layer only -- there is no OCR here and the README says so. A scanned
contract goes in and nothing comes out, which is the honest behaviour: silently
returning an empty document that then produces a review with no findings would
be far worse than refusing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from revrec_contract_reviewer.models.document import ContractDocument, Page

# A page number sitting on its own line, which is what this corpus's footer
# renders as once the layout is gone.
_PAGE_FOOTER = re.compile(r"^\s*Page\s+\d+\s*$", re.IGNORECASE)


def _strip_running_footer(text: str) -> str:
    """Drop a trailing page-number line.

    Worth doing rather than tolerating, because of what a footer does to text
    that crosses a page break. Join the pages raw and a clause split across
    pages 2 and 3 comes back as "...on ninety (90) days' written Page 2 notice,
    without further liability...". No quote of that sentence will ever match, so
    the field silently grounds to nothing and the contract looks like it doesn't
    contain a termination clause.

    Only the page-number pattern is handled. Detecting arbitrary running headers
    means comparing candidate lines across pages, and this corpus doesn't have
    any -- claiming to handle them without a document that exercises it would be
    a lie the tests couldn't catch.
    """
    lines = text.split("\n")
    while lines and (not lines[-1].strip() or _PAGE_FOOTER.match(lines[-1])):
        lines.pop()
    return "\n".join(lines)


def load_contract(path: Path) -> ContractDocument:
    """Parse `path` into a ContractDocument with per-page character offsets."""
    if not path.exists():
        raise FileNotFoundError(f"no contract at {path}")

    with pdfplumber.open(path) as pdf:
        raw_pages = [page.extract_text() or "" for page in pdf.pages]

    if not any(page.strip() for page in raw_pages):
        raise ValueError(
            f"{path.name} has no extractable text layer. This reviewer does not do OCR -- "
            f"a scanned contract needs to go through OCR before it gets here."
        )

    pages: list[Page] = []
    chunks: list[str] = []
    cursor = 0

    for number, raw in enumerate(raw_pages, start=1):
        body = _strip_running_footer(raw)
        # Pages are joined with a blank line. The separator belongs to no page,
        # which keeps every offset unambiguously attributable to one of them.
        separator = "\n\n" if number > 1 else ""
        cursor += len(separator)
        pages.append(Page(number=number, start=cursor, end=cursor + len(body), text=body))
        chunks.append(separator + body)
        cursor += len(body)

    return ContractDocument(
        doc_id=path.stem,
        source_path=path,
        text="".join(chunks),
        pages=pages,
    )
