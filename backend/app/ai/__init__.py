"""AI Model Adapter package."""

import httpx

from app.ai.interface import ModelClient
from app.ai.live import LiveModelClient
from app.ai.mock import MockModelClient
from app.core.config import settings
from app.core.errors import ConfigurationError


def get_model_client(
    *,
    timeout_seconds: float | None = None,
    connect_timeout_seconds: float | None = None,
    max_retries: int | None = None,
    disable_read_timeout: bool = False,
    http_client: httpx.AsyncClient | None = None,
) -> ModelClient:
    """Return model client based on application configuration."""
    provider = settings.MODEL_PROVIDER
    if provider is None:
        provider = "mock" if settings.MODEL_MOCK_MODE else "live"
    if provider == "mock":
        return MockModelClient()
    elif provider in ("live", "openai", "generic"):
        return LiveModelClient(
            timeout_seconds=timeout_seconds or settings.MODEL_REQUEST_TIMEOUT_SECONDS,
            connect_timeout_seconds=connect_timeout_seconds,
            max_retries=settings.MODEL_MAX_RETRIES if max_retries is None else max_retries,
            disable_read_timeout=disable_read_timeout,
            http_client=http_client,
        )
    else:
        raise ConfigurationError(f"Unsupported MODEL_PROVIDER '{settings.MODEL_PROVIDER}'. Must be 'mock' or 'live'.")


__all__ = [
    "ModelClient",
    "MockModelClient",
    "LiveModelClient",
    "get_model_client",
]
