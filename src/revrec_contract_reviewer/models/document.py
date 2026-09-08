"""The parsed contract, before anyone tries to understand it.

Everything here is mechanical: pages, character offsets, clause boundaries. No
accounting meaning has been attached yet. Keeping that split explicit matters
because the offsets are what every later citation resolves against -- if this
layer is wrong, every piece of evidence in the memo points at the wrong words,
and nothing downstream can detect it.
"""

from __future__ import annotations

from bisect import bisect_right
from pathlib import Path

from pydantic import BaseModel, Field


class Page(BaseModel):
    """One page of the PDF, and where its text sits in the document-wide string."""

    number: int = Field(ge=1)
    start: int = Field(ge=0, description="Offset of this page's first character in ContractDocument.text.")
    end: int = Field(ge=0)
    text: str


class Clause(BaseModel):
    """A numbered section of the contract.

    Segmentation is a convenience for the extractor, not a source of truth. A
    citation resolves against the document text, never against a clause, so a
    mis-split clause costs us retrieval quality but can never produce a citation
    that points somewhere the words aren't.
    """

    number: str = Field(description='Clause number as printed, e.g. "4.2". Empty for unnumbered preamble text.')
    heading: str = ""
    text: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    page: int = Field(ge=1)

    def reference(self) -> str:
        if self.number and self.heading:
            return f"{self.number} {self.heading}"
        return self.number or self.heading or f"p.{self.page}"


class ContractDocument(BaseModel):
    """A contract PDF turned into addressable text."""

    doc_id: str = Field(description="Stable identifier, taken from the filename stem.")
    source_path: Path
    text: str
    pages: list[Page]
    clauses: list[Clause] = []

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def page_for_offset(self, offset: int) -> int:
        """Which page a character offset falls on.

        Binary search rather than a linear scan -- not for speed on a 12-page
        contract, but because grounding calls this once per candidate quote per
        field, and a linear scan here was the first thing that showed up when the
        eval harness started running the whole corpus in a loop.
        """
        if not self.pages:
            raise ValueError(f"{self.doc_id} has no pages to locate offset {offset} in")
        starts = [page.start for page in self.pages]
        index = bisect_right(starts, offset) - 1
        return self.pages[max(index, 0)].number

    def clause_for_offset(self, offset: int) -> Clause | None:
        for clause in self.clauses:
            if clause.start <= offset < clause.end:
                return clause
        return None
