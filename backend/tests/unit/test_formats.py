"""Parametrized unit tests for shared format validators per docs/15 section 2."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.core.formats import (
    decode_cursor,
    encode_cursor,
    format_money,
    parse_money,
    validate_idempotency_key,
    validate_language,
    validate_phone,
    validate_sku,
    validate_slug,
)


@pytest.mark.parametrize(
    "phone,expected",
    [
        ("+919876543210", "+919876543210"),
        ("+14155552671", "+14155552671"),
        ("+447911123456", "+447911123456"),
    ],
)
def test_valid_phone(phone: str, expected: str) -> None:
    assert validate_phone(phone) == expected


@pytest.mark.parametrize(
    "invalid_phone",
    [
        "9876543210",  # missing leading +
        "+0123456789",  # leading 0 in country code
        "+91 98765 43210",  # unstripped spaces
        "+91",  # too short
        "+919876543210987654",  # too long
        "not-a-phone",
    ],
)
def test_invalid_phone(invalid_phone: str) -> None:
    with pytest.raises(ValueError):
        validate_phone(invalid_phone)


@pytest.mark.parametrize(
    "slug,expected",
    [
        ("my-saree-store", "my-saree-store"),
        ("store123", "store123"),
        ("shree-ganesh-creations", "shree-ganesh-creations"),
        ("UPPER-CASE-STORE", "upper-case-store"),  # normalized to lower()
    ],
)
def test_valid_slug(slug: str, expected: str) -> None:
    assert validate_slug(slug) == expected


@pytest.mark.parametrize(
    "invalid_slug",
    [
        "a",  # too short (< 2 chars)
        "-leading-hyphen",  # cannot start with hyphen
        "has spaces in it",
        "has_underscore",
        "special!chars",
        "a" * 65,  # too long (> 63 chars)
    ],
)
def test_invalid_slug(invalid_slug: str) -> None:
    with pytest.raises(ValueError):
        validate_slug(invalid_slug)


@pytest.mark.parametrize(
    "sku,expected",
    [
        ("SAR-001", "SAR-001"),
        ("PROD_123.A", "PROD_123.A"),
        ("kurtis-xl-red", "kurtis-xl-red"),
        ("10023", "10023"),
    ],
)
def test_valid_sku(sku: str, expected: str) -> None:
    assert validate_sku(sku) == expected


@pytest.mark.parametrize(
    "invalid_sku",
    [
        "",  # empty
        "sku with spaces",
        "sku#123",
        "sku@item",
        "a" * 65,  # too long (> 64 chars)
    ],
)
def test_invalid_sku(invalid_sku: str) -> None:
    with pytest.raises(ValueError):
        validate_sku(invalid_sku)


@pytest.mark.parametrize("lang", ["en", "hi", "mr"])
def test_valid_language(lang: str) -> None:
    assert validate_language(lang) == lang


@pytest.mark.parametrize("invalid_lang", ["fr", "es", "de", "zh", "unknown"])
def test_invalid_language(invalid_lang: str) -> None:
    with pytest.raises(ValueError):
        validate_language(invalid_lang)


@pytest.mark.parametrize(
    "raw,expected_dec,expected_str",
    [
        ("2499.00", Decimal("2499.00"), "2499.00"),
        ("2499", Decimal("2499.00"), "2499.00"),
        (2499, Decimal("2499.00"), "2499.00"),
        ("0.00", Decimal("0.00"), "0.00"),
        ("199.999", Decimal("200.00"), "200.00"),
    ],
)
def test_valid_money(raw: str | int, expected_dec: Decimal, expected_str: str) -> None:
    dec = parse_money(raw)
    assert dec == expected_dec
    assert format_money(dec) == expected_str


@pytest.mark.parametrize("invalid_money", ["-10.00", -50, "-0.01", "not-a-number", 12.34])
def test_invalid_money(invalid_money: str | int | float) -> None:
    with pytest.raises(ValueError):
        parse_money(invalid_money)  # type: ignore


@pytest.mark.parametrize("key", ["12345678", "idem_key_uuid_1234", "req-idem-01HXYZ"])
def test_valid_idempotency_key(key: str) -> None:
    assert validate_idempotency_key(key) == key


@pytest.mark.parametrize("invalid_key", ["short", "a" * 65, "invalid char!", "spaces key"])
def test_invalid_idempotency_key(invalid_key: str) -> None:
    with pytest.raises(ValueError):
        validate_idempotency_key(invalid_key)


def test_cursor_roundtrip() -> None:
    """Cursor encode and decode roundtrip maintains exact timestamp and UUID."""
    now = datetime(2026, 10, 28, 12, 0, 0, tzinfo=timezone.utc)
    item_id = uuid.uuid4()
    cursor = encode_cursor(now, item_id)
    assert isinstance(cursor, str)
    assert "=" not in cursor  # unpadded base64url

    decoded_ts, decoded_id = decode_cursor(cursor)
    assert decoded_ts == now
    assert decoded_id == item_id
