"""The gate every proposed fact has to get through.

This is the control the whole project is built around, so it's worth being blunt
about what it does and doesn't do.

It does: take a claim, look for the quoted words in the actual document, and
refuse to build a field if they aren't there.

It does not: judge whether the value is *right*. A quote that resolves and a
value that misreads it still gets through -- grounding catches invention, not
misinterpretation. Measuring misinterpretation is what the eval harness is for,
and the two failure modes are genuinely different: an ungrounded field is a
model asserting something the document never said, and no amount of prompting
makes that acceptable, while a misread field is an accuracy number you can
watch move.

Drops are counted, not swallowed. `dropped_for_no_evidence` ends up on the
extraction and in the memo, because a run where it climbs is a run that needs
looking at before anyone trusts the output.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import TypeVar

from revrec_contract_reviewer.extract.schema import Claim
from revrec_contract_reviewer.extract.values import (
    parse_bool,
    parse_date,
    parse_decimal,
    parse_enum,
    parse_int,
    parse_str,
)
from revrec_contract_reviewer.ingest.text import NormalizedText
from revrec_contract_reviewer.models.citation import Citation
from revrec_contract_reviewer.models.document import ContractDocument
from revrec_contract_reviewer.models.fields import ExtractedField

T = TypeVar("T")
E = TypeVar("E", bound=StrEnum)

# A quote has to be long enough to actually identify a passage. "30" appears
# forty times in a contract and grounds against all of them, which is evidence
# of nothing. Twelve characters is roughly three words -- short enough to allow
# "net thirty days", long enough to exclude a bare number.
MIN_QUOTE_LENGTH = 12


class Grounder:
    """Resolves claims against one document."""

    def __init__(self, document: ContractDocument) -> None:
        self.document = document
        self._text = NormalizedText(document.text)
        self.dropped = 0

    def citations_for(self, quotes: list[str]) -> list[Citation]:
        """Every quote that could be located, as citations. Unfindable quotes yield nothing.

        A quote appearing more than once produces a citation for each occurrence.
        That matters for the conflicting case: the reviewer needs to see both
        places the contract says something, not the first one.
        """
        citations: list[Citation] = []
        for quote in quotes:
            trimmed = quote.strip()
            if len(NormalizedText.normalize(trimmed)) < MIN_QUOTE_LENGTH:
                continue
            for start, end in self._text.find_all(trimmed):
                citations.append(
                    Citation(
                        page=self.document.page_for_offset(start),
                        start=start,
                        end=end,
                        quote=self.document.text[start:end],
                    )
                )
        return citations

    def field(self, claim: Claim | None, parse: Callable[[str | None], T | None]) -> ExtractedField[T]:
        """Build a domain field from a claim, or absent if the claim doesn't hold up."""
        if claim is None:
            return ExtractedField[T].absent()

        citations = self.citations_for(claim.quotes)
        if not citations:
            self.dropped += 1
            return ExtractedField[T].absent(
                note="Dropped: the supporting quote could not be located in the document."
            )

        value = parse(claim.value)
        if value is None:
            self.dropped += 1
            return ExtractedField[T].absent(note=f"Dropped: could not read a value from {claim.value!r}.")

        if claim.conflicting:
            return ExtractedField[T].ambiguous(
                value,
                citations,
                claim.note or "The document states this in more than one place, and the statements disagree.",
            )

        return ExtractedField[T].found(value, citations, claim.note)

    # The parse function is the only thing that varies between field types, so
    # these exist purely to keep call sites at the extraction boundary readable.

    def text_field(self, claim: Claim | None) -> ExtractedField[str]:
        return self.field(claim, parse_str)

    def money_field(self, claim: Claim | None) -> ExtractedField[Decimal]:
        return self.field(claim, parse_decimal)

    def count_field(self, claim: Claim | None) -> ExtractedField[int]:
        return self.field(claim, parse_int)

    def flag_field(self, claim: Claim | None) -> ExtractedField[bool]:
        return self.field(claim, parse_bool)

    def date_field(self, claim: Claim | None) -> ExtractedField[date]:
        return self.field(claim, parse_date)

    def enum_field(self, claim: Claim | None, enum_cls: type[E]) -> ExtractedField[E]:
        return self.field(claim, lambda raw: parse_enum(raw, enum_cls))
