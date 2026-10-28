"""Model adapter smoke test."""

import asyncio
import sys

from app.ai import get_model_client
from app.core.config import settings


async def main() -> int:
    print(f"=== AI Model Adapter Smoke Test (Provider: {settings.MODEL_PROVIDER}) ===")
    try:
        client = get_model_client()
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "message": {"type": "string"},
            },
            "required": ["status"],
        }
        result = await client.generate_structured(
            prompt="Hello BizSaathi! Verify connectivity.",
            schema=schema,
        )
        print(f"[OK] generate_structured response: {result}")

        # Test transcription
        transcription = await client.transcribe(b"dummy-audio-bytes")
        print(f"[OK] transcribe response: {transcription[:60]}...")

        # Test image generation
        img_bytes = await client.generate_image("Handcrafted blue cotton shirt")
        print(f"[OK] generate_image bytes received: {len(img_bytes)} bytes")

        print("=== Model Adapter Smoke Test PASSED ===")
        return 0
    except Exception as e:
        print(f"[ERROR] Smoke test failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
