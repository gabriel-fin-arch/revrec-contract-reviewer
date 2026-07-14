"""Model-based extraction, via the Anthropic API.

One design decision here matters more than the rest: **the model is given the
text this repository extracted, not the PDF.**

Sending the PDF would be the obvious move and it quietly breaks grounding. The
model would read the document through the API's own PDF handling, quote what it
saw there, and those quotes would be checked against pdfplumber's rendering of
the same pages -- a different string, with different line breaks, different
handling of the fee tables, and its own idea of where the footer went. Perfectly
faithful quotes would fail to ground, the fields would drop, and the failure
would look like the model hallucinating. Feeding it the same string grounding
searches removes an entire class of phantom failure.

The cost of that choice is real and worth naming: the model never sees the
layout. A fee table arrives as a run of lines, not as a grid, and anything
carried by position on the page is gone before the model sees it.
"""

from __future__ import annotations

import os

import anthropic

from revrec_contract_reviewer.extract.schema import WireExtraction
from revrec_contract_reviewer.models.document import ContractDocument

DEFAULT_MODEL = "claude-opus-5"

SYSTEM_PROMPT = """You are assisting a group financial controller with an ASC 606 review of contracts \
entered into by subsidiaries of the group. Your job is to read one contract and report what it says. \
It is not to decide the accounting.

Two rules govern everything you return.

First: every value you report must be supported by a verbatim quote from the contract text you were \
given. Copy the words exactly, including line breaks. Do not paraphrase them, do not tidy them, and \
do not stitch together text from clauses that are not adjacent. A quote that does not appear in the \
document causes the value it supports to be discarded, so a shorter quote you are sure of is always \
better than a longer one you have reconstructed.

Second: report only what the document states. If the contract does not address something, omit the \
field rather than inferring a sensible answer from context. Silence is a valid and useful finding. \
Where the contract addresses something in two places and the two disagree, set conflicting to true, \
quote both passages, and say what the conflict is -- do not pick a winner silently.

Some specific guidance, because these are where a careful reader and a hasty one diverge:

- Report the term the document states, even where a termination clause makes that term look \
unenforceable. Both facts are wanted separately.
- Quote termination compensation rather than characterising it. Whether a penalty is substantive is \
not your call.
- A list rate or rate card price is not a standalone selling price. Report it in list_price where the \
document prints one, and never as anything else.
- Mark recognition as undetermined unless the contract says something about how control passes. The \
name of a product is not evidence of a recognition pattern.
- Only report integration_language where the contract actually describes one promise as customising, \
integrating with, or depending on another. Do not supply it because the arrangement looks like it \
might be.
"""

USER_TEMPLATE = """Below is the full text of {doc_id}, as extracted from the PDF. Page breaks are \
marked. Quote from this text exactly as it appears here.

<contract>
{body}
</contract>

Extract the contract's terms."""


def available() -> bool:
    """Whether an API key is present. Absence is a normal state, not an error."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def model_name() -> str:
    return os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL


def _with_page_markers(document: ContractDocument) -> str:
    """The document text, with page boundaries called out.

    The markers are the only thing the model sees that isn't in the string
    grounding searches, and they sit between pages rather than inside them, so
    no quote can span one.
    """
    parts = []
    for page in document.pages:
        parts.append(f"[page {page.number}]\n{page.text}")
    return "\n\n".join(parts)


def extract(document: ContractDocument, client: anthropic.Anthropic | None = None) -> tuple[WireExtraction, str]:
    """Extract `document` with the model. Returns the claims and the model id that produced them."""
    client = client or anthropic.Anthropic()
    model = model_name()

    response = client.messages.parse(
        model=model,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                # The instructions and the schema are identical for every
                # contract in a run; only the document below them changes.
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": USER_TEMPLATE.format(doc_id=document.doc_id, body=_with_page_markers(document)),
            }
        ],
        output_format=WireExtraction,
    )

    return response.parsed_output, model
