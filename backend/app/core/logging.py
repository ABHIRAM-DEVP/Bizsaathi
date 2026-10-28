"""Structured JSON logging and PII / secret redaction per docs/15 section 9 & 14."""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

PHONE_SEARCH_RE = re.compile(r"\+[1-9]\d{7,14}\b")

SENSITIVE_KEYS = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "secret_key",
    "api_key",
    "otp",
    "code",
    "authorization",
    "cookie",
}


def mask_phone(phone: str) -> str:
    """Mask phone string keeping country code and last 2 digits, e.g. +91******21."""
    if phone.startswith("+91") and len(phone) == 13:
        return f"+91******{phone[-2:]}"
    if phone.startswith("+1") and len(phone) == 12:
        return f"+1******{phone[-2:]}"
    m = re.match(r"^(\+[1-9]\d{0,2})\d{4,}(\d{2})$", phone)
    if m:
        return f"{m.group(1)}******{m.group(2)}"
    return phone


def redact_value(key: str, value: Any) -> Any:
    """Redact sensitive fields based on key name or content patterns."""
    if isinstance(key, str) and any(s in key.lower() for s in SENSITIVE_KEYS):
        return "[REDACTED]"
    if isinstance(value, str):
        if PHONE_SEARCH_RE.search(value):
            return PHONE_SEARCH_RE.sub(lambda m: mask_phone(m.group(0)), value)
    return value


def redact_payload(obj: Any) -> Any:
    """Recursively redact dictionary or list payloads."""
    if isinstance(obj, dict):
        return {k: redact_payload(redact_value(k, v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_payload(item) for item in obj]
    return obj


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects per docs/15 section 14."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
        }

        # Contextual metadata injected via extra
        for field in ("request_id", "business_id", "job_id", "node", "duration_ms", "error_code"):
            val = getattr(record, field, None)
            if val is not None:
                log_entry[field] = val

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(redact_payload(log_entry))


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger to output structured JSON."""
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())
    root.addHandler(handler)


logger = logging.getLogger("bizsaathi")
