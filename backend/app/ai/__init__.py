"""AI Model Adapter package."""

from app.ai.interface import ModelClient
from app.ai.live import LiveModelClient
from app.ai.mock import MockModelClient
from app.core.config import settings
from app.core.errors import ConfigurationError


def get_model_client() -> ModelClient:
    """Return model client based on application configuration."""
    provider = settings.MODEL_PROVIDER.lower()
    if provider == "mock":
        return MockModelClient()
    elif provider in ("live", "openai", "generic"):
        return LiveModelClient()
    else:
        raise ConfigurationError(f"Unsupported MODEL_PROVIDER '{settings.MODEL_PROVIDER}'. Must be 'mock' or 'live'.")


__all__ = [
    "ModelClient",
    "MockModelClient",
    "LiveModelClient",
    "get_model_client",
]
