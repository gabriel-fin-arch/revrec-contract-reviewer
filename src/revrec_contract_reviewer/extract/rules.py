"""The offline extractor: regular expressions over conventional contract wording.

Read this as the baseline, not as the product. It works because the corpus is
internally consistent -- every document writes durations as "thirty-six (36)
months", introduces parties as `Full Name ("ShortName")`, and lays fee lines out
as a description followed by a currency code and an amount. Point it at a
contract drafted from anyone else's template and most of it stops firing.

That is the honest argument for the model-based extractor sitting next to it,
and it is a better argument than any benchmark number: the rules don't
generalise because contract language doesn't, and hand-writing a rule per
template is the thing this project exists to avoid.

Two things it is genuinely good for. It makes the repository runnable with no
API key, so anyone can clone it and watch the pipeline work end to end. And it
gives the eval harness a floor -- a model extractor that cannot beat regular
expressions on this corpus is not earning its cost.

Note that it cites. Every claim it makes carries the words it matched and goes
through the same grounding gate as the model. "Nothing is asserted without
evidence" is not a rule about language models.

Everything below runs against a whitespace-collapsed view of the document, with
matches mapped back to raw offsets before they become quotes. Without that, a
pattern containing a space fails wherever the PDF happened to wrap the line, and
which fields a contract appears to contain ends up depending on its typesetting.
"""

from __future__ import annotations

import re

from revrec_contract_reviewer.extract.schema import (
    Claim,
    ContractField,
    FieldClaim,
    WireExtraction,
    WireObligation,
    WireVariableConsideration,
    maybe,
)
from revrec_contract_reviewer.ingest.text import NormalizedText
from revrec_contract_reviewer.models.document import ContractDocument
from revrec_contract_reviewer.models.extraction import (
    AgreementType,
    ObligationKind,
    VariableConsiderationKind,
)

_MONTH = "(?:January|February|March|April|May|June|July|August|September|October|November|December)"
_DATE = rf"(?:{_MONTH} \d{{1,2}}, \d{{4}}|\d{{1,2}} {_MONTH} \d{{4}})"

# Ordered by how strongly the phrasing means "this document's own date". A
# contract's first line is often a reference to *another* agreement's date --
# "Issued under the Master Subscription Agreement dated January 15, 2025" -- so
# a single pattern that accepts "dated" reads the wrong date on every order form
# in the corpus. The specific phrasings are tried first and "dated" is the last
# resort.
_EFFECTIVE_DATE_PATTERNS = [
    re.compile(rf"(?:is )?entered into as of ({_DATE})", re.IGNORECASE),
    re.compile(rf"is made on ({_DATE})", re.IGNORECASE),
    re.compile(rf"\bas of ({_DATE})", re.IGNORECASE),
    re.compile(rf"\bdated ({_DATE})", re.IGNORECASE),
]

# A party is introduced as its full legal name followed by a bracketed short
# name. The capture is a wide window rather than a precise name, because the
# preamble puts arbitrary text in front of it -- a date, an address, the other
# party -- and the window then gets trimmed below. Trying to write the trimming
# into the pattern produced something nobody could read and that still lost
# "Calderwood" off the front of Calderwood Logistics Group.
_PARTY = re.compile(r"([A-Z][^()\"]{3,160}?)\s*\(\"([A-Za-z]+)\"\)")

# Everything before one of these belongs to the sentence, not to the name.
# Order matters: " between " is cut first, and the descriptor is stripped
# between the two cuts. Otherwise "Nimbus Analytics Ltd, a company registered in
# England and Wales" gets cut at its own last " and " and the supplier comes out
# as "Wales".
_NAME_SEPARATORS = (" between ", " and ")
_NAME_LEAD = re.compile(r"^(?:by and between|between|and)\s+", re.IGNORECASE)
# "Nimbus Analytics, Inc., a Delaware corporation with its principal place of
# business at ..." -- the legal name ends where the description of it begins.
_NAME_DESCRIPTOR = re.compile(r",\s+an?\s+[A-Za-z].*$")

_CURRENCY = re.compile(r"\b(USD|GBP|EUR)\b")
_TERM_MONTHS = re.compile(r"(?:term of|continues for|for)\s+[\w\-]+\s+\((\d+)\) months", re.IGNORECASE)
_NET_DAYS = re.compile(
    r"(?:payable within|within|are net)\s+[\w\-]+\s+\((\d+)\) days (?:of|from) the invoice date",
    re.IGNORECASE,
)
_NOTICE_DAYS = re.compile(r"\((\d+)\) days'? written notice", re.IGNORECASE)
_BILLING = re.compile(
    r"invoiced (annually|quarterly|monthly|in full)(?: in (advance|arrears))?",
    re.IGNORECASE,
)
# A duration printed inside a fee line: "Platform subscription, Tier 3 (36
# months)", "Premium Support, 36 months". A perpetual licence has none, which is
# the answer rather than a gap.
_ROW_MONTHS = re.compile(r"(\d+)\s*months?\b", re.IGNORECASE)
_AMENDS = re.compile(r"amends ((?:Order Form|Agreement|Clinical Services Agreement)[^,.]{0,60})", re.IGNORECASE)

# A fee line, once the layout is gone: description, then one or two amounts.
# The second amount is optional because some tables print a list rate alongside
# the agreed fee and some don't. There is deliberately no lookahead asserting
# what follows the row: an earlier version required the next character to start
# a new row, which silently failed on the last line of every table -- so the
# "Total" line, the one row whose value is most load-bearing, was the one row
# that never matched.
_FEE_LINE = re.compile(
    r"(?P<item>[A-Z][^.;]{4,80}?) (?P<cur>USD|GBP|EUR) ?(?P<first>[\d,]+)"
    r"(?: (?:USD|GBP|EUR) ?(?P<second>[\d,]+))?(?![\d,])"
)

# The header row of a fee table, which is the only marker left once the grid is
# flattened into a line of text.
_FEE_HEADER = re.compile(r"\b(?:Item|Milestone) (?:List Rate )?Fee\b")

# Wording that grants a termination right without cause, and wording that denies
# one. Both are searched: a document matching each is not undecided, it is
# contradictory, and that distinction is why FieldStatus has an AMBIGUOUS member.
# The lookbehind matters more than it looks. "Neither party may terminate this
# Order Form for convenience" contains "may terminate ... for convenience"
# verbatim, so without it the clearest denial in the corpus reads as a grant --
# and, because the denial pattern matches the same sentence, the field comes out
# ambiguous rather than merely wrong. A contradiction invented out of one
# unambiguous sentence is worse than a miss: it sends a reviewer to read a
# clause that says exactly what it appears to say.
_TFC_GRANTED = re.compile(
    r"(?<!Neither party )may (?:additionally )?terminate[^.]{0,140}?for convenience", re.IGNORECASE
)
_TFC_DENIED = re.compile(
    r"(?:may not terminate[^.]{0,140}?for convenience"
    r"|has no right to terminate[^.]{0,140}?for convenience"
    r"|no right of termination for convenience"
    r"|Neither party may terminate[^.]{0,140}?for convenience)",
    re.IGNORECASE,
)

_KIND_KEYWORDS: list[tuple[str, ObligationKind]] = [
    ("perpetual licence", ObligationKind.SOFTWARE_LICENSE),
    ("perpetual license", ObligationKind.SOFTWARE_LICENSE),
    ("gateway", ObligationKind.THIRD_PARTY_RESALE),
    ("database licence", ObligationKind.THIRD_PARTY_RESALE),
    ("third party", ObligationKind.THIRD_PARTY_RESALE),
    ("subscription", ObligationKind.SAAS_SUBSCRIPTION),
    ("implementation", ObligationKind.IMPLEMENTATION),
    ("migration", ObligationKind.IMPLEMENTATION),
    ("support", ObligationKind.SUPPORT),
    ("maintenance", ObligationKind.SUPPORT),
    ("training", ObligationKind.TRAINING),
    ("investigator sites", ObligationKind.CLINICAL_SERVICES),
    ("enrolment", ObligationKind.CLINICAL_SERVICES),
    ("database lock", ObligationKind.CLINICAL_SERVICES),
    ("subject", ObligationKind.CLINICAL_SERVICES),
]

_TITLE_TYPES: list[tuple[str, AgreementType]] = [
    ("change order", AgreementType.AMENDMENT),
    ("amendment", AgreementType.AMENDMENT),
    ("order form", AgreementType.ORDER_FORM),
    ("statement of work", AgreementType.STATEMENT_OF_WORK),
    ("master subscription agreement", AgreementType.MASTER_AGREEMENT),
    ("clinical services agreement", AgreementType.MASTER_AGREEMENT),
]


class Reader:
    """A whitespace-collapsed view of one document that can quote itself back in raw text."""

    def __init__(self, document: ContractDocument) -> None:
        self.document = document
        self._view = NormalizedText(document.text, fold_case=False)
        self.text = self._view.text

    def raw(self, start: int, end: int) -> str:
        raw_start, raw_end = self._view.to_raw_span(start, end)
        return self.document.text[raw_start:raw_end]

    def sentence(self, start: int, end: int) -> str:
        """The sentence containing `[start, end)`, returned as raw document text.

        Quotes end up in the memo, and a reviewer checking one against the PDF
        wants a sentence rather than the eleven characters a pattern happened to
        match. Widened to sentence boundaries, then mapped back to the raw text
        so what the memo prints is what the document says, line breaks and all.
        """
        left = self.text.rfind(". ", 0, start)
        left = 0 if left == -1 else left + 2
        right = self.text.find(". ", end)
        right = min(len(self.text), end + 220) if right == -1 else right + 1
        return self.raw(left, right).strip()

    def claim(self, match: re.Match[str], value: str) -> Claim:
        return Claim(value=value, quotes=[self.sentence(match.start(), match.end())])

    def first(self, pattern: re.Pattern[str], group: int = 1) -> Claim | None:
        match = pattern.search(self.text)
        return self.claim(match, match.group(group)) if match else None


def _kind_for(description: str) -> ObligationKind:
    lowered = description.lower()
    for keyword, kind in _KIND_KEYWORDS:
        if keyword in lowered:
            return kind
    return ObligationKind.OTHER


def _agreement_type(reader: Reader) -> Claim | None:
    # The title is the first line. Scanning the whole document for these words
    # would match the recital naming the agreement being amended.
    head = reader.text[:200]
    lowered = head.lower()
    for keyword, agreement_type in _TITLE_TYPES:
        if keyword in lowered:
            return Claim(value=agreement_type.value, quotes=[reader.raw(0, min(110, len(reader.text)))])
    return None


def _trim_party_name(window: str) -> str:
    """Cut a captured preamble window down to the legal name it ends with.

    Right to left: drop everything up to the last connective, then drop the
    description that follows the name. Right to left because the name is
    anchored at the end of the window -- it is the text immediately before the
    bracketed short name -- while what precedes it is unbounded.
    """
    name = window.strip()
    for separator in _NAME_SEPARATORS:
        position = name.rfind(separator)
        if position != -1:
            name = name[position + len(separator) :]
        name = _NAME_DESCRIPTOR.sub("", name).strip(" ,")
    return _NAME_LEAD.sub("", name).strip(" ,")


def _parties(reader: Reader) -> tuple[Claim | None, Claim | None]:
    """Pull the two named parties out of the preamble.

    Keying on the *role* in the bracketed short name rather than on a list of
    known supplier names is what lets this work across the group's entities --
    Nimbus, Nimbus Ltd, Nimbus GmbH and Meridian all get found by the same rule.
    """
    preamble = reader.text[: min(len(reader.text), 1400)]
    customer = supplier = None

    for match in _PARTY.finditer(preamble):
        name = _trim_party_name(match.group(1))
        role = match.group(2).lower()
        quote = reader.sentence(match.start(1), match.end(1))
        if role in {"customer", "sponsor"}:
            customer = customer or Claim(value=name, quotes=[quote])
        elif supplier is None:
            supplier = Claim(value=name, quotes=[quote])

    return customer, supplier


def _effective_date(reader: Reader) -> Claim | None:
    for pattern in _EFFECTIVE_DATE_PATTERNS:
        match = pattern.search(reader.text)
        if match:
            return reader.claim(match, match.group(1))
    return None


def _termination_for_convenience(reader: Reader) -> tuple[Claim | None, Claim | None]:
    granted = _TFC_GRANTED.search(reader.text)
    denied = _TFC_DENIED.search(reader.text)

    notice: Claim | None = None
    if granted:
        window = reader.text[granted.start() : granted.start() + 400]
        found = _NOTICE_DAYS.search(window)
        if found:
            at = granted.start() + found.start()
            notice = Claim(value=found.group(1), quotes=[reader.sentence(at, at + len(found.group(0)))])

    if granted and denied:
        return (
            Claim(
                value="true",
                quotes=[
                    reader.sentence(granted.start(), granted.end()),
                    reader.sentence(denied.start(), denied.end()),
                ],
                conflicting=True,
                note="One clause grants a right to terminate for convenience and another states none is granted.",
            ),
            notice,
        )
    if granted:
        return reader.claim(granted, "true"), notice
    if denied:
        return reader.claim(denied, "false"), None
    return None, None


def _fee_rows(reader: Reader) -> list[tuple[str, str, str | None, re.Match[str]]]:
    """Every parsed fee line inside the fee table: (item, agreed, list, match).

    Scoped to the table rather than run over the whole document, and the scoping
    is what makes the output usable. Prose contains amounts too -- "the balance
    of USD 900,000 in four (4) equal annual instalments of USD 225,000" parses
    as a perfectly good fee line, and taking it produced a performance
    obligation labelled "USD 900,000 in four (4) equal annual i" priced at
    225,000, which is not a promise to the customer and never was.

    Once the layout is gone a table has exactly two landmarks: the header row,
    and the total row that closes it. Reading between them is the whole
    heuristic.
    """
    header = _FEE_HEADER.search(reader.text)
    if header is None:
        return []

    rows: list[tuple[str, str, str | None, re.Match[str]]] = []
    for match in _FEE_LINE.finditer(reader.text, header.end()):
        item = match.group("item").strip()
        first = match.group("first").replace(",", "")
        second = match.group("second")
        if second is None:
            rows.append((item, first, None, match))
        else:
            # Two amounts on one line is a list-rate column followed by the
            # agreed fee. The right-hand number is what the customer pays.
            rows.append((item, second.replace(",", ""), first, match))
        if item.lower().startswith("total"):
            break
    return rows


def _obligations(reader: Reader) -> list[WireObligation]:
    obligations: list[WireObligation] = []
    for item, agreed, listed, match in _fee_rows(reader):
        if item.lower().startswith("total"):
            continue
        # The row itself, not the sentence around it. A fee table contains no
        # full stops, so sentence expansion swallows the entire table and the
        # clause heading after it -- technically a true quote, and useless as
        # evidence for one line of it.
        quote = reader.raw(match.start(), match.end())
        months = _ROW_MONTHS.search(item)
        obligations.append(
            WireObligation(
                label=item,
                kind=_kind_for(item),
                quotes=[quote],
                duration_months=maybe(Claim(value=months.group(1), quotes=[quote]) if months else None),
                stated_price=maybe(Claim(value=agreed, quotes=[quote])),
                list_price=maybe(Claim(value=listed, quotes=[quote]) if listed else None),
                # No recognition claim at all. An earlier version reported
                # UNDETERMINED here, cited to the fee row -- a quote that
                # resolves perfectly and supports nothing, because a line in a
                # price table is not evidence about how control transfers. That
                # is the failure grounding cannot catch: the citation is real,
                # the inference from it is invented. Saying nothing is the
                # honest output, and it lets the check downstream tell
                # "the contract is silent" apart from "nobody read it".
            )
        )
    return obligations


def _total(reader: Reader) -> Claim | None:
    for item, agreed, _listed, match in _fee_rows(reader):
        if item.lower().startswith("total"):
            return Claim(value=agreed, quotes=[reader.raw(match.start(), match.end())])
    return None


_VARIABLE_PATTERNS: list[tuple[re.Pattern[str], VariableConsiderationKind, str]] = [
    (
        re.compile(r"charged at (?:USD|GBP|EUR) ?[\d.,]+ per", re.IGNORECASE),
        VariableConsiderationKind.USAGE_OVERAGE,
        "Usage above the included allowance is charged per unit.",
    ),
    (
        re.compile(r"rebate equal to [\w\-]+ percent", re.IGNORECASE),
        VariableConsiderationKind.VOLUME_REBATE,
        "A rebate is payable if a volume threshold is exceeded.",
    ),
    (
        re.compile(r"entitled to a credit against", re.IGNORECASE),
        VariableConsiderationKind.SERVICE_LEVEL_CREDIT,
        "Service level shortfalls generate credits against future fees.",
    ),
    (
        re.compile(r"shall pay[^.]{0,60}an additional fee of", re.IGNORECASE),
        VariableConsiderationKind.MILESTONE_BONUS,
        "An additional fee is payable if a delivery date is met.",
    ),
    (
        re.compile(r"shall be reduced by (?:USD|GBP|EUR)", re.IGNORECASE),
        VariableConsiderationKind.LATE_DELIVERY_PENALTY,
        "The fee is reduced for each period of delay.",
    ),
    (
        re.compile(r"earned only on achievement of the stated event", re.IGNORECASE),
        VariableConsiderationKind.MILESTONE_BONUS,
        "Fees are earned only on achievement of defined milestones.",
    ),
]


def _variable_consideration(reader: Reader) -> list[WireVariableConsideration]:
    found: list[WireVariableConsideration] = []
    for pattern, kind, description in _VARIABLE_PATTERNS:
        match = pattern.search(reader.text)
        if not match:
            continue
        found.append(
            WireVariableConsideration(
                kind=kind,
                description=description,
                quotes=[reader.sentence(match.start(), match.end())],
                # Never true from a rule. Whether the contract fixes an amount
                # is a reading of the whole clause, and a pattern that matched
                # nine words has not done that reading.
                estimable_from_contract=False,
            )
        )
    return found


_RENEWAL_PRICE = re.compile(r"renew[^.]{0,200}?at a fee of (?:USD|GBP|EUR) ?([\d,]+)", re.IGNORECASE)
_RENEWAL_TERM = re.compile(r"renew[^.]{0,120}?for (?:a further |successive )?[\w\-]+ \((\d+)\) month", re.IGNORECASE)
_RENEWAL_DISCOUNTED = re.compile(r"renewal fee represents a discount|preferential pricing", re.IGNORECASE)
_RENEWAL_AT_LIST = re.compile(r"renews? automatically[^.]{0,160}?then-current published list rate", re.IGNORECASE)

# "the balance of USD 900,000 in four (4) equal annual instalments" -- the only
# instalment wording in the corpus. Deliberately narrow: a rule that guessed a
# schedule from "instalments" alone would have to invent the period.
_ANNUAL_INSTALMENTS = re.compile(r"\((\d+)\) equal annual instalments", re.IGNORECASE)

_THIRD_PARTY = re.compile(
    r"[^.]{0,180}\b(?:unaffiliated third party|an unaffiliated third party|third party)\b[^.]{0,180}\.",
    re.IGNORECASE,
)


def _renewal(reader: Reader) -> tuple[Claim | None, Claim | None, Claim | None]:
    term = reader.first(_RENEWAL_TERM)
    price = None
    price_match = _RENEWAL_PRICE.search(reader.text)
    if price_match:
        price = Claim(
            value=price_match.group(1).replace(",", ""),
            quotes=[reader.sentence(price_match.start(), price_match.end())],
        )

    discounted = None
    # Only ask whether a renewal is discounted once a renewal has been found.
    # Without this guard, "preferential pricing" in the Orchid amendment -- which
    # describes the pricing of the modification itself, and has no renewal
    # anywhere in it -- raised a material right against an option that does not
    # exist. A false positive on a judgment flag costs a reviewer a trip to a
    # clause that isn't there, which is exactly the credibility this is
    # supposed to be building.
    if term is None and price is None:
        return term, price, None

    discount_match = _RENEWAL_DISCOUNTED.search(reader.text)
    if discount_match:
        discounted = Claim(value="true", quotes=[reader.sentence(discount_match.start(), discount_match.end())])
    else:
        at_list = _RENEWAL_AT_LIST.search(reader.text)
        if at_list:
            discounted = Claim(value="false", quotes=[reader.sentence(at_list.start(), at_list.end())])

    return term, price, discounted


def _billing_frequency(reader: Reader) -> Claim | None:
    match = _BILLING.search(reader.text)
    if match is None:
        return None
    cadence = match.group(1).lower()
    timing = match.group(2)
    value = f"{cadence} in {timing.lower()}" if timing else cadence
    return Claim(value=value, quotes=[reader.sentence(match.start(), match.end())])


def _field_claims(**claims: Claim | None) -> list[FieldClaim]:
    """Turn the optional claims the rules produced into the wire's flat list.

    Keyword names are the enum values, so a typo is a KeyError here rather than
    a term that silently never reaches the memo.
    """
    return [
        FieldClaim(
            field=ContractField(name),
            value=claim.value,
            quotes=claim.quotes,
            conflicting=claim.conflicting,
            note=claim.note,
        )
        for name, claim in claims.items()
        if claim is not None
    ]


def extract(document: ContractDocument) -> WireExtraction:
    """Read `document` with rules only. No network, no model, no API key."""
    reader = Reader(document)
    customer, supplier = _parties(reader)
    tfc, notice = _termination_for_convenience(reader)
    renewal_term, renewal_price, renewal_discounted = _renewal(reader)

    spread = None
    instalments = _ANNUAL_INSTALMENTS.search(reader.text)
    if instalments:
        # n annual instalments after an initial payment span n years.
        spread = Claim(
            value=str(int(instalments.group(1)) * 12),
            quotes=[reader.sentence(instalments.start(), instalments.end())],
        )

    third_party = None
    third_party_match = _THIRD_PARTY.search(reader.text)
    if third_party_match:
        quote = reader.sentence(third_party_match.start(), third_party_match.end())
        third_party = Claim(value=" ".join(quote.split())[:300], quotes=[quote])

    return WireExtraction(
        fields=_field_claims(
            agreement_type=_agreement_type(reader),
            customer=customer,
            supplier=supplier,
            amends=reader.first(_AMENDS),
            currency=reader.first(_CURRENCY),
            total_fixed_consideration=_total(reader),
            effective_date=_effective_date(reader),
            stated_term_months=reader.first(_TERM_MONTHS),
            termination_for_convenience=tfc,
            termination_notice_days=notice,
            net_days=reader.first(_NET_DAYS),
            billing_frequency=_billing_frequency(reader),
            payment_spread_months=spread,
            renewal_term_months=renewal_term,
            renewal_price=renewal_price,
            renewal_described_as_discounted=renewal_discounted,
            third_party_components=third_party,
        ),
        obligations=_obligations(reader),
        variable_consideration=_variable_consideration(reader),
    )
