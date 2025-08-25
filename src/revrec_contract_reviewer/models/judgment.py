"""The taxonomy of things this tool will not decide.

Every entry here shares one property, and it's the property that justifies the
list existing: **answering it requires information that is not in the contract.**
Not "the model isn't confident enough" -- genuinely not in the document. An
entity's typical discount range, its estimate of how much variable consideration
will reverse, its assessment of whether it controls a third-party service before
transfer: none of that is written on the paper, so no amount of better reading
gets you there.

That is a much stronger position than a confidence threshold. A threshold invites
"can you tune it up?"; this doesn't, because the answer is a fact about where the
information lives.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from revrec_contract_reviewer.models.citation import Citation


class JudgmentType(StrEnum):
    ENFORCEABLE_TERM = "enforceable_term"
    DISTINCT_UNCERTAIN = "distinct_uncertain"
    PRINCIPAL_VS_AGENT = "principal_vs_agent"
    MATERIAL_RIGHT = "material_right"
    VARIABLE_CONSIDERATION_CONSTRAINT = "variable_consideration_constraint"
    SIGNIFICANT_FINANCING = "significant_financing"
    SSP_NOT_OBSERVABLE = "ssp_not_observable"
    CONTRACT_MODIFICATION = "contract_modification"


# Which of the five steps each judgment belongs to. Used for ordering the
# reviewer's worklist, and the ordering is not cosmetic: you cannot sensibly
# allocate a transaction price (step 4) until you've settled what the
# obligations are (step 2), so working the list top-down is working it in the
# only order that doesn't make you redo things.
JUDGMENT_STEP: dict[JudgmentType, int] = {
    JudgmentType.ENFORCEABLE_TERM: 1,
    JudgmentType.CONTRACT_MODIFICATION: 1,
    JudgmentType.DISTINCT_UNCERTAIN: 2,
    JudgmentType.MATERIAL_RIGHT: 2,
    JudgmentType.PRINCIPAL_VS_AGENT: 2,
    JudgmentType.VARIABLE_CONSIDERATION_CONSTRAINT: 3,
    JudgmentType.SIGNIFICANT_FINANCING: 3,
    JudgmentType.SSP_NOT_OBSERVABLE: 4,
}

# The standing reason each judgment stays with a human. These are properties of
# the standard and of where data lives, not settings -- which is why they're a
# constant rather than anything configurable.
WHY_A_HUMAN: dict[JudgmentType, str] = {
    JudgmentType.ENFORCEABLE_TERM: (
        "Whether a termination right is substantive turns on how enforceable the compensation clause is in the "
        "governing jurisdiction. That is a legal reading of the words, not a fact stated by them."
    ),
    JudgmentType.DISTINCT_UNCERTAIN: (
        "Whether a service significantly customises or is highly interdependent with another promise depends on how "
        "the work is actually delivered, which the contract describes only in general terms."
    ),
    JudgmentType.PRINCIPAL_VS_AGENT: (
        "Control of a third-party good or service before transfer depends on the operating arrangement behind the "
        "contract -- inventory risk, pricing discretion, who is responsible for fulfilment."
    ),
    JudgmentType.MATERIAL_RIGHT: (
        "A renewal discount is a material right only if it is incremental to the range the entity typically grants. "
        "That range is pricing data held by the entity, not a term of this contract."
    ),
    JudgmentType.VARIABLE_CONSIDERATION_CONSTRAINT: (
        "How much variable consideration to include requires an estimate of the probability of a significant "
        "reversal, which draws on the entity's own history with similar contracts."
    ),
    JudgmentType.SIGNIFICANT_FINANCING: (
        "Whether extended payment terms convey financing depends on the intent behind them and on prevailing rates "
        "at inception, neither of which the contract states."
    ),
    JudgmentType.SSP_NOT_OBSERVABLE: (
        "Standalone selling price is what the entity would charge selling separately. A contract records what it "
        "charged this customer on this deal -- the two only coincide by accident."
    ),
    JudgmentType.CONTRACT_MODIFICATION: (
        "Whether a modification is a separate contract, a prospective change, or a cumulative catch-up depends on "
        "whether the added goods are distinct and priced at their standalone selling price."
    ),
}


class JudgmentFlag(BaseModel):
    """One decision routed to a human, with the evidence that raised it."""

    judgment_type: JudgmentType
    question: str = Field(description="The decision, phrased as the question the reviewer has to answer.")
    trigger: str = Field(description="What in the document caused this to be raised.")
    evidence: list[Citation] = Field(description="Where in the contract the trigger was found.")
    affects: list[str] = Field(default=[], description="Obligation labels whose accounting this decision changes.")

    @model_validator(mode="after")
    def _evidence_is_unique(self) -> JudgmentFlag:
        """Collapse citations that point at the same span.

        A flag raised from several obligations gathers a citation from each, and
        when those obligations came off one fee table they all resolve to the
        same run of text. Printing it three times makes the memo look like it
        found three pieces of evidence when it found one.
        """
        seen: set[tuple[int, int]] = set()
        unique: list[Citation] = []
        for citation in self.evidence:
            key = (citation.start, citation.end)
            if key not in seen:
                seen.add(key)
                unique.append(citation)
        self.evidence = unique
        return self

    @property
    def step(self) -> int:
        return JUDGMENT_STEP[self.judgment_type]

    @property
    def why_a_human(self) -> str:
        return WHY_A_HUMAN[self.judgment_type]
