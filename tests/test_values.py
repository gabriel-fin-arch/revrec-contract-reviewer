"""Value parsing. Every parser returns None rather than guessing."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from revrec_contract_reviewer.extract.values import (
    parse_bool,
    parse_date,
    parse_decimal,
    parse_enum,
    parse_int,
    parse_str,
)
from revrec_contract_reviewer.models.extraction import AgreementType


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("689000", Decimal("689000")),
        ("USD 689,000", Decimal("689000")),
        ("  1,200,000.50 ", Decimal("1200000.50")),
        ("-2,500", Decimal("-2500")),
        ("about three hundred thousand", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_decimal(raw, expected):
    assert parse_decimal(raw) == expected


def test_a_fractional_term_is_refused_rather_than_rounded():
    """No contract says 24.5 months. Getting one means the wrong number was read,
    and rounding would hide that."""
    assert parse_int("24.5") is None
    assert parse_int("24") == 24


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("true", True), ("YES", True), ("false", False), ("n", False), ("probably", None), (None, None)],
)
def test_parse_bool(raw, expected):
    assert parse_bool(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2025-03-03", date(2025, 3, 3)),
        ("March 3, 2025", date(2025, 3, 3)),
        ("12 June 2025", date(2025, 6, 12)),
        ("sometime in March", None),
    ],
)
def test_parse_date(raw, expected):
    assert parse_date(raw) == expected


def test_parse_str_collapses_whitespace():
    assert parse_str("  Nimbus\n Analytics  ") == "Nimbus Analytics"
    assert parse_str("   ") is None


def test_parse_enum_is_forgiving_about_spelling_not_meaning():
    assert parse_enum("Order Form", AgreementType) is AgreementType.ORDER_FORM
    assert parse_enum("order-form", AgreementType) is AgreementType.ORDER_FORM
    assert parse_enum("purchase requisition", AgreementType) is None
