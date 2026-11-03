"""Signed sessions for local development accounts."""

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from uuid import UUID, uuid4

_MIN_SECRET_BYTES = 32


@dataclass(frozen=True)
class DevSessionClaims:
    user_id: UUID
    business_id: UUID
    session_version: int = 0


def _validate_secret(secret: str) -> bytes:
    secret_bytes = secret.encode("utf-8")
    if len(secret_bytes) < _MIN_SECRET_BYTES:
        raise ValueError(f"Development session signing secret must be at least {_MIN_SECRET_BYTES} bytes.")
    return secret_bytes


def create_dev_session_token(
    user_id: UUID | str,
    business_id: UUID | str,
    secret: str,
    session_version: int = 0,
) -> str:
    if not isinstance(session_version, int) or isinstance(session_version, bool) or session_version < 0:
        raise ValueError("Development session version must be a non-negative integer.")
    secret_bytes = _validate_secret(secret)
    payload = json.dumps(
        {
            "business_id": str(UUID(str(business_id))),
            "session_version": session_version,
            "user_id": str(UUID(str(user_id))),
            "session_id": str(uuid4()),
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
    signature = hmac.new(secret_bytes, encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"


def verify_dev_session_token(token: str, secret: str) -> DevSessionClaims:
    secret_bytes = _validate_secret(secret)
    try:
        encoded_payload, signature = token.split(".", maxsplit=1)
        if not encoded_payload or len(signature) != hashlib.sha256().digest_size * 2:
            raise ValueError
        expected_signature = hmac.new(secret_bytes, encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid development session signature.")

        payload_bytes = base64.b64decode(
            encoded_payload + "=" * (-len(encoded_payload) % 4),
            altchars=b"-_",
            validate=True,
        )
        payload = json.loads(payload_bytes)
        legacy_keys = {"business_id", "user_id"}
        legacy_keys_with_expiration = {"business_id", "expires_at", "user_id"}
        current_keys = {"business_id", "session_id", "session_version", "user_id"}
        if not isinstance(payload, dict) or set(payload) not in (
            legacy_keys,
            legacy_keys_with_expiration,
            current_keys,
        ):
            raise ValueError
        if "expires_at" in payload:
            expires_at = payload["expires_at"]
            if not isinstance(expires_at, int) or isinstance(expires_at, bool):
                raise ValueError("Malformed development session token.")
        session_version = payload.get("session_version", 0)
        if not isinstance(session_version, int) or isinstance(session_version, bool) or session_version < 0:
            raise ValueError("Malformed development session token.")
        if "session_id" in payload:
            UUID(payload["session_id"])
        return DevSessionClaims(
            user_id=UUID(payload["user_id"]),
            business_id=UUID(payload["business_id"]),
            session_version=session_version,
        )
    except ValueError:
        raise
    except (AttributeError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("Malformed development session token.") from exc
