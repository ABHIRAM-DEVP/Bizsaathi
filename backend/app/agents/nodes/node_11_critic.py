"""Node 11: independent deterministic cross-modal critic."""

from app.agents.state import GraphState


def critique_consistency(state: GraphState) -> dict[str, object]:
    fields = state.get("extracted_fields", {})
    text = str(fields.get("text", "")).casefold()
    context = state.get("context_bundle")
    product = (context.matching_products or [{}])[0] if context else {}
    color = str(product.get("attributes", {}).get("color", product.get("color", ""))).casefold()
    mismatch = bool(color and color != "green" and "green" in text)
    return {"critique": {"mismatch": mismatch, "severity": "high" if mismatch else "low"}, "status": "running"}
