"""The wire format both extractors produce.

Not the domain model. Deliberately.

The domain model in `models/extraction.py` carries resolved citations, parsed
Decimals and dates, and an invariant that an extracted field must have evidence.
None of that can be produced by an extractor, because the extractor is the thing
being checked. Letting it build a Citation directly would be letting it mark
its own homework.

So an extractor's whole vocabulary is the `Claim` below: a value written as a
string, and the words in the document it came from. Grounding turns claims into
domain fields, and only grounding can. The offline rule-based extractor speaks
exactly the same wire format and goes through exactly the same gate, so "the
rules extractor doesn't have to cite anything" is not a shortcut available to it.

## Why the contract terms are a list rather than named fields

The obvious shape for this is one named field per contract term, each optional.
That shape does not survive contact with structured outputs, and it took two
different 400s to find out:

  `Claim | None` per term      -> "too many parameters with union types
                                  (21 ... limit: 16)"
  `list[Claim]` per term       -> "the compiled grammar is too large"

Strict output compiles the schema into a grammar, and a nested optional object
costs a lot of grammar. Probing it, the ceiling landed at about eleven such
fields; this schema wanted twenty-one. Splitting the request in two did not help
either: fourteen fields was still "schema is too complex".

What compiles, and stays compiling, is a **flat list of claims that each name
the term they are about**. The grammar is small and, more usefully, constant:
adding a twenty-second contract term is adding an enum member, not growing the
schema. It is a better shape than the one I set out to write, which is not how
these things usually go.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from revrec_contract_reviewer.models.extraction import ObligationKind, VariableConsiderationKind


class Claim(BaseModel):
    """A proposed fact and the text it was read from."""

    value: str = Field(
        description=(
            "The value as a plain string. Dates as YYYY-MM-DD, money as digits only with no currency symbol or "
            "thousands separator, booleans as true or false, durations as a whole number of months or days."
        )
    )
    quotes: list[str] = Field(
        description=(
            "Verbatim text from the contract supporting this value. Copy the words exactly as they appear, "
            "including any line breaks. Do not paraphrase, summarise, or join text from separate clauses into "
            "one quote."
        )
    )
    conflicting: bool = Field(
        default=False,
        description=(
            "True when the contract states this in more than one place and the statements disagree. Quote every "
            "conflicting passage and set the value to whichever reading appears to govern."
        ),
    )
    note: str = Field(
        default="",
        description="Only when something needs saying, most often what the conflict is between.",
    )


class ContractField(StrEnum):
    """The contract terms an extractor may report. Omit a term it cannot find."""

    AGREEMENT_TYPE = "agreement_type"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    AMENDS = "amends"
    CURRENCY = "currency"
    TOTAL_FIXED_CONSIDERATION = "total_fixed_consideration"
    EFFECTIVE_DATE = "effective_date"
    STATED_TERM_MONTHS = "stated_term_months"
    AUTO_RENEWS = "auto_renews"
    TERMINATION_FOR_CONVENIENCE = "termination_for_convenience"
    TERMINATION_NOTICE_DAYS = "termination_notice_days"
    TERMINATION_COMPENSATION = "termination_compensation"
    NET_DAYS = "net_days"
    BILLING_FREQUENCY = "billing_frequency"
    UPFRONT_FEE = "upfront_fee"
    UPFRONT_FEE_REFUNDABLE = "upfront_fee_refundable"
    PAYMENT_SPREAD_MONTHS = "payment_spread_months"
    RENEWAL_TERM_MONTHS = "renewal_term_months"
    RENEWAL_PRICE = "renewal_price"
    RENEWAL_DESCRIBED_AS_DISCOUNTED = "renewal_described_as_discounted"
    THIRD_PARTY_COMPONENTS = "third_party_components"


# What each term means. Kept beside the enum rather than in the prompt so the
# two cannot drift: this text is what the model is told, and it is also the
# only description of these terms anywhere.
FIELD_GUIDANCE: dict[ContractField, str] = {
    ContractField.AGREEMENT_TYPE: (
        "master_agreement, order_form, statement_of_work, amendment or unknown."
    ),
    ContractField.CUSTOMER: "The legal name of the buying party.",
    ContractField.SUPPLIER: "The legal name of the selling party.",
    ContractField.AMENDS: "For an amendment, the agreement it modifies.",
    ContractField.CURRENCY: "ISO code, e.g. USD.",
    ContractField.TOTAL_FIXED_CONSIDERATION: (
        "Total fixed fees stated in the document. Exclude anything variable."
    ),
    ContractField.EFFECTIVE_DATE: "The date this document takes effect, not the date of one it references.",
    ContractField.STATED_TERM_MONTHS: (
        "The duration the document states, whether or not a termination right makes it look unenforceable."
    ),
    ContractField.AUTO_RENEWS: "Whether the term renews automatically absent notice.",
    ContractField.TERMINATION_FOR_CONVENIENCE: (
        "Whether either party may terminate without cause. Mark conflicting if two clauses disagree."
    ),
    ContractField.TERMINATION_NOTICE_DAYS: "Notice required to terminate without cause.",
    ContractField.TERMINATION_COMPENSATION: (
        "What a terminating party owes, quoted rather than characterised. Whether it is substantive is not "
        "your call."
    ),
    ContractField.NET_DAYS: "Payment terms in days from the invoice date.",
    ContractField.BILLING_FREQUENCY: "e.g. annually in advance, monthly in arrears.",
    ContractField.UPFRONT_FEE: "A fee payable on signing or commencement.",
    ContractField.UPFRONT_FEE_REFUNDABLE: "Whether that upfront fee is refundable.",
    ContractField.PAYMENT_SPREAD_MONTHS: (
        "Where the contract sets out an instalment schedule, months from the first payment to the last. Omit "
        "when fees are simply invoiced in advance on normal net terms."
    ),
    ContractField.RENEWAL_TERM_MONTHS: "Length of a renewal the contract grants an option over.",
    ContractField.RENEWAL_PRICE: "The price stated for that renewal.",
    ContractField.RENEWAL_DESCRIBED_AS_DISCOUNTED: (
        "Whether the document itself frames the renewal price as a discount. Not whether you think it is one."
    ),
    ContractField.THIRD_PARTY_COMPONENTS: (
        "Language about goods or services supplied by an unaffiliated third party."
    ),
}


class FieldClaim(Claim):
    """A claim that names the contract term it is about."""

    field: ContractField


# Zero or one claim, used for the handful of nested fields on an obligation.
# Same reasoning as above: `Claim | None` is a union and unions are capped,
# but there are few enough of them here that the grammar still compiles.
MaybeClaim = list[Claim]


def one(claims: MaybeClaim) -> Claim | None:
    """The single claim, or None. Extra entries are a schema violation, not data."""
    return claims[0] if claims else None


def maybe(claim: Claim | None) -> MaybeClaim:
    """Wrap an optional claim for the wire."""
    return [claim] if claim is not None else []


class WireObligation(BaseModel):
    label: str = Field(description="The promise as the contract names it.")
    kind: ObligationKind
    quotes: list[str] = Field(
        description=(
            "Verbatim text establishing that this promise exists. Required: an obligation whose existence "
            "cannot be pointed at in the document is dropped."
        )
    )
    stated_price: MaybeClaim = []
    list_price: MaybeClaim = Field(
        default=[],
        description="Undiscounted or list rate, only where the document prints one for this item.",
    )
    duration_months: MaybeClaim = []
    recognition: MaybeClaim = Field(
        default=[],
        description=(
            "over_time, point_in_time, or undetermined, based on what the contract says about how control "
            "passes. Use undetermined when it says nothing. Do not infer from the product name."
        ),
    )
    integration_language: MaybeClaim = Field(
        default=[],
        description=(
            "Wording indicating this promise significantly customises, is integrated with, or is highly "
            "interdependent with another. Omit unless the contract actually says something to that effect."
        ),
    )


class WireVariableConsideration(BaseModel):
    kind: VariableConsiderationKind
    description: str
    quotes: list[str] = Field(description="Verbatim text establishing this term.")
    cap: MaybeClaim = Field(default=[], description="Stated ceiling, where the contract sets one.")
    estimable_from_contract: bool = Field(
        default=False,
        description=(
            "True only if the contract itself fixes both the amount and the event that triggers it. False "
            "whenever the amount depends on something outside the document, such as usage or volumes."
        ),
    )


class WireExtraction(BaseModel):
    """Everything an extractor is allowed to say about a contract."""

    fields: list[FieldClaim] = Field(
        default=[],
        description=(
            "One entry per contract term you can find and quote. Omit any term the document does not "
            "address -- an absent entry is a finding, and a wrong one is not."
        ),
    )
    obligations: list[WireObligation] = []
    variable_consideration: list[WireVariableConsideration] = []

    def claim_for(self, field: ContractField) -> Claim | None:
        """The claim for `field`, or None.

        First wins if a term is reported twice. Two entries for one term is not
        how a disagreement gets expressed here (that is what `conflicting` and
        multiple quotes on a single claim are for), so a duplicate is a
        malformed response rather than extra information.
        """
        for claim in self.fields:
            if claim.field is field:
                return claim
        return None
