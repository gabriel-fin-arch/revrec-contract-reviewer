"""The three states a contract fact can be in, and the wrapper that carries it.

There is no confidence score anywhere in this project. A number like 0.72 invites
exactly one question in a review meeting -- "why 0.72?" -- and there is no honest
answer, because nothing in a contract is 72% true. What a reviewer actually needs
to know is which of three situations they're in:

  extracted  the document says it, and here is where
  ambiguous  the document says it in more than one place, and the places disagree
  absent     the document does not address this at all

Those three drive genuinely different actions. `absent` on a termination clause is
a drafting gap to raise with legal; `ambiguous` on the same clause is an order form
overriding an MSA and someone has to decide which governs. A single blended score
would have flattened both into "0.4, take a look".
"""

from __future__ import annotations

from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, model_validator

from revrec_contract_reviewer.models.citation import Citation

T = TypeVar("T")


class FieldStatus(StrEnum):
    EXTRACTED = "extracted"
    AMBIGUOUS = "ambiguous"
    ABSENT = "absent"


class ExtractedField(BaseModel, Generic[T]):
    """A single fact read off a contract, with the evidence that supports it.

    The invariant enforced below is the project's central rule in executable form:
    an EXTRACTED field must carry at least one citation. Anything the grounding
    step could not tie to real source text degrades to ABSENT with its value
    stripped -- not to a "low confidence" version of itself. A fact with no
    evidence is not a weak fact, it's not a fact.
    """

    value: T | None = None
    status: FieldStatus = FieldStatus.ABSENT
    citations: list[Citation] = []
    note: str | None = None

    @model_validator(mode="after")
    def _evidence_matches_status(self) -> ExtractedField[T]:
        if self.status is FieldStatus.EXTRACTED:
            if self.value is None:
                raise ValueError("an extracted field must carry a value")
            if not self.citations:
                raise ValueError("an extracted field must cite the text it came from")
        if self.status is FieldStatus.ABSENT and self.value is not None:
            raise ValueError("an absent field cannot carry a value")
        return self

    @property
    def is_known(self) -> bool:
        """True when we have a usable answer -- ambiguity is not a usable answer."""
        return self.status is FieldStatus.EXTRACTED

    @classmethod
    def absent(cls, note: str | None = None) -> ExtractedField[T]:
        return cls(value=None, status=FieldStatus.ABSENT, citations=[], note=note)

    @classmethod
    def found(cls, value: T, citations: list[Citation], note: str | None = None) -> ExtractedField[T]:
        return cls(value=value, status=FieldStatus.EXTRACTED, citations=citations, note=note)

    @classmethod
    def ambiguous(cls, value: T | None, citations: list[Citation], note: str) -> ExtractedField[T]:
        """Conflicting sources. `value` is whichever reading the extractor leaned to, and
        the note says what it conflicts with -- but `is_known` stays False either way,
        so nothing downstream can quietly treat it as settled."""
        return cls(value=value, status=FieldStatus.AMBIGUOUS, citations=citations, note=note)
