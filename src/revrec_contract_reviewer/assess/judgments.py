"""Raising the judgment flags.

Each rule below answers one question: does this contract contain a fact that
makes a particular judgment unavoidable? Not "is the judgment likely to go one
way" -- these rules never predict an answer, and the memo never contains one.

Worth being precise about why that isn't timidity. Take the two third-party
arrangements in the corpus. Beacon passes a database licence through at cost,
granted directly by the vendor to the customer, with no warranty; Quarry buys
gateway units into inventory, sets the price, installs them and warrants them.
Every indicator points one way in the first and the other way in the second, and
a tool confident enough to conclude either would eventually meet a third
contract that looked like Beacon and was actually Quarry. The flag is the honest
output; the conclusion belongs to whoever can see how the arrangement operates.

The one number in the whole module is the twelve-month mark for a financing
component, and it is not tuned -- it is the period the standard's own practical
expedient uses.
"""

from __future__ import annotations

from revrec_contract_reviewer.models.citation import Citation
from revrec_contract_reviewer.models.extraction import AgreementType, ContractExtraction, ObligationKind
from revrec_contract_reviewer.models.fields import FieldStatus
from revrec_contract_reviewer.models.judgment import JudgmentFlag, JudgmentType

# ASC 606-10-32-18 lets an entity ignore financing where the gap between
# payment and transfer is a year or less. Above it, the question has to be
# asked. Taken from the standard, not chosen.
FINANCING_EXPEDIENT_MONTHS = 12


def _enforceable_term(extraction: ContractExtraction) -> JudgmentFlag | None:
    field = extraction.term.termination_for_convenience
    if field.status is FieldStatus.ABSENT:
        return None
    # A termination right that exists, or that the document contradicts itself
    # about, both put the stated term in question. An express denial does not.
    if field.status is FieldStatus.EXTRACTED and field.value is False:
        return None

    evidence: list[Citation] = list(field.citations)
    evidence.extend(extraction.term.termination_compensation.citations)

    stated = extraction.term.stated_term_months
    stated_text = f"{stated.value} months" if stated.is_known else "the stated term"

    if field.status is FieldStatus.AMBIGUOUS:
        trigger = (
            "The document addresses termination for convenience in more than one place and the clauses "
            "disagree, so it does not settle whether the customer is committed."
        )
    else:
        compensation = extraction.term.termination_compensation
        if compensation.is_known:
            trigger = (
                "Termination for convenience is available, and what the terminating party owes is: "
                f"{compensation.value}"
            )
        else:
            trigger = (
                "Termination for convenience is available and the document states no compensation for the "
                "unexpired term."
            )

    return JudgmentFlag(
        judgment_type=JudgmentType.ENFORCEABLE_TERM,
        question=(
            f"Is the enforceable term {stated_text}, or does the termination right shorten it to the notice "
            f"period? The transaction price and the allocation both follow from the answer."
        ),
        trigger=trigger,
        evidence=evidence,
    )


def _ssp_not_observable(extraction: ContractExtraction) -> JudgmentFlag | None:
    obligations = extraction.obligations
    if len(obligations) < 2:
        # One obligation, nothing to allocate. This is why the Pinegrove
        # contract produces no flags at all, and why that is correct rather
        # than a gap.
        return None

    evidence: list[Citation] = []
    listed = []
    for obligation in obligations:
        evidence.extend(obligation.evidence[:1])
        if obligation.list_price.is_known:
            listed.append(obligation.label)

    trigger = (
        f"{len(obligations)} performance obligations are sold together, so the transaction price has to be "
        f"allocated between them on relative standalone selling price."
    )
    if listed:
        trigger += (
            f" The document prints a list rate for {len(listed)} of them, which is an input to the estimate "
            f"and not a substitute for it."
        )

    return JudgmentFlag(
        judgment_type=JudgmentType.SSP_NOT_OBSERVABLE,
        question=(
            "What is the standalone selling price of each obligation, and is it directly observable from "
            "separate sales? If not, which estimation approach applies?"
        ),
        trigger=trigger,
        evidence=evidence,
        affects=[ob.label for ob in obligations],
    )


def _material_right(extraction: ContractExtraction) -> JudgmentFlag | None:
    discounted = extraction.renewal.described_as_discounted
    if not discounted.is_known or discounted.value is not True:
        return None

    price = extraction.renewal.renewal_price
    evidence = list(discounted.citations) + list(price.citations)
    priced = f" at {price.value}" if price.is_known else ""

    return JudgmentFlag(
        judgment_type=JudgmentType.MATERIAL_RIGHT,
        question=(
            "Does the renewal option give the customer a material right, requiring part of the transaction "
            "price to be allocated to it and deferred?"
        ),
        trigger=(
            f"The contract grants a renewal{priced} and describes the price as a discount. Whether that "
            f"discount is incremental to the range the entity typically offers is not stated here."
        ),
        evidence=evidence,
    )


def _variable_consideration(extraction: ContractExtraction) -> JudgmentFlag | None:
    terms = extraction.variable_consideration
    if not terms:
        return None

    evidence: list[Citation] = []
    for term in terms:
        evidence.extend(term.evidence[:1])

    kinds = ", ".join(sorted({term.kind.value.replace("_", " ") for term in terms}))
    uncapped = [term for term in terms if not term.cap.is_known]
    trigger = f"The contract contains variable consideration: {kinds}."
    if uncapped:
        trigger += f" {len(uncapped)} of these terms state no ceiling."

    return JudgmentFlag(
        judgment_type=JudgmentType.VARIABLE_CONSIDERATION_CONSTRAINT,
        question=(
            "How much of the variable consideration should be included in the transaction price, and does "
            "the constraint limit it further?"
        ),
        trigger=trigger,
        evidence=evidence,
    )


def _distinct_uncertain(extraction: ContractExtraction) -> JudgmentFlag | None:
    integrated = [ob for ob in extraction.obligations if ob.integration_language.is_known]
    if not integrated:
        return None

    evidence: list[Citation] = []
    for obligation in integrated:
        evidence.extend(obligation.integration_language.citations[:1])

    return JudgmentFlag(
        judgment_type=JudgmentType.DISTINCT_UNCERTAIN,
        question=(
            "Are these promises distinct within the context of the contract, or does the integration between "
            "them make them a single performance obligation?"
        ),
        trigger=(
            "The contract describes these promises as integrated with, customising, or dependent on another: "
            + "; ".join(ob.label for ob in integrated)
        ),
        evidence=evidence,
        affects=[ob.label for ob in integrated],
    )


def _principal_vs_agent(extraction: ContractExtraction) -> JudgmentFlag | None:
    resold = [ob for ob in extraction.obligations if ob.kind is ObligationKind.THIRD_PARTY_RESALE]
    language = extraction.third_party_components
    if not resold and not language.is_known:
        return None

    evidence: list[Citation] = list(language.citations[:1])
    for obligation in resold:
        evidence.extend(obligation.evidence[:1])

    if resold:
        trigger = "The contract includes goods or services supplied by a third party: " + "; ".join(
            ob.label for ob in resold
        )
    else:
        trigger = "The contract describes goods or services supplied by an unaffiliated third party."

    return JudgmentFlag(
        judgment_type=JudgmentType.PRINCIPAL_VS_AGENT,
        question=(
            "Does the entity control the third-party good or service before it transfers to the customer? "
            "Gross revenue if so, net if not."
        ),
        trigger=trigger,
        evidence=evidence,
        affects=[ob.label for ob in resold],
    )


def _significant_financing(extraction: ContractExtraction) -> JudgmentFlag | None:
    spread = extraction.payment.payment_spread_months
    if not spread.is_known or spread.value <= FINANCING_EXPEDIENT_MONTHS:
        return None

    return JudgmentFlag(
        judgment_type=JudgmentType.SIGNIFICANT_FINANCING,
        question=(
            "Do the payment terms convey a significant financing benefit to the customer, and if so at what "
            "discount rate should the consideration be adjusted?"
        ),
        trigger=(
            f"Payment of the fixed consideration is spread over {spread.value} months, beyond the "
            f"{FINANCING_EXPEDIENT_MONTHS}-month practical expedient. A statement in the contract that no "
            f"interest is charged does not answer the question -- it is part of what raises it."
        ),
        evidence=list(spread.citations),
    )


def _contract_modification(extraction: ContractExtraction) -> JudgmentFlag | None:
    agreement_type = extraction.agreement_type
    if not agreement_type.is_known or agreement_type.value is not AgreementType.AMENDMENT:
        return None

    evidence = list(agreement_type.citations[:1]) + list(extraction.amends.citations[:1])
    amended = f" It modifies {extraction.amends.value}." if extraction.amends.is_known else ""

    return JudgmentFlag(
        judgment_type=JudgmentType.CONTRACT_MODIFICATION,
        question=(
            "Is this modification a separate contract, a prospective change to the existing one, or a "
            "cumulative catch-up adjustment?"
        ),
        trigger=(
            f"The document amends an existing agreement rather than standing alone.{amended} It cannot be "
            f"assessed without the agreement it modifies."
        ),
        evidence=evidence,
    )


_RULES = (
    _enforceable_term,
    _contract_modification,
    _distinct_uncertain,
    _material_right,
    _principal_vs_agent,
    _variable_consideration,
    _significant_financing,
    _ssp_not_observable,
)


def raise_flags(extraction: ContractExtraction) -> list[JudgmentFlag]:
    """Every judgment this contract forces, in the order of the five-step model."""
    flags = [flag for rule in _RULES if (flag := rule(extraction)) is not None]
    return sorted(flags, key=lambda flag: flag.step)
