"""Tests for persistent, signed development sessions."""

import base64
import hashlib
import hmac
import json
from uuid import UUID

import pytest

from app.core.dev_sessions import (
    create_dev_session_token,
    verify_dev_session_token,
)

SECRET = "local-test-signing-secret-with-at-least-32-bytes"


def test_dev_session_round_trip() -> None:
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    business_id = UUID("00000000-0000-0000-0000-000000000002")

    token = create_dev_session_token(user_id, business_id, SECRET)
    claims = verify_dev_session_token(token, SECRET)

    assert claims.user_id == user_id
    assert claims.business_id == business_id
    assert claims.session_version == 0


def test_dev_session_carries_version_and_uses_unique_session_id() -> None:
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    business_id = UUID("00000000-0000-0000-0000-000000000002")

    token = create_dev_session_token(user_id, business_id, SECRET, session_version=4)
    claims = verify_dev_session_token(token, SECRET)

    assert claims.session_version == 4
    assert token != create_dev_session_token(user_id, business_id, SECRET, session_version=4)


def test_dev_session_rejects_tampered_signature() -> None:
    token = create_dev_session_token(
        UUID("00000000-0000-0000-0000-000000000001"),
        UUID("00000000-0000-0000-0000-000000000002"),
        SECRET,
    )
    payload, signature = token.split(".", maxsplit=1)
    replacement = ("A" if signature[0] != "A" else "B") + signature[1:]

    with pytest.raises(ValueError, match="signature"):
        verify_dev_session_token(f"{payload}.{replacement}", SECRET)


def test_dev_session_does_not_expire() -> None:
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    business_id = UUID("00000000-0000-0000-0000-000000000002")
    token = create_dev_session_token(user_id, business_id, SECRET)

    claims = verify_dev_session_token(token, SECRET)

    assert claims.user_id == user_id
    assert claims.business_id == business_id


def test_dev_session_accepts_legacy_signed_token_after_its_expiration() -> None:
    payload = json.dumps(
        {
            "business_id": "00000000-0000-0000-0000-000000000002",
            "expires_at": 1,
            "user_id": "00000000-0000-0000-0000-000000000001",
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
    signature = hmac.new(SECRET.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
    token = f"{encoded_payload}.{signature}"

    claims = verify_dev_session_token(token, SECRET)

    assert claims.user_id == UUID("00000000-0000-0000-0000-000000000001")
    assert claims.business_id == UUID("00000000-0000-0000-0000-000000000002")


def test_dev_session_accepts_token_without_legacy_expiration_claim() -> None:
    payload = json.dumps(
        {
            "business_id": "00000000-0000-0000-0000-000000000002",
            "user_id": "00000000-0000-0000-0000-000000000001",
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
    signature = hmac.new(SECRET.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
    token = f"{encoded_payload}.{signature}"

    claims = verify_dev_session_token(token, SECRET)

    assert claims.user_id == UUID("00000000-0000-0000-0000-000000000001")
    assert claims.business_id == UUID("00000000-0000-0000-0000-000000000002")


def test_dev_session_rejects_expiration_claim_with_wrong_type() -> None:
    payload = json.dumps(
        {
            "business_id": "00000000-0000-0000-0000-000000000002",
            "expires_at": True,
            "user_id": "00000000-0000-0000-0000-000000000001",
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
    signature = hmac.new(SECRET.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
    token = f"{encoded_payload}.{signature}"

    with pytest.raises(ValueError, match="Malformed"):
        verify_dev_session_token(token, SECRET)


def test_dev_session_requires_a_strong_signing_secret() -> None:
    with pytest.raises(ValueError, match="32 bytes"):
        create_dev_session_token(
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            "short",
        )
