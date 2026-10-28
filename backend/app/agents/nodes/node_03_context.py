"""Node 03: Context (deterministic context retrieval)."""

from typing import Any

from app.agents.models import ContextBundle
from app.agents.state import GraphState


def gather_context(state: GraphState) -> dict[str, Any]:
    """Gather policies and matching catalog items for tenant."""
    # Existing context bundle from state or fresh
    existing_cb = state.get("context_bundle")
    if existing_cb is not None and (existing_cb.policies or existing_cb.matching_products):
        return {"context_bundle": existing_cb}

    context = ContextBundle(
        matching_products=[],
        matching_skus=[],
        policies=[
            {"kind": "delivery", "body": "Standard shipping 3-5 days across India."},
            {"kind": "returns", "body": "7-day easy returns on unused apparel."},
        ],
    )
    return {
        "context_bundle": context,
        "status": "running",
    }
