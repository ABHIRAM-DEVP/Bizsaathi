"""Abstract AI Model Adapter interface.

All model interactions flow through this typed adapter.
Default mode is mock; live calls use credentials from environment only.
"""

from abc import ABC, abstractmethod
from typing import Any


class ModelClient(ABC):
    """Abstract interface for AI model capabilities."""

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Generate structured JSON conforming to the given schema."""
        pass

    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/wav",
    ) -> str:
        """Transcribe speech audio into text."""
        pass

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
    ) -> bytes:
        """Generate an image from a descriptive prompt, returning raw image bytes."""
        pass
