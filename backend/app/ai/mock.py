"""Mock AI Model Adapter for deterministic, zero-cost development and testing."""

import json
import logging
from typing import Any

from app.ai.interface import ModelClient

logger = logging.getLogger("bizsaathi.ai.mock")

# Minimal 1x1 transparent PNG bytes for mock image generation
MOCK_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff"
    b"?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82"
)


class MockModelClient(ModelClient):
    """Deterministic, zero-cost AI model mock client."""

    def __init__(self, model_id: str = "mock-model-v1"):
        self.model_id = model_id

    async def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Return deterministic structured data adhering to requested schema."""
        logger.info(
            "[MOCK] generate_structured invoked",
            extra={
                "model_id": self.model_id,
                "is_mock": True,
                "prompt_len": len(prompt),
                "estimated_tokens": max(1, len(prompt) // 4),
            },
        )

        properties = schema.get("properties", {})
        result: dict[str, Any] = {}
        try:
            prompt_data = json.loads(prompt)
        except json.JSONDecodeError:
            prompt_data = {}
        language = prompt_data.get("language") if isinstance(prompt_data, dict) else None
        localized_post_text = {
            "en": "Make every playtime moment feel a little more magical.",
            "hi": "हर खेल के पल को खुशियों से भरें।",
            "mr": "खेळाचा प्रत्येक क्षण आनंदाने उजळवा.",
        }
        localized_second_line = {
            "en": "Bring home a thoughtful touch for everyday smiles.",
            "hi": "रोज़मर्रा की मुस्कान के लिए एक सुंदर चुनाव करें।",
            "mr": "दररोजच्या हसण्यात माया भरणारी एक खास निवड घ्या.",
        }

        for prop_name, prop_spec in properties.items():
            prop_type = prop_spec.get("type", "string")
            if prop_name == "sku":
                result["sku"] = "MOCK-SKU-001"
            elif prop_name == "name":
                result["name"] = "Mock Handcrafted Cotton Shirt"
            elif prop_name == "creative_hook":
                result[prop_name] = localized_post_text.get(
                    language, localized_post_text["en"]
                )
            elif prop_name == "creative_lines":
                first_line = localized_post_text.get(language, localized_post_text["en"])
                result[prop_name] = [
                    first_line,
                    localized_second_line.get(language, localized_second_line["en"]),
                ]
            elif prop_name == "text" and language in localized_post_text:
                result[prop_name] = localized_post_text[language]
            elif prop_name == "price_inr":
                result["price_inr"] = 499.00
            elif prop_name == "description":
                result["description"] = "A premium quality handcrafted cotton shirt made with organic materials."
            elif prop_name == "status":
                result["status"] = "active"
            elif prop_type == "string":
                result[prop_name] = f"mock_{prop_name}"
            elif prop_type in ("number", "integer"):
                result[prop_name] = 100
            elif prop_type == "boolean":
                result[prop_name] = True
            elif prop_type == "array":
                result[prop_name] = ["mock_item"]
            elif prop_type == "object":
                result[prop_name] = {}
            else:
                result[prop_name] = "mock_value"

        return result

    async def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/wav",
    ) -> str:
        """Return deterministic audio transcription."""
        logger.info(
            "[MOCK] transcribe invoked",
            extra={
                "model_id": self.model_id,
                "is_mock": True,
                "audio_bytes_len": len(audio_bytes),
                "mime_type": mime_type,
            },
        )
        return (
            "Mock audio transcription: Pure cotton round neck shirt in indigo blue, "
            "available in M, L, XL sizes. Price 499 rupees."
        )

    async def generate_image(
        self,
        prompt: str,
    ) -> bytes:
        """Return deterministic 1x1 image bytes."""
        logger.info(
            "[MOCK] generate_image invoked",
            extra={
                "model_id": self.model_id,
                "is_mock": True,
                "prompt_len": len(prompt),
            },
        )
        return MOCK_PNG_BYTES

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str = "Analyze this product image and extract its attributes.",
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return deterministic structured product extraction from image bytes."""
        logger.info(
            "[MOCK] analyze_image invoked",
            extra={
                "model_id": self.model_id,
                "is_mock": True,
                "image_bytes_len": len(image_bytes),
                "mime_type": mime_type,
            },
        )
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
        return await self.generate_structured(prompt, extraction_schema)
