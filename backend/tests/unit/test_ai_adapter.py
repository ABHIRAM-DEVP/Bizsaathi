"""Unit tests for the AI Model Adapter."""

import pytest

from app.ai import MockModelClient, get_model_client
from app.ai.live import LiveModelClient, redact_pii
from app.core.config import settings
from app.core.errors import ConfigurationError


@pytest.mark.anyio
async def test_mock_client_generate_structured():
    client = MockModelClient()
    schema = {
        "type": "object",
        "properties": {
            "sku": {"type": "string"},
            "name": {"type": "string"},
            "price_inr": {"type": "number"},
            "description": {"type": "string"},
        },
        "required": ["sku", "name", "price_inr"],
    }
    result = await client.generate_structured("Extract product info from photo", schema)
    assert result["sku"] == "MOCK-SKU-001"
    assert "Handcrafted" in result["name"]
    assert result["price_inr"] == 499.00
    assert "description" in result


@pytest.mark.anyio
async def test_mock_client_transcribe():
    client = MockModelClient()
    transcription = await client.transcribe(b"dummy_wav_bytes")
    assert isinstance(transcription, str)
    assert len(transcription) > 10
    assert "cotton" in transcription.lower()


@pytest.mark.anyio
async def test_mock_client_generate_image():
    client = MockModelClient()
    img_bytes = await client.generate_image("A beautiful blue shirt")
    assert isinstance(img_bytes, bytes)
    assert img_bytes.startswith(b"\x89PNG")


def test_pii_redaction():
    text = "Call me at +919876543210 or email seller@example.com for order details"
    sanitized = redact_pii(text)
    assert "+919876543210" not in sanitized
    assert "seller@example.com" not in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "[REDACTED_EMAIL]" in sanitized


def test_live_client_missing_api_key_raises_config_error(monkeypatch):
    monkeypatch.setattr(settings, "MODEL_API_KEY", "")
    with pytest.raises(ConfigurationError) as exc_info:
        LiveModelClient(api_key=None)
    assert "MODEL_API_KEY is not configured" in str(exc_info.value)


def test_get_model_client_factory(monkeypatch):
    monkeypatch.setattr(settings, "MODEL_PROVIDER", "mock")
    client = get_model_client()
    assert isinstance(client, MockModelClient)

    monkeypatch.setattr(settings, "MODEL_PROVIDER", "unsupported_provider")
    with pytest.raises(ConfigurationError):
        get_model_client()
