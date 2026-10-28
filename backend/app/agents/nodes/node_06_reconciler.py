"""Node 06: Reconciler (deterministic catalog reconciliation & proposal generation)."""

from typing import Any
from uuid import uuid4

from app.agents.models import ConflictRecord
from app.agents.state import GraphState


def reconcile_catalog(state: GraphState) -> dict[str, Any]:
    """Reconcile extracted candidate attributes against confirmed catalog facts."""
    if state.get("status") in ("blocked", "failed"):
        return {}

    extracted = state.get("extracted_fields", {})
    context_bundle = state.get("context_bundle")
    uncertainties = state.get("uncertainties", [])

    conflicts: list[dict[str, Any]] = []
    matched_sku: str | None = None

    candidate_name = extracted.get("name", "").strip().lower()

    if context_bundle:
        for p in context_bundle.matching_products:
            existing_name = p.get("name", "").strip().lower()
            if candidate_name and (candidate_name == existing_name or candidate_name in existing_name):
                matched_sku = p.get("sku")
                # Detect field conflicts (e.g. color, material)
                if "attributes" in p and isinstance(p["attributes"], dict):
                    existing_mat = p["attributes"].get("material")
                    candidate_mat = extracted.get("material")
                    if existing_mat and candidate_mat and existing_mat.lower() != candidate_mat.lower():
                        conflict = ConflictRecord(
                            field="material",
                            incoming_value=candidate_mat,
                            existing_value=existing_mat,
                            severity="high",
                            ask_seller=True,
                        )
                        conflicts.append(conflict.model_dump())

    # Build product_draft proposal payload per docs/15 section 6
    # Provenance for each field marked as "ai_suggested"
    field_sources = {k: {"source": "ai_suggested", "confidence": 0.85} for k in extracted.keys()}

    proposal_payload = {
        "type": "product_draft",
        "matched_sku": matched_sku,
        "fields": extracted,
        "field_sources": field_sources,
        "uncertainties": uncertainties,
        "conflicts": conflicts,
        "seller_confirmed_fields": [],  # Empty by default; seller must confirm price and stock
    }

    root_id = uuid4()
    return {
        "conflicts": conflicts,
        "proposal_payload": proposal_payload,
        "proposal_id": root_id,
        "result": {
            "type": "proposal",
            "id": str(root_id),
            "version": 1,
            "proposal_type": "product_draft",
        },
        "status": "awaiting_approval" if conflicts or uncertainties else "succeeded",
    }
