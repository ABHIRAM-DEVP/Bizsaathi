"""Unit tests for PII and secret redaction per docs/15 section 9 & 14."""

from app.core.logging import mask_phone, redact_payload


def test_phone_masking() -> None:
    """Phone masking preserves country code and last 2 digits, masking middle digits."""
    assert mask_phone("+919876543210") == "+91******10"
    assert mask_phone("+14155552671") == "+1******71"


def test_payload_redaction() -> None:
    """Redaction recursively masks sensitive keys and phone numbers."""
    payload = {
        "user": {
            "name": "Ramesh",
            "phone": "+919876543210",
            "password": "secret_password_123",
            "token": "bearer-opaque-token",
        },
        "auth": {
            "otp": "123456",
            "secret_key": "supersecret",
            "api_key": "some-key",
        },
        "items": [{"product_name": "Saree", "buyer_phone": "+919123456789"}],
    }

    redacted = redact_payload(payload)

    # Phone is masked
    assert redacted["user"]["phone"] == "+91******10"
    assert redacted["items"][0]["buyer_phone"] == "+91******89"

    # Sensitive keys are masked
    assert redacted["user"]["password"] == "[REDACTED]"
    assert redacted["user"]["token"] == "[REDACTED]"
    assert redacted["auth"]["otp"] == "[REDACTED]"
    assert redacted["auth"]["secret_key"] == "[REDACTED]"
    assert redacted["auth"]["api_key"] == "[REDACTED]"

    # Non-sensitive keys remain unchanged
    assert redacted["user"]["name"] == "Ramesh"
    assert redacted["items"][0]["product_name"] == "Saree"
