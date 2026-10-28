"""Unit tests for Photo to Product Draft extraction and reconciliation (T-202)."""

from uuid import uuid4

import pytest

from app.agents.models import ContextBundle, InputBundle
from app.agents.nodes.node_04_extractor import extract_from_photo
from app.agents.nodes.node_06_reconciler import reconcile_catalog
from app.agents.state import GraphState


@pytest.mark.anyio
async def test_blurry_photo_places_material_in_uncertainty():
    b_id = uuid4()
    state: GraphState = {
        "business_id": b_id,
        "input_bundle": InputBundle(
            kind="product_from_photo",
            storage_keys=["uploads/blurry_photo_sample.jpg"],
        ),
        "model_calls": 0,
        "max_model_calls": 2,
    }

    res = await extract_from_photo(state)
    assert res["status"] == "running"
    uncertainties = res["uncertainties"]
    assert len(uncertainties) > 0
    uncert_fields = [u["field"] for u in uncertainties]
    assert "material" in uncert_fields
    assert uncertainties[0]["ask_seller"] is True
    # Verify material is not claimed as confident
    assert "material" not in res["extracted_fields"]


def test_reconciler_detects_conflict_with_existing_sku():
    b_id = uuid4()
    existing_product = {
        "id": str(uuid4()),
        "sku": "SKU-COTTON-01",
        "name": "Handcrafted Cotton Shirt",
        "price_inr": 499.00,
        "attributes": {"material": "100% Pure Organic Cotton"},
    }

    state: GraphState = {
        "business_id": b_id,
        "extracted_fields": {
            "name": "Handcrafted Cotton Shirt",
            "material": "Synthetic Polyester Blend",
        },
        "context_bundle": ContextBundle(
            matching_products=[existing_product],
            matching_skus=["SKU-COTTON-01"],
        ),
    }

    res = reconcile_catalog(state)
    assert res["status"] == "awaiting_approval"
    conflicts = res["conflicts"]
    assert len(conflicts) > 0
    assert conflicts[0]["field"] == "material"
    assert conflicts[0]["incoming_value"] == "Synthetic Polyester Blend"
    assert conflicts[0]["existing_value"] == "100% Pure Organic Cotton"
    assert conflicts[0]["severity"] == "high"
    assert conflicts[0]["ask_seller"] is True

    # Provenance for fields is marked ai_suggested
    field_sources = res["proposal_payload"]["field_sources"]
    assert field_sources["name"]["source"] == "ai_suggested"
