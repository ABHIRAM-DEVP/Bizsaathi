"""Abstract AI Model Adapter interface.

All model interactions flow through this typed adapter.
Default mode is mock; live calls use credentials from environment only.
"""

import json
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
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

    async def generate_structured_stream(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None = None,
        *,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Yield structured model output; non-streaming adapters provide one chunk."""
        result = await self.generate_structured(prompt, schema, system_prompt)
        yield json.dumps(result, ensure_ascii=False)

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

    @abstractmethod
    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str = "Analyze this product image and extract its attributes.",
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Analyze image bytes and return structured product attribute extraction.

        Args:
            image_bytes: Raw image bytes (JPEG, PNG, or WebP).
            mime_type: MIME type of the image (e.g. 'image/jpeg').
            prompt: Instruction for the model.
            schema: Optional JSON schema the response must conform to.

        Returns:
            Structured dict with extracted product attributes.
        """
        pass
