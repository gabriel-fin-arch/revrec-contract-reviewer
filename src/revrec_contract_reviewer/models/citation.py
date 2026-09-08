"""Citations -- the pointer from an asserted fact back to the words that support it.

A Citation is only ever built by the grounding step, never by the extractor and
never by hand in application code. That is the whole control: the extractor says
"the contract says X, and here is the sentence I read it in", and grounding is
what checks that sentence actually exists in the PDF before anyone is allowed to
rely on it. If the quote can't be located, no Citation gets built and the fact it
was supporting is dropped.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class Citation(BaseModel):
    """One located span of source text.

    Offsets are into the document's raw extracted text, not the normalised form
    used for searching, so a reader (or the HTML memo) can slice the original
    characters and get back something that looks like the PDF.
    """

    page: int = Field(ge=1, description="1-indexed page number, matching what the reader sees in the PDF.")
    start: int = Field(ge=0, description="Character offset of the quote in the document's raw text.")
    end: int = Field(gt=0)
    quote: str = Field(min_length=1, description="The source text as it appears in the document.")

    @model_validator(mode="after")
    def _span_is_coherent(self) -> Citation:
        if self.end <= self.start:
            raise ValueError(f"citation span ends before it starts: [{self.start}, {self.end})")
        return self

    def label(self) -> str:
        """Short human reference, the way it appears in the memo: `p.4`."""
        return f"p.{self.page}"

    def excerpt(self, limit: int = 220) -> str:
        """The quote, trimmed for display in a table cell."""
        collapsed = " ".join(self.quote.split())
        if len(collapsed) <= limit:
            return collapsed
        return collapsed[: limit - 1].rstrip() + "…"
