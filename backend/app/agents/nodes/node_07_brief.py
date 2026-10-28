"""Node 07: Brief (creative post brief generation based on confirmed facts)."""

from typing import Any

from app.agents.state import GraphState


def create_brief(state: GraphState) -> dict[str, Any]:
    """Assemble confirmed facts into a strict brief for post drafting."""
    context_bundle = state.get("context_bundle")
    products = context_bundle.matching_products if context_bundle else []
    product = products[0] if products else {}

    channel = state.get("extracted_fields", {}).get("channel", "instagram")

    brief = {
        "channel": channel,
        "product_name": product.get("name", "Handcrafted Product"),
        "price_inr": product.get("price_inr", 0.0),
        "description": product.get("description", ""),
        "policies": context_bundle.policies if context_bundle else [],
    }

    return {
        "extracted_fields": {**state.get("extracted_fields", {}), "brief": brief},
        "status": "running",
    }
