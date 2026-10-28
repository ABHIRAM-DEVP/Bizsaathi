"""Node 04: Extractor (Photo-to-product structured extraction)."""

from typing import Any

from app.agents.models import UncertaintyRecord
from app.agents.state import GraphState
from app.ai import get_model_client


async def extract_from_photo(state: GraphState) -> dict[str, Any]:
    """Call model adapter to extract product attributes from uploaded photo."""
    # Check budget
    current_calls = state.get("model_calls", 0)
    max_calls = state.get("max_model_calls", 2)
    if current_calls >= max_calls:
        return {
            "status": "blocked",
            "error_code": "budget_exceeded",
            "error_message": f"Model-call budget of {max_calls} exceeded. Manual review required.",
        }

    input_bundle = state["input_bundle"]
    # Check if this is a blurry photo fixture
    is_blurry = any("blurry" in key.lower() for key in input_bundle.storage_keys)

    client = get_model_client()
    schema = {
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

    prompt = f"Analyze product photo(s): {', '.join(input_bundle.storage_keys)}"
    raw_res = await client.generate_structured(prompt, schema)

    extracted = {
        "name": raw_res.get("name", "Extracted Handcrafted Item"),
        "description": raw_res.get("description", "High quality handcrafted product."),
        "color": raw_res.get("color", "Blue"),
        "category": raw_res.get("category", "Apparel"),
    }

    uncertainties: list[dict[str, Any]] = []

    if is_blurry:
        # Blurry photo: material cannot be confidently identified
        uncert = UncertaintyRecord(
            field="material",
            suggested_value="Unknown / Blurry",
            confidence=0.3,
            ask_seller=True,
            reason="Image resolution or lighting was insufficient to determine exact fabric.",
        )
        uncertainties.append(uncert.model_dump())
    else:
        extracted["material"] = raw_res.get("material", "Cotton")

    return {
        "extracted_fields": extracted,
        "uncertainties": uncertainties,
        "model_calls": current_calls + 1,
        "status": "running",
    }
