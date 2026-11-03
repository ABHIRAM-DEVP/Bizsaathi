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
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any
from urllib.parse import urlsplit

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
        model_id: str | None = None,
        timeout_seconds: float | None = None,
        connect_timeout_seconds: float | None = None,
        max_retries: int | None = None,
        disable_read_timeout: bool = False,
        http_client: httpx.AsyncClient | None = None,
    ):
        configured_key = settings.MODEL_API_KEY.get_secret_value()
        self.api_key = api_key if api_key is not None else configured_key
        if not self.api_key:
            raise ConfigurationError(
                "Reasoning API key is not configured. Set REASONING_API_KEY in the server environment."
            )

        self.base_url = (base_url or settings.MODEL_BASE_URL).rstrip("/")
        parsed_url = urlsplit(self.base_url)
        is_local_http = parsed_url.scheme == "http" and parsed_url.hostname in ("localhost", "127.0.0.1", "::1")
        if not parsed_url.hostname or (parsed_url.scheme != "https" and not is_local_http):
            raise ConfigurationError(
                "MODEL_API_BASE_URL must be an absolute HTTPS endpoint "
                "(HTTP is allowed for localhost)."
            )

        self.model_id = model_id or settings.MODEL_ID
        if not self.model_id:
            raise ConfigurationError("REASONING_MODEL is not configured in the server environment.")
        if self.model_id == self.api_key:
            raise ConfigurationError("MODEL_ID must be a model identifier, not the configured API key.")
        self.timeout = timeout_seconds or settings.MODEL_REQUEST_TIMEOUT_SECONDS
        self.connect_timeout = connect_timeout_seconds or min(10.0, self.timeout)
        self.max_retries = settings.MODEL_MAX_RETRIES if max_retries is None else max_retries
        self.disable_read_timeout = disable_read_timeout
        self.http_client = http_client

    @property
    def request_timeout(self) -> httpx.Timeout:
        return httpx.Timeout(
            self.timeout,
            connect=self.connect_timeout,
            read=None if self.disable_read_timeout else self.timeout,
            write=min(10.0, self.timeout),
            pool=min(10.0, self.timeout),
        )

    @asynccontextmanager
    async def _open_stream(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> AsyncGenerator[httpx.Response, None]:
        if self.http_client is not None:
            async with self.http_client.stream(
                "POST",
                url,
                json=payload,
                headers=headers,
                timeout=self.request_timeout,
            ) as response:
                yield response
            return

        async with httpx.AsyncClient(timeout=self.request_timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                yield response

    async def _post_with_retry(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute HTTP POST with bounded retries on transient errors."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(self.max_retries + 1):
            start_time = time.monotonic()
            try:
                timeout: float | httpx.Timeout = (
                    self.request_timeout if self.disable_read_timeout else self.timeout
                )
                if self.http_client is None:
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        response = await client.post(url, json=payload, headers=headers)
                else:
                    response = await self.http_client.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=timeout,
                    )

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
                        "latency_ms": latency_ms,
                        "attempt": attempt + 1,
                    },
                )
                data = response.json()
                if isinstance(data, dict):
                    return data
                return {"result": data}

            except httpx.TimeoutException as err:
                latency_ms = int((time.monotonic() - start_time) * 1000)
                logger.warning(
                    "Model request timed out, attempt %d/%d",
                    attempt + 1,
                    self.max_retries + 1,
                    extra={"latency_ms": latency_ms},
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                message = (
                    "Model provider connection or request transmission timed out."
                    if self.disable_read_timeout
                    else f"Model provider timed out after {self.timeout:g} seconds."
                )
                raise ExternalServiceError(service="ai_model", message=message) from err
            except httpx.ConnectError as err:
                latency_ms = int((time.monotonic() - start_time) * 1000)
                logger.warning(
                    "Could not connect to model provider, attempt %d/%d",
                    attempt + 1,
                    self.max_retries + 1,
                    extra={"latency_ms": latency_ms},
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                raise ExternalServiceError(
                    service="ai_model",
                    message="Could not connect to the model provider.",
                ) from err

        raise ExternalServiceError(
            service="ai_model",
            message=f"Model call failed after {self.max_retries + 1} attempts.",
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
        sys_prompt = f"{sys_prompt} JSON schema: {json.dumps(schema, separators=(',', ':'))}"

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
                message="Model returned invalid or malformed structured output.",
            ) from e

    async def generate_structured_stream(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None = None,
        *,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Yield content deltas from an OpenAI-compatible SSE chat completion."""
        sanitized_prompt = redact_pii(prompt)
        sys_prompt = system_prompt or "You are a helpful business assistant. Output valid JSON matching the schema."
        sys_prompt = f"{sys_prompt} JSON schema: {json.dumps(schema, separators=(',', ':'))}"
        payload: dict[str, Any] = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": sanitized_prompt},
            ],
            "response_format": {"type": "json_object"},
            "stream": True,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        url = f"{self.base_url}/chat/completions"
        started = time.monotonic()
        first_token_ms: int | None = None
        token_count = 0
        finish_reason: str | None = None
        done_received = False

        try:
            async with self._open_stream(url, payload, headers) as response:
                if not response.is_success:
                    raise ExternalServiceError(
                        service="ai_model",
                        message=f"Model service returned status {response.status_code}",
                    )

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        done_received = True
                        break
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError as err:
                        raise ExternalServiceError(
                            service="ai_model",
                            message="Model stream returned malformed event data.",
                        ) from err
                    if not isinstance(event, dict):
                        raise ExternalServiceError(
                            service="ai_model",
                            message="Model stream returned malformed event data.",
                        )
                    choices = event.get("choices")
                    if (
                        not isinstance(choices, list)
                        or not choices
                        or not isinstance(choices[0], dict)
                    ):
                        continue
                    choice = choices[0]
                    reason = choice.get("finish_reason")
                    if isinstance(reason, str):
                        finish_reason = reason
                    delta_value = choice.get("delta")
                    if not isinstance(delta_value, dict):
                        continue
                    delta = delta_value.get("content")
                    if not isinstance(delta, str) or not delta:
                        continue
                    if first_token_ms is None:
                        first_token_ms = int((time.monotonic() - started) * 1000)
                    token_count += len(delta)
                    yield delta
        except httpx.TimeoutException as err:
            latency_ms = int((time.monotonic() - started) * 1000)
            logger.warning(
                "Model stream timed out",
                extra={
                    "model_id": self.model_id,
                    "latency_ms": latency_ms,
                    "first_token_ms": first_token_ms,
                },
            )
            message = (
                "Model provider connection or request transmission timed out."
                if self.disable_read_timeout
                else f"Model provider timed out after {self.timeout:g} seconds."
            )
            raise ExternalServiceError(service="ai_model", message=message) from err
        except httpx.ConnectError as err:
            latency_ms = int((time.monotonic() - started) * 1000)
            logger.warning(
                "Could not connect to model provider for stream",
                extra={"model_id": self.model_id, "latency_ms": latency_ms},
            )
            raise ExternalServiceError(
                service="ai_model",
                message="Could not connect to the model provider.",
            ) from err

        log_stream_end = logger.warning if finish_reason == "length" or token_count == 0 else logger.info
        log_stream_end(
            "Live model stream completed",
            extra={
                "model_id": self.model_id,
                "latency_ms": int((time.monotonic() - started) * 1000),
                "first_token_ms": first_token_ms,
                "output_chars": token_count,
                "attempt": 1,
                "finish_reason": finish_reason,
                "done_received": done_received,
            },
        )

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

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str = "Analyze this product image and extract its attributes.",
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send base64-encoded image bytes with structured schema to multimodal model."""
        import base64

        sanitized_prompt = redact_pii(prompt)
        extraction_schema = schema or {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "color": {"type": "string"},
                "category": {"type": "string"},
                "material": {"type": "string"},
            },
            "required": ["name"],
        }
        sys_prompt = (
            "You are an expert product catalog assistant. "
            "Examine the product photo and output valid JSON conforming strictly to the schema. "
            f"JSON schema: {json.dumps(extraction_schema, separators=(',', ':'))}"
        )
        b64_img = base64.b64encode(image_bytes).decode("ascii")
        data_uri = f"data:{mime_type};base64,{b64_img}"

        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": sanitized_prompt},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                },
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
                message="Model returned invalid or malformed structured output.",
            ) from e

