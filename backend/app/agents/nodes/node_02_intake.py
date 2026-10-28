"""Node 02: Intake (validation of incoming artifacts)."""

from typing import Any

from app.agents.state import GraphState


def process_intake(state: GraphState) -> dict[str, Any]:
    """Validate presence and structure of incoming media or text."""
    input_bundle = state["input_bundle"]

    if input_bundle.kind == "product_from_photo":
        if not input_bundle.media_ids and not input_bundle.storage_keys:
            return {
                "error_code": "intake.missing_photos",
                "error_message": "At least one uploaded photo is required for product_from_photo",
                "status": "failed",
            }
    elif input_bundle.kind == "product_from_voice":
        if not input_bundle.audio_bytes and not input_bundle.media_ids:
            return {
                "error_code": "intake.missing_audio",
                "error_message": "Audio asset or stream is required for product_from_voice",
                "status": "failed",
            }
    elif input_bundle.kind == "post_generate":
        if not input_bundle.raw_text and not input_bundle.media_ids:
            # Need product context or instructions
            pass
    elif input_bundle.kind == "customer_reply":
        if not input_bundle.customer_message:
            return {
                "error_code": "intake.missing_message",
                "error_message": "Customer message is required for customer_reply",
                "status": "failed",
            }
        # Validate language
        if input_bundle.language not in ("en", "hi", "mr"):
            return {
                "error_code": "intake.invalid_language",
                "error_message": f"Language must be one of: en, hi, mr. Got: {input_bundle.language}",
                "status": "failed",
            }

    return {
        "status": "running",
    }
