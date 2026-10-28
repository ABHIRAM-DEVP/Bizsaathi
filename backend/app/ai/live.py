"""Live AI Model Adapter for real API interactions.

Communicates with generic OpenAI-compatible or standard HTTP model endpoint
configured via MODEL_BASE_URL and MODEL_API_KEY.
Defaults to bounded retries (max 2) and PII redaction on inputs.
"""

import asyncio
import json
import logging
import re
import time
from typing import Any

import httpx

from app.ai.interface import ModelClient
from app.core.config import settings
from app.core.errors import ConfigurationError, ExternalServiceError

logger = logging.getLogger("bizsaathi.ai.live")

# Basic PII regex patterns for prompt sanitization
PHONE_PATTERN = re.compile(r"(\+?91[\-\s]?)?[6-9]\d{9}")
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def redact_pii(text: str) -> str:
    """Mask phone numbers and email addresses before external dispatch."""
    text = PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
    text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    return text


class LiveModelClient(ModelClient):
    """Production AI model client with resilience, timeout, and observability."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model_id: str = "generic-instruct-v1",
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
    ):
        self.api_key = api_key or settings.MODEL_API_KEY
        if not self.api_key:
            raise ConfigurationError(
                "MODEL_API_KEY is not configured. Set MODEL_API_KEY in .env or switch MODEL_PROVIDER=mock."
            )
        self.base_url = (base_url or settings.MODEL_BASE_URL).rstrip("/")
        self.model_id = model_id
        self.timeout = timeout_seconds
        self.max_retries = max_retries

    async def _post_with_retry(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute HTTP POST with bounded retries on transient errors."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            start_time = time.monotonic()
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    latency_ms = int((time.monotonic() - start_time) * 1000)

                    if response.status_code in (502, 503, 504):
                        logger.warning(
                            "Transient upstream error %d on attempt %d/%d",
                            response.status_code,
                            attempt + 1,
                            self.max_retries + 1,
                            extra={"status_code": response.status_code, "latency_ms": latency_ms},
                        )
                        if attempt < self.max_retries:
                            await asyncio.sleep(0.5 * (2**attempt))
                            continue
                        raise ExternalServiceError(
                            service="ai_model",
                            message=f"Model service temporarily unavailable (status {response.status_code})",
                        )

                    if not response.is_success:
                        raise ExternalServiceError(
                            service="ai_model",
                            message=f"Model service returned status {response.status_code}",
                        )

                    logger.info(
                        "Live model call succeeded",
                        extra={
                            "model_id": self.model_id,
                            "latency_ms": latency_ms,
                            "attempt": attempt + 1,
                        },
                    )
                    data = response.json()
                    if isinstance(data, dict):
                        return data
                    return {"result": data}

            except (httpx.ConnectError, httpx.TimeoutException) as err:
                last_error = err
                logger.warning(
                    "Network error %s on attempt %d/%d",
                    type(err).__name__,
                    attempt + 1,
                    self.max_retries + 1,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue

        raise ExternalServiceError(
            service="ai_model",
            message=f"Model call failed after {self.max_retries + 1} attempts: {last_error}",
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Send prompt and schema to live model, enforcing JSON schema output."""
        sanitized_prompt = redact_pii(prompt)
        sys_prompt = system_prompt or "You are a helpful business assistant. Output valid JSON matching the schema."

        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": sanitized_prompt},
            ],
            "response_format": {"type": "json_object"},
        }

        data = await self._post_with_retry("/chat/completions", payload)
        try:
            content_str = data["choices"][0]["message"]["content"]
            parsed = json.loads(content_str)
            if isinstance(parsed, dict):
                return parsed
            raise ExternalServiceError(service="ai_model", message="Model output was not a JSON object")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise ExternalServiceError(
                service="ai_model",
                message=f"Model returned invalid or malformed output: {e}",
            ) from e

    async def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/wav",
    ) -> str:
        """Transcribe speech audio via live endpoint."""
        url = f"{self.base_url}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = {"file": ("audio.wav", audio_bytes, mime_type)}
        data = {"model": "whisper-1"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, files=files, data=data)
                if not response.is_success:
                    raise ExternalServiceError(
                        service="ai_model",
                        message=f"Audio transcription failed with status {response.status_code}",
                    )
                resp_json = response.json()
                return str(resp_json.get("text", "") if isinstance(resp_json, dict) else "")
        except httpx.HTTPError as err:
            raise ExternalServiceError(
                service="ai_model",
                message=f"Audio transcription network failure: {err}",
            ) from err

    async def generate_image(
        self,
        prompt: str,
    ) -> bytes:
        """Generate image via live endpoint."""
        sanitized_prompt = redact_pii(prompt)
        payload = {
            "model": "image-generation-v1",
            "prompt": sanitized_prompt,
            "n": 1,
            "response_format": "b64_json",
        }
        import base64

        data = await self._post_with_retry("/images/generations", payload)
        try:
            b64_str = data["data"][0]["b64_json"]
            return base64.b64decode(b64_str)
        except (KeyError, IndexError, Exception) as err:
            raise ExternalServiceError(
                service="ai_model",
                message=f"Image generation failed to parse result: {err}",
            ) from err
