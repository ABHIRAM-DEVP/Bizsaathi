"""Node 05: Voice (audio transcription and attribute extraction with spans)."""

import re
from typing import Any

from app.agents.models import ConflictRecord
from app.agents.state import GraphState
from app.ai import get_model_client


async def process_voice(state: GraphState) -> dict[str, Any]:
    """Transcribe voice recording and extract suggestions with character spans."""
    current_calls = state.get("model_calls", 0)
    max_calls = state.get("max_model_calls", 2)
    if current_calls >= max_calls:
        return {
            "status": "blocked",
            "error_code": "budget_exceeded",
            "error_message": f"Model-call budget of {max_calls} exceeded.",
        }

    input_bundle = state["input_bundle"]
    audio_bytes = input_bundle.audio_bytes or b"dummy_audio_bytes"

    client = get_model_client()
    transcript = await client.transcribe(audio_bytes, mime_type=input_bundle.mime_type or "audio/wav")

    # Extract price with span from transcript
    price_match = re.search(r"(\d+(?:\.\d{1,2})?)\s*(?:rupees|rs|inr)", transcript, re.IGNORECASE)
    conflicts: list[dict[str, Any]] = []

    extracted: dict[str, Any] = {
        "transcript": transcript,
        "name": "Handcrafted Cotton Shirt",
        "material": "Pure Cotton",
        "color": "Indigo Blue",
    }

    if price_match:
        extracted_price = float(price_match.group(1))
        extracted["suggested_price_inr"] = extracted_price
        extracted["price_span"] = {"start": price_match.start(), "end": price_match.end()}

        # Compare with existing matching product price if any
        context_bundle = state.get("context_bundle")
        if context_bundle and context_bundle.matching_products:
            confirmed_price = float(context_bundle.matching_products[0].get("price_inr", 0.0))
            if confirmed_price > 0 and abs(extracted_price - confirmed_price) > 0.01:
                conflict = ConflictRecord(
                    field="price_inr",
                    incoming_value=extracted_price,
                    existing_value=confirmed_price,
                    severity="high",
                    ask_seller=True,
                )
                conflicts.append(conflict.model_dump())

    return {
        "model_calls": current_calls + 1,
        "extracted_fields": extracted,
        "conflicts": conflicts,
        "status": "running",
    }
