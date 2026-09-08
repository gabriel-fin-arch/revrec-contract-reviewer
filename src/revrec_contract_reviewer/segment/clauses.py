"""Split a contract into numbered clauses.

Segmentation earns its place for two reasons, and neither is accuracy of the
final answer -- a citation resolves against the document text, so a clause split
in the wrong place cannot produce a wrong citation.

What it buys is, first, a reference a reviewer recognises: "Section 3.2" is how
people argue about contracts, and a memo that says "p.2, characters 4180-4260"
will not be read by the person who has to sign it. Second, it gives the offline
rule-based extractor somewhere to look, so that a rule about termination can be
scoped to the clause headed "Termination" instead of firing on the word wherever
it appears in the document.
"""

from __future__ import annotations

import re

from revrec_contract_reviewer.models.document import Clause, ContractDocument

# "3." or "3.2." or "12.4.1." at the start of a line, followed by a heading.
# Requires the heading to start with a capital: without that, a paragraph
# beginning "2.5 million events were processed" reads as clause 2.5.
_HEADING = re.compile(r"^(\d+(?:\.\d+)*)\.\s+([A-Z][^\n]{0,80})$", re.MULTILINE)


def segment(document: ContractDocument) -> list[Clause]:
    """Find the clause boundaries in `document` and return them in document order.

    Text before the first numbered heading -- the title block, the parties, the
    recitals -- comes back as a single unnumbered clause rather than being
    dropped. The effective date and the names of the parties live there, and
    they are three of the fields the reviewer needs most.
    """
    text = document.text
    matches = list(_HEADING.finditer(text))

    clauses: list[Clause] = []

    if not matches or matches[0].start() > 0:
        preamble_end = matches[0].start() if matches else len(text)
        preamble = text[:preamble_end]
        if preamble.strip():
            clauses.append(
                Clause(
                    number="",
                    heading="Preamble",
                    text=preamble,
                    start=0,
                    end=preamble_end,
                    page=document.page_for_offset(0),
                )
            )

    for position, match in enumerate(matches):
        start = match.start()
        end = matches[position + 1].start() if position + 1 < len(matches) else len(text)
        clauses.append(
            Clause(
                number=match.group(1),
                heading=match.group(2).strip(),
                text=text[start:end],
                start=start,
                end=end,
                page=document.page_for_offset(start),
            )
        )

    return clauses


def segmented(document: ContractDocument) -> ContractDocument:
    """`document` with its clauses filled in."""
    document.clauses = segment(document)
    return document


def find_clause(document: ContractDocument, *keywords: str) -> Clause | None:
    """First clause whose heading mentions any of `keywords`.

    Used by the offline extractor to scope its rules. Case-insensitive substring
    match on the heading only -- matching the body would defeat the purpose,
    since the body of clause 1 mentions most of the words in the contract.
    """
    lowered = [keyword.lower() for keyword in keywords]
    for clause in document.clauses:
        heading = clause.heading.lower()
        if any(keyword in heading for keyword in lowered):
            return clause
    return None
