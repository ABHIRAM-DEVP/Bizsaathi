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

@pytest.mark.anyio
async def test_photo_reads_image_bytes_from_disk_and_analyzes(tmp_path, monkeypatch):
    from app.ai.interface import ModelClient
    from app.core.config import settings

    monkeypatch.setattr(settings, "MEDIA_STORAGE_PATH", str(tmp_path))

    rel_path = "uploads/2026/11/sample.png"
    target_file = tmp_path / rel_path
    target_file.parent.mkdir(parents=True, exist_ok=True)
    sample_bytes = b"\x89PNG\r\n\x1a\nfake_image_content_12345"
    target_file.write_bytes(sample_bytes)

    received_bytes = []
    received_mime = []

    class SpyClient(ModelClient):
        async def generate_structured(self, prompt, schema, system_prompt=None):
            return {}
        async def transcribe(self, audio_bytes, mime_type="audio/wav"):
            return ""
        async def generate_image(self, prompt):
            return b""
        async def analyze_image(self, image_bytes, mime_type, prompt="...", schema=None):
            received_bytes.append(image_bytes)
            received_mime.append(mime_type)
            return {
                "name": "Handmade Silk Scarf",
                "description": "Pure silk handcrafted scarf.",
                "color": "Red",
                "category": "Accessories",
                "material": "Silk",
            }

    monkeypatch.setattr("app.agents.nodes.node_04_extractor.get_model_client", lambda: SpyClient())

    b_id = uuid4()
    state: GraphState = {
        "business_id": b_id,
        "input_bundle": InputBundle(
            kind="product_from_photo",
            storage_keys=[rel_path],
        ),
        "model_calls": 0,
        "max_model_calls": 2,
    }

    res = await extract_from_photo(state)
    assert res["status"] == "running"
    assert res["extracted_fields"]["name"] == "Handmade Silk Scarf"
    assert res["extracted_fields"]["material"] == "Silk"
    assert len(received_bytes) == 1
    assert received_bytes[0] == sample_bytes
    assert received_mime[0] == "image/png"


@pytest.mark.anyio
async def test_live_photo_extraction_blocks_when_uploaded_image_is_missing(tmp_path, monkeypatch):
    from app.ai.interface import ModelClient
    from app.core.config import settings

    monkeypatch.setattr(settings, "MEDIA_STORAGE_PATH", str(tmp_path))
    monkeypatch.setattr(settings, "MODEL_MOCK_MODE", False)
    monkeypatch.setattr(settings, "MODEL_PROVIDER", "live")

    class SpyClient(ModelClient):
        async def generate_structured(self, prompt, schema, system_prompt=None):
            return {}
        async def transcribe(self, audio_bytes, mime_type="audio/wav"):
            return ""
        async def generate_image(self, prompt):
            return b""
        async def analyze_image(self, image_bytes, mime_type, prompt="...", schema=None):
            pytest.fail("Live image analysis must not receive placeholder bytes")

    monkeypatch.setattr("app.agents.nodes.node_04_extractor.get_model_client", lambda: SpyClient())

    state: GraphState = {
        "business_id": uuid4(),
        "input_bundle": InputBundle(
            kind="product_from_photo",
            storage_keys=["uploads/2026/11/missing.jpg"],
        ),
        "model_calls": 0,
        "max_model_calls": 2,
    }

    res = await extract_from_photo(state)
    assert res["status"] == "blocked"
    assert res["error_code"] == "image_unavailable"
