"""Shared scalar format validators, serializers and helpers per docs/15 section 2."""

import base64
import json
import re
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal
from uuid import UUID

PHONE_REGEX = re.compile(r"^\+[1-9][0-9]{7,14}$")
SLUG_REGEX = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
SKU_REGEX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
IDEMPOTENCY_KEY_REGEX = re.compile(r"^[A-Za-z0-9_-]{8,64}$")

SUPPORTED_LANGUAGES = {"en", "hi", "mr"}
LanguageCode = Literal["en", "hi", "mr"]


def validate_phone(phone: str) -> str:
    """Validate and normalize E.164 phone string."""
    cleaned = phone.strip()
    if not PHONE_REGEX.match(cleaned):
        raise ValueError("Invalid phone number. Must be E.164 format (e.g. +919876543210).")
    return cleaned


def validate_slug(slug: str) -> str:
    """Validate url-safe slug."""
    lowered = slug.strip().lower()
    if not SLUG_REGEX.match(lowered):
        raise ValueError(
            "Invalid slug. Must be 2-63 lowercase alphanumeric chars or hyphens, starting with alphanumeric."
        )
    return lowered


def validate_sku(sku: str) -> str:
    """Validate seller SKU."""
    cleaned = sku.strip()
    if not SKU_REGEX.match(cleaned):
        raise ValueError("Invalid SKU. Must be 1-64 alphanumeric chars with optional dot, underscore, or hyphen.")
    return cleaned


def validate_language(lang: str) -> LanguageCode:
    """Validate language against supported languages (en, hi, mr)."""
    cleaned = lang.strip().lower()
    if cleaned not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language '{cleaned}'. Must be one of {sorted(SUPPORTED_LANGUAGES)}.")
    return cleaned  # type: ignore[return-value]


def validate_idempotency_key(key: str) -> str:
    """Validate Idempotency-Key header value."""
    cleaned = key.strip()
    if not IDEMPOTENCY_KEY_REGEX.match(cleaned):
        raise ValueError("Invalid Idempotency-Key. Must be 8-64 alphanumeric characters, underscores, or hyphens.")
    return cleaned


def parse_money(val: str | Decimal | int) -> Decimal:
    """Parse and validate money string into 2-decimal-place non-negative Decimal."""
    if isinstance(val, (int, str)):
        try:
            d = Decimal(str(val))
        except Exception as e:
            raise ValueError(f"Invalid money value '{val}'. Must be a valid numeric string or integer.") from e
    elif isinstance(val, Decimal):
        d = val
    else:
        raise ValueError("Money must be a string or Decimal, never float.")

    if d < Decimal("0.00"):
        raise ValueError("Money cannot be negative.")

    # Quantize to 2 decimal places
    quantized = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return quantized


def format_money(val: Decimal) -> str:
    """Format Decimal into standard 2-decimal-place INR string."""
    return f"{val:.2f}"


def encode_cursor(created_at: datetime, item_id: UUID) -> str:
    """Encode created_at and UUID into an opaque base64url cursor."""
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    payload = {
        "ts": created_at.astimezone(timezone.utc).isoformat(),
        "id": str(item_id),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    """Decode an opaque base64url cursor into (created_at, item_id)."""
    try:
        # Re-add base64 padding
        padding = 4 - (len(cursor) % 4)
        if padding != 4:
            cursor += "=" * padding
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        payload = json.loads(raw.decode("utf-8"))
        ts = datetime.fromisoformat(payload["ts"])
        item_id = UUID(payload["id"])
        return ts, item_id
    except Exception as e:
        raise ValueError(f"Invalid pagination cursor: {e}") from e
