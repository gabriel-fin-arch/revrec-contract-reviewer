"""Turning the strings an extractor returns into typed values.

Every parser here returns None rather than raising or guessing. A value that
can't be parsed is treated exactly like a quote that can't be found: the field
degrades to absent and the drop is counted. "USD 312,000" becoming 312000 is a
convenience; "roughly 300k" becoming anything at all would be an invention.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import TypeVar

E = TypeVar("E", bound=StrEnum)

_MONEY_NOISE = re.compile(r"[^\d.\-]")
_TRUE = {"true", "yes", "y", "1"}
_FALSE = {"false", "no", "n", "0"}

# Formats seen in the corpus. US order forms write "March 3, 2025", the UK and
# European entities write "12 June 2025", and both extractors are asked for ISO.
_DATE_FORMATS = ("%Y-%m-%d", "%B %d, %Y", "%d %B %Y", "%d/%m/%Y", "%m/%d/%Y")


def parse_decimal(raw: str | None) -> Decimal | None:
    if raw is None:
        return None
    cleaned = _MONEY_NOISE.sub("", raw.strip())
    if not cleaned or cleaned in {"-", ".", "-."}:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_int(raw: str | None) -> int | None:
    value = parse_decimal(raw)
    if value is None:
        return None
    # A term of 24.5 months is not something a contract says; if we got one,
    # the extractor has read the wrong number and rounding would hide it.
    if value != value.to_integral_value():
        return None
    return int(value)


def parse_bool(raw: str | None) -> bool | None:
    if raw is None:
        return None
    lowered = raw.strip().lower()
    if lowered in _TRUE:
        return True
    if lowered in _FALSE:
        return False
    return None


def parse_date(raw: str | None) -> date | None:
    if raw is None:
        return None
    candidate = raw.strip()
    for pattern in _DATE_FORMATS:
        try:
            return datetime.strptime(candidate, pattern).date()
        except ValueError:
            continue
    return None


def parse_str(raw: str | None) -> str | None:
    if raw is None:
        return None
    collapsed = " ".join(raw.split())
    return collapsed or None


def parse_enum(raw: str | None, enum_cls: type[E]) -> E | None:
    if raw is None:
        return None
    candidate = raw.strip().lower().replace(" ", "_").replace("-", "_")
    for member in enum_cls:
        if member.value == candidate:
            return member
    return None
