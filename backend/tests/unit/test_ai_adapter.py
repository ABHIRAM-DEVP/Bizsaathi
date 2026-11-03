"""Unit tests for the AI Model Adapter."""

import json
import logging

import httpx
import pytest
from pydantic import SecretStr

from app.ai import MockModelClient, get_model_client
from app.ai.live import LiveModelClient, redact_pii
from app.core.config import settings
from app.core.errors import ConfigurationError, ExternalServiceError


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


@pytest.mark.anyio
async def test_mock_client_analyze_image():
    client = MockModelClient()
    result = await client.analyze_image(
        image_bytes=b"\x89PNG\r\n\x1a\nfake_image_bytes",
        mime_type="image/png",
        prompt="Analyze product photo",
    )
    assert isinstance(result, dict)
    assert "name" in result
    assert "Mock Handcrafted" in result["name"]


def test_pii_redaction():
    text = "Call me at +919876543210 or email seller@example.com for order details"
    sanitized = redact_pii(text)
    assert "+919876543210" not in sanitized
    assert "seller@example.com" not in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "[REDACTED_EMAIL]" in sanitized


def test_live_client_missing_api_key_raises_config_error(monkeypatch):
    monkeypatch.setattr(settings, "MODEL_API_KEY", SecretStr(""))
    with pytest.raises(ConfigurationError) as exc_info:
        LiveModelClient(api_key=None)
    assert "Reasoning API key is not configured" in str(exc_info.value)


def test_get_model_client_factory(monkeypatch):
    monkeypatch.setattr(settings, "MODEL_PROVIDER", "mock")
    client = get_model_client()
    assert isinstance(client, MockModelClient)

    monkeypatch.setattr(settings, "MODEL_PROVIDER", "live")
    client = get_model_client(timeout_seconds=15, max_retries=0)
    assert isinstance(client, LiveModelClient)
    assert client.timeout == 15
    assert client.max_retries == 0

    monkeypatch.setattr(settings, "MODEL_PROVIDER", "unsupported_provider")
    with pytest.raises(ConfigurationError):
        get_model_client()


def test_live_client_rejects_invalid_endpoint_without_exposing_key():
    api_key = "unit-test-secret"
    with pytest.raises(ConfigurationError) as exc_info:
        LiveModelClient(api_key=api_key, base_url="not-an-absolute-url", model_id="configured-model")
    assert api_key not in str(exc_info.value)


def test_live_client_rejects_api_key_used_as_model_id(monkeypatch):
    api_key = "unit-test-secret-never-use-as-model-id"
    monkeypatch.setattr(settings, "MODEL_API_KEY", SecretStr(api_key))

    with pytest.raises(ConfigurationError) as exc_info:
        LiveModelClient(
            base_url="https://models.example.test/v1",
            model_id=api_key,
        )

    assert api_key not in str(exc_info.value)


@pytest.mark.anyio
async def test_live_client_sends_api_key_without_logging_it(monkeypatch, caplog):
    api_key = "unit-test-secret-never-log"
    monkeypatch.setattr(settings, "MODEL_API_KEY", SecretStr(""))
    requests = []

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, **kwargs):
            requests.append(kwargs)
            if url.endswith("/audio/transcriptions"):
                return httpx.Response(200, json={"text": "Test transcript"})
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": json.dumps({"status": "ok"})}}]},
            )

    monkeypatch.setattr("app.ai.live.httpx.AsyncClient", FakeAsyncClient)
    client = LiveModelClient(
        api_key=api_key,
        base_url="http://127.0.0.1:8000/v1",
        model_id="test-model",
        max_retries=0,
    )

    assert await client.generate_structured("test prompt", {"type": "object"}) == {"status": "ok"}
    assert await client.transcribe(b"test audio") == "Test transcript"
    assert await client.analyze_image(b"fake_bytes", "image/jpeg") == {"status": "ok"}
    assert [request["headers"]["Authorization"] for request in requests] == [
        f"Bearer {api_key}",
        f"Bearer {api_key}",
        f"Bearer {api_key}",
    ]
    assert api_key not in caplog.text
    assert "test-model" not in caplog.text


@pytest.mark.anyio
async def test_live_client_reuses_injected_http_client(caplog):
    requests = []

    class PooledClient:
        async def post(self, url, **kwargs):
            requests.append((url, kwargs))
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"creative_lines":["A lovely everyday choice for you.",'
                                    '"Bring more joy to your special moments."]}'
                                )
                            }
                        }
                    ]
                },
            )

    shared_http_client = PooledClient()
    client = LiveModelClient(
        api_key="unit-test-pooled-secret",
        base_url="http://127.0.0.1:8000/v1",
        model_id="test-model",
        max_retries=0,
        http_client=shared_http_client,
    )

    await client.generate_structured("first prompt", {"type": "object"})
    await client.generate_structured("second prompt", {"type": "object"})

    assert len(requests) == 2
    assert all(request[0].endswith("/chat/completions") for request in requests)
    assert all(request[1]["timeout"] == client.timeout for request in requests)
    assert all(
        request[1]["headers"]["Authorization"] == "Bearer unit-test-pooled-secret"
        for request in requests
    )
    assert "unit-test-pooled-secret" not in caplog.text


@pytest.mark.anyio
async def test_live_client_logs_latency_when_pooled_request_times_out(caplog):
    class TimedOutClient:
        async def post(self, url, **kwargs):
            raise httpx.ReadTimeout("request timed out", request=httpx.Request("POST", url))

    client = LiveModelClient(
        api_key="unit-test-timeout-secret",
        base_url="http://127.0.0.1:8000/v1",
        model_id="test-model",
        timeout_seconds=0.01,
        max_retries=0,
        http_client=TimedOutClient(),
    )

    with pytest.raises(ExternalServiceError, match="timed out after 0.01 seconds") as exc_info:
        await client.generate_structured("test prompt", {"type": "object"})

    assert "unit-test-timeout-secret" not in str(exc_info.value)
    timeout_records = [
        record for record in caplog.records
        if record.name == "bizsaathi.ai.live" and "Model request timed out" in record.getMessage()
    ]
    assert len(timeout_records) == 1
    assert isinstance(timeout_records[0].latency_ms, int)
    assert timeout_records[0].latency_ms >= 0
    assert "unit-test-timeout-secret" not in caplog.text


@pytest.mark.anyio
async def test_live_client_streams_structured_content_with_bounded_output(caplog):
    caplog.set_level(logging.INFO, logger="bizsaathi.ai.live")
    model_content = (
        '{"creative_lines":["A lovely everyday choice for your special moments.",'
        '"Bring a little more joy to the celebrations you share."]}'
    )
    chunks = [model_content[:24], model_content[24:66], model_content[66:]]
    sse_body = "".join(
        "data: "
        + json.dumps({"choices": [{"delta": {"content": chunk}}]})
        + "\n\n"
        for chunk in chunks
    ) + (
        "data: "
        + json.dumps({"choices": [{"delta": {}, "finish_reason": "stop"}]})
        + "\n\n"
        + "data: [DONE]\n\n"
    )
    captured = {}

    async def handler(request):
        captured["payload"] = json.loads(request.content)
        captured["authorization"] = request.headers.get("authorization")
        captured["timeout"] = request.extensions["timeout"]
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=sse_body,
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = LiveModelClient(
            api_key="unit-test-stream-secret",
            base_url="https://models.example.test/v1",
            model_id="test-model",
            timeout_seconds=120,
            max_retries=0,
            disable_read_timeout=True,
            http_client=http_client,
        )
        streamed = [
            chunk async for chunk in client.generate_structured_stream(
                "safe prompt",
                {"type": "object"},
                max_tokens=2048,
            )
        ]

    assert streamed == chunks
    assert captured["payload"]["stream"] is True
    assert captured["payload"]["max_tokens"] == 2048
    assert captured["authorization"] == "Bearer unit-test-stream-secret"
    assert captured["timeout"]["connect"] == 10
    assert captured["timeout"]["read"] is None
    stream_record = next(record for record in caplog.records if record.getMessage() == "Live model stream completed")
    assert isinstance(stream_record.first_token_ms, int)
    assert stream_record.finish_reason == "stop"
    assert stream_record.done_received is True
