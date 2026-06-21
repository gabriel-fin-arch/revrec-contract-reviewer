"""Whitespace- and typography-insensitive search over the document text.

This exists because of one stubborn fact about PDFs: the sentence a reader sees
as a sentence is stored with hard line breaks in the middle of it. Extracted, the
Helix termination clause comes out as

    "...terminate this Order Form at any time for convenience by giving sixty\\n(60) days' written notice..."

and any quote the extractor returns will have that as a single space. A literal
`in` test fails on every quote longer than a line, which would mean grounding
rejects almost everything and the tool reports an empty contract.

So matching happens against a normalised copy -- whitespace runs collapsed to one
space, case folded, and the typographic variants a PDF renderer emits (curly
quotes, en and em dashes, non-breaking spaces) folded onto their ASCII
equivalents. An index alongside it maps every normalised character back to the
character it came from, so a match found in the normalised text yields offsets
into the *raw* text. Citations therefore always point at real characters in the
document, never at the search copy.

What deliberately isn't here is fuzzy matching. No edit distance, no "close
enough" threshold. The whole value of grounding is that it can say no, and a
matcher that tolerates a few wrong characters tolerates a quote that was never
in the document -- which is precisely the failure it is there to catch.
"""

from __future__ import annotations

# Characters a PDF renderer or a copy-paste round trip is liable to substitute.
# Folding them is not fuzzy matching: each pair is the same character, written
# two ways, and every replacement is exactly one character long so the offset
# map stays one-to-one.
_FOLD = {
    "‘": "'",
    "’": "'",
    "‚": "'",
    "“": '"',
    "”": '"',
    "„": '"',
    "–": "-",
    "—": "-",
    "−": "-",
    " ": " ",
    " ": " ",
    " ": " ",
}


def _fold_char(ch: str, fold_case: bool) -> str:
    folded = _FOLD.get(ch, ch)
    if not fold_case:
        return folded
    lowered = folded.lower()
    # A handful of characters lengthen when lowercased (German sharp s is the
    # one that turns up in practice). Keeping the original preserves the
    # one-character-in, one-character-out property the offset map depends on.
    return lowered if len(lowered) == 1 else folded


class NormalizedText:
    """A searchable view of a document, with a map back to the original offsets.

    `fold_case` is on for grounding, where a quote differing only in case is
    still the same quote. It's off for the rule-based extractor, which needs
    capitalisation to tell a party name from the middle of a sentence -- but
    still wants the line breaks gone, because a regular expression written with
    a space in it does not match a contract that wrapped at that space.
    """

    def __init__(self, raw: str, fold_case: bool = True) -> None:
        self.raw = raw
        self.fold_case = fold_case
        chars: list[str] = []
        offsets: list[int] = []
        at_space = True

        for index, char in enumerate(raw):
            if char.isspace():
                if at_space:
                    continue
                chars.append(" ")
                offsets.append(index)
                at_space = True
            else:
                chars.append(_fold_char(char, fold_case))
                offsets.append(index)
                at_space = False

        self.text = "".join(chars)
        self._offsets = offsets

    @staticmethod
    def normalize(value: str, fold_case: bool = True) -> str:
        """Fold a needle the same way the haystack was folded."""
        return " ".join("".join(_fold_char(ch, fold_case) for ch in value).split())

    def to_raw_span(self, start: int, end: int) -> tuple[int, int]:
        """Translate a span in the normalised text back to raw character offsets."""
        if not self._offsets:
            return 0, 0
        raw_start = self._offsets[start]
        raw_end = self._offsets[end - 1] + 1
        return raw_start, raw_end

    def find_all(self, needle: str, limit: int = 8) -> list[tuple[int, int]]:
        """Every raw-text span where `needle` occurs, up to `limit` of them.

        Returns all of them rather than the first because a quote appearing in
        two places is a signal in its own right: it's how the reviewer finds out
        that the term it just extracted is stated twice, which is the difference
        between an extracted field and an ambiguous one.
        """
        target = self.normalize(needle, self.fold_case)
        if not target:
            return []

        spans: list[tuple[int, int]] = []
        cursor = 0
        while len(spans) < limit:
            hit = self.text.find(target, cursor)
            if hit == -1:
                break
            spans.append(self.to_raw_span(hit, hit + len(target)))
            cursor = hit + 1
        return spans

    def contains(self, needle: str) -> bool:
        return bool(self.find_all(needle, limit=1))
