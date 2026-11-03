"""Tests for safe, adapter-backed post copy generation."""

import json
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.ai.interface import ModelClient
from app.ai.mock import MockModelClient
from app.core.errors import ConflictError, ExternalServiceError
from app.core.tenancy import AuthContext, require_owner_role
from app.main import app
from app.models.base import get_db
from app.services.post_generation import (
    create_generated_post,
    create_quick_generated_post,
    generate_post_copy,
)


class CapturingModel(ModelClient):
    model_id = "unit-test-model"

    def __init__(self, result):
        self.result = result
        self.prompt = ""
        self.system_prompt = ""
        self.max_tokens = None

    async def generate_structured(self, prompt, schema, system_prompt=None):
        self.prompt = prompt
        self.system_prompt = system_prompt or ""
        return self.result

    async def generate_structured_stream(
        self, prompt, schema, system_prompt=None, *, max_tokens=None
    ):
        self.max_tokens = max_tokens
        yield json.dumps(await self.generate_structured(prompt, schema, system_prompt))

    async def transcribe(self, audio_bytes, mime_type="audio/wav"):
        return ""

    async def generate_image(self, prompt):
        return b""

    async def analyze_image(self, image_bytes, mime_type, prompt="...", schema=None):
        return {}


@pytest.mark.anyio
async def test_generation_uses_seller_description_and_attributes_as_feature_sources(monkeypatch):
    client = CapturingModel(
        {"creative_lines": ["Bring a little more joy to playtime.", "Make room for everyday smiles."]}
    )
    model_options = {}
    monkeypatch.setattr(
        "app.services.post_generation.get_model_client",
        lambda **options: model_options.update(options) or client,
    )

    creative_lines, mode, model_id = await generate_post_copy(
        product_name="Demo Toy",
        channel="instagram",
        language="en",
        product_description="Handwoven cotton scarf in indigo with a lightweight feel.",
        product_attributes={"material": "cotton", "pattern": "indigo"},
    )

    assert creative_lines == ["Bring a little more joy to playtime.", "Make room for everyday smiles."]
    assert mode == "live"
    assert model_id == "unit-test-model"
    assert '"product_name": "Demo Toy"' in client.prompt
    assert '"product_description": "Handwoven cotton scarf in indigo with a lightweight feel."' in client.prompt
    assert '"material": "cotton"' in client.prompt
    assert "seller-provided product description and attributes" in client.system_prompt.lower()
    assert "never infer or invent" in client.system_prompt.lower()
    assert "price" not in client.prompt.lower()
    assert client.max_tokens == 2048
    assert model_options == {
        "timeout_seconds": 120,
        "connect_timeout_seconds": 10,
        "max_retries": 0,
        "disable_read_timeout": True,
    }


@pytest.mark.anyio
async def test_generation_emits_incremental_json_string_snapshots(monkeypatch):
    chunks = [
        '{"creative_lines":["A thoughtful choice with \\',
        '"care\\" in every moment."',
        ',"A beautiful design for special occasions."]}',
    ]

    class ChunkedModel(CapturingModel):
        async def generate_structured_stream(
            self, prompt, schema, system_prompt=None, *, max_tokens=None
        ):
            for chunk in chunks:
                yield chunk

    client = ChunkedModel(
        {
            "creative_lines": [
                'A thoughtful choice with "care" in every moment.',
                "A beautiful design for special occasions.",
            ]
        }
    )
    monkeypatch.setattr("app.services.post_generation.get_model_client", lambda **_options: client)
    updates = []

    creative_lines, _, _ = await generate_post_copy(
        product_name="Demo Toy",
        channel="instagram",
        language="en",
        on_token=lambda index, text: updates.append((index, text)),
    )

    assert creative_lines == [
        'A thoughtful choice with "care" in every moment.',
        "A beautiful design for special occasions.",
    ]
    assert updates
    first_line_updates = [text for index, text in updates if index == 0]
    assert first_line_updates[-1] == creative_lines[0]
    assert all(
        earlier.startswith("A thoughtful choice")
        and later.startswith(earlier)
        for earlier, later in zip(first_line_updates, first_line_updates[1:], strict=False)
    )
    assert any(index == 1 and text == creative_lines[1] for index, text in updates)


@pytest.mark.anyio
async def test_generation_recovers_complete_lines_when_provider_truncates_json_closers(monkeypatch):
    class TruncatedModel(CapturingModel):
        async def generate_structured_stream(
            self, prompt, schema, system_prompt=None, *, max_tokens=None
        ):
            yield (
                '{"creative_lines":["A thoughtful choice for everyday moments.",'
                '"Bring a little more joy to the celebrations you share."'
            )

    client = TruncatedModel({})
    monkeypatch.setattr("app.services.post_generation.get_model_client", lambda **_options: client)

    creative_lines, mode, model_id = await generate_post_copy(
        product_name="Demo Toy",
        channel="instagram",
        language="en",
    )

    assert creative_lines == [
        "A thoughtful choice for everyday moments.",
        "Bring a little more joy to the celebrations you share.",
    ]
    assert mode == "live"
    assert model_id == "unit-test-model"


@pytest.mark.anyio
async def test_generation_reports_empty_model_stream_without_claiming_malformed_json(monkeypatch):
    class EmptyModel(CapturingModel):
        async def generate_structured_stream(
            self, prompt, schema, system_prompt=None, *, max_tokens=None
        ):
            yield ""

    client = EmptyModel({})
    monkeypatch.setattr("app.services.post_generation.get_model_client", lambda **_options: client)

    with pytest.raises(ExternalServiceError, match="ended without post copy") as exc_info:
        await generate_post_copy(product_name="Demo Toy", channel="instagram", language="en")

    assert exc_info.value.status_code == 502


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("language", "language_name"),
    [("hi", "Hindi (हिन्दी)"), ("mr", "Marathi (मराठी)")],
)
async def test_generation_prompt_explicitly_names_requested_language(
    monkeypatch, language, language_name
):
    client = CapturingModel({"creative_lines": ["A suitable creative line.", "Another suitable creative line."]})
    monkeypatch.setattr("app.services.post_generation.get_model_client", lambda **_options: client)

    await generate_post_copy(product_name="Demo Toy", channel="instagram", language=language)

    assert language_name in client.prompt
    assert "Devanagari" in client.prompt
    assert language_name in client.system_prompt


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("language", "expected_hook"),
    [
        ("hi", "हर खेल के पल को खुशियों से भरें।"),
        ("mr", "खेळाचा प्रत्येक क्षण आनंदाने उजळवा."),
    ],
)
async def test_mock_post_hook_uses_requested_language(language, expected_hook):
    import json

    result = await MockModelClient().generate_structured(
        prompt=json.dumps({"language": language}, ensure_ascii=False),
        schema={"type": "object", "properties": {"creative_hook": {"type": "string"}}},
    )

    assert result["creative_hook"] == expected_hook


@pytest.mark.anyio
async def test_mock_post_copy_has_two_lines_in_requested_language():
    import json

    result = await MockModelClient().generate_structured(
        prompt=json.dumps({"language": "hi"}, ensure_ascii=False),
        schema={"type": "object", "properties": {"creative_lines": {"type": "array"}}},
    )

    assert len(result["creative_lines"]) == 2
    assert all(any("\u0900" <= char <= "\u097f" for char in line) for line in result["creative_lines"])


@pytest.mark.anyio
async def test_generation_rejects_malformed_model_output(monkeypatch):
    client = CapturingModel({"creative_lines": [42, "A valid second line."]})
    monkeypatch.setattr("app.services.post_generation.get_model_client", lambda **_options: client)

    with pytest.raises(ExternalServiceError):
        await generate_post_copy(product_name="Demo Toy", channel="instagram", language="en")


class FakeDatabase:
    def __init__(self, product):
        self.product = product
        self.added = []
        self.statements = []

    def execute(self, statement):
        self.statements.append(str(statement))
        return SimpleNamespace(scalar_one_or_none=lambda: self.product)

    def commit(self):
        pass

    def add(self, item):
        self.added.append(item)

    def add_all(self, items):
        self.added.extend(items)

    def flush(self):
        now = datetime.now(timezone.utc)
        for item in self.added:
            if hasattr(item, "created_at") and item.created_at is None:
                item.created_at = now
            if hasattr(item, "updated_at") and item.updated_at is None:
                item.updated_at = now


def make_product(business_id):
    return SimpleNamespace(
        id=uuid4(),
        business_id=business_id,
        name="Demo Toy",
        status="active",
        description="Handwoven cotton scarf in indigo with a lightweight feel.",
        attributes={"material": "cotton", "pattern": "indigo"},
        price_inr=Decimal("349.50"),
        version=3,
    )


@pytest.mark.anyio
async def test_create_generated_post_uses_tenant_catalog_and_links_fact_evidence(monkeypatch):
    business_id = uuid4()
    product = make_product(business_id)
    db = FakeDatabase(product)
    auth = AuthContext(business_id=business_id, user_id=uuid4(), role="owner")

    copy_inputs = []

    async def mock_copy(**kwargs):
        copy_inputs.append(kwargs)
        return (
            ["Make every playtime moment feel a little more magical.", "A thoughtful choice for every day."],
            "mock",
            "mock-model-v1",
        )

    monkeypatch.setattr("app.services.post_generation.generate_post_copy", mock_copy)
    response = await create_generated_post(
        db, auth=auth, product_id=product.id, channel="instagram", language="en"
    )

    assert "product.business_id" in db.statements[0]
    assert response.provenance["mode"] == "mock"
    assert "Demo Toy" in response.text and "349.50" in response.text
    assert len(response.text.splitlines()) == 3
    assert copy_inputs[0]["product_description"] == product.description
    assert copy_inputs[0]["product_attributes"] == product.attributes
    assert [claim.verdict for claim in response.claims] == ["unverified", "supported", "supported"]
    assert all(response.claims[index].evidence_ids for index in (1, 2))
    assert response.claims[0].evidence_ids
    evidence = [item for item in db.added if item.__class__.__name__ == "Evidence"]
    assert len(evidence) == 4
    assert {item.snapshot["field"] for item in evidence} == {
        "name",
        "price_inr",
        "description",
        "attributes",
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("language", "expected_line"),
    [
        ("en", "Bring a little more joy to the moments you share."),
        ("hi", "अपने खास पलों में थोड़ी और खुशी जोड़ें।"),
        ("mr", "तुमच्या खास क्षणांमध्ये आणखी आनंद भरा."),
    ],
)
async def test_quick_post_generates_and_saves_localized_draft_without_model_call(
    monkeypatch, language, expected_line
):
    business_id = uuid4()
    product = make_product(business_id)
    db = FakeDatabase(product)
    auth = AuthContext(business_id=business_id, user_id=uuid4(), role="owner")

    def reject_model_call(**_options):
        raise AssertionError("Quick local drafts must not call a model provider.")

    monkeypatch.setattr("app.services.post_generation.get_model_client", reject_model_call)

    response = await create_quick_generated_post(
        db, auth=auth, product_id=product.id, channel="instagram", language=language
    )

    assert response.provenance["mode"] == "mock"
    assert response.provenance["model_id"] == "quick-local-template-v1"
    assert expected_line in response.text
    assert response.text.endswith("Demo Toy — ₹349.50")
    assert len(response.text.splitlines()) == 3
    assert [claim.verdict for claim in response.claims] == ["unverified", "supported", "supported"]


@pytest.mark.anyio
async def test_create_generated_post_rejects_price_in_unverified_hook(monkeypatch):
    business_id = uuid4()
    product = make_product(business_id)
    db = FakeDatabase(product)
    auth = AuthContext(business_id=business_id, user_id=uuid4(), role="owner")

    async def unsafe_copy(**_kwargs):
        return ["Save 50 rupees today.", "A thoughtful choice for every day."], "mock", "mock-model-v1"

    monkeypatch.setattr("app.services.post_generation.generate_post_copy", unsafe_copy)
    with pytest.raises(ConflictError):
        await create_generated_post(
            db, auth=auth, product_id=product.id, channel="instagram", language="en"
        )
    assert db.added == []


@pytest.mark.anyio
async def test_create_generated_post_rejects_non_owner(monkeypatch):
    business_id = uuid4()
    db = FakeDatabase(make_product(business_id))
    auth = AuthContext(business_id=business_id, user_id=uuid4(), role="operator")

    with pytest.raises(Exception) as exc_info:
        await create_generated_post(
            db, auth=auth, product_id=db.product.id, channel="instagram", language="en"
        )
    assert exc_info.type.__name__ == "ForbiddenError"
    assert db.statements == []


def test_generate_post_api_endpoint_is_reached_without_live_model_call(monkeypatch):
    business_id = uuid4()
    product = make_product(business_id)
    db = FakeDatabase(product)
    auth = AuthContext(business_id=business_id, user_id=uuid4(), role="owner")
    model_calls = []

    async def mock_copy(**kwargs):
        model_calls.append(kwargs)
        assert kwargs["http_client"] is not None
        assert not kwargs["http_client"].is_closed
        return [
            "Make every playtime moment feel a little more magical.",
            "A thoughtful choice for everyday smiles.",
        ], "mock", "mock-model-v1"

    monkeypatch.setattr("app.services.post_generation.generate_post_copy", mock_copy)
    original_db_override = app.dependency_overrides.get(get_db)
    original_auth_override = app.dependency_overrides.get(require_owner_role)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[require_owner_role] = lambda: auth
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/v1/posts/generate/{product.id}",
                json={"channel": "instagram", "language": "en"},
            )
    finally:
        if original_db_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = original_db_override
        if original_auth_override is None:
            app.dependency_overrides.pop(require_owner_role, None)
        else:
            app.dependency_overrides[require_owner_role] = original_auth_override

    assert response.status_code == 201
    assert response.json()["provenance"]["mode"] == "mock"
    assert len(model_calls) == 1


def test_stream_generate_post_endpoint_emits_live_updates_before_validated_post(monkeypatch):
    business_id = uuid4()
    product = make_product(business_id)
    db = FakeDatabase(product)
    auth = AuthContext(business_id=business_id, user_id=uuid4(), role="owner")

    async def mock_copy(**kwargs):
        kwargs["on_token"](0, "A streaming creative suggestion.")
        return [
            "Make every playtime moment feel a little more magical.",
            "A thoughtful choice for everyday smiles.",
        ], "mock", "mock-model-v1"

    monkeypatch.setattr("app.services.post_generation.generate_post_copy", mock_copy)
    original_db_override = app.dependency_overrides.get(get_db)
    original_auth_override = app.dependency_overrides.get(require_owner_role)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[require_owner_role] = lambda: auth
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/v1/posts/generate/{product.id}/stream",
                json={"channel": "instagram", "language": "en"},
            )
    finally:
        if original_db_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = original_db_override
        if original_auth_override is None:
            app.dependency_overrides.pop(require_owner_role, None)
        else:
            app.dependency_overrides[require_owner_role] = original_auth_override

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: status" in response.text
    assert '"line_index": 0' in response.text
    assert "A streaming creative suggestion." in response.text
    assert "event: complete" in response.text
    assert "349.50" in response.text
    assert response.text.index("event: token") < response.text.index("event: complete")


def test_quick_post_endpoint_reaches_service_and_returns_local_template(monkeypatch):
    business_id = uuid4()
    product = make_product(business_id)
    db = FakeDatabase(product)
    auth = AuthContext(business_id=business_id, user_id=uuid4(), role="owner")
    calls = []

    async def quick_copy(_db, **kwargs):
        calls.append(kwargs)
        return await create_quick_generated_post(db, **kwargs)

    monkeypatch.setattr("app.routers.posts.create_quick_generated_post", quick_copy)
    original_db_override = app.dependency_overrides.get(get_db)
    original_auth_override = app.dependency_overrides.get(require_owner_role)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[require_owner_role] = lambda: auth
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/v1/posts/generate/{product.id}/quick",
                json={"channel": "instagram", "language": "en"},
            )
    finally:
        if original_db_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = original_db_override
        if original_auth_override is None:
            app.dependency_overrides.pop(require_owner_role, None)
        else:
            app.dependency_overrides[require_owner_role] = original_auth_override

    assert response.status_code == 201
    assert response.json()["provenance"]["mode"] == "mock"
    assert response.json()["provenance"]["model_id"] == "quick-local-template-v1"
    assert len(calls) == 1
