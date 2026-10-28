"""Unit tests for models and repository structure without requiring a live database."""

from decimal import Decimal
from uuid import uuid4

from app.models.domain import AuditEvent, Business, Job, Media, Product
from app.repositories.product import ProductRepository


def test_business_model_init():
    b = Business(
        name="Test Shop",
        slug="test-shop",
        description="A test shop",
        languages=["en", "hi"],
        status="active",
    )
    assert b.name == "Test Shop"
    assert b.slug == "test-shop"
    assert b.status == "active"
    assert b.languages == ["en", "hi"]


def test_product_model_init():
    p_id = uuid4()
    b_id = uuid4()
    p = Product(
        id=p_id,
        business_id=b_id,
        sku="TEST-SKU-001",
        name="Cotton Shirt",
        price_inr=Decimal("499.00"),
        field_sources={"name": "voice"},
        attributes={"color": "blue"},
        status="active",
        version=1,
    )
    assert p.id == p_id
    assert p.business_id == b_id
    assert p.sku == "TEST-SKU-001"
    assert p.price_inr == Decimal("499.00")
    assert p.version == 1


def test_media_model_init():
    b_id = uuid4()
    m = Media(
        business_id=b_id,
        kind="photo",
        storage_key=f"{b_id}/media/photo1.jpg",
        mime="image/jpeg",
        size_bytes=1024,
        status="pending",
    )
    assert m.business_id == b_id
    assert m.kind == "photo"
    assert m.mime == "image/jpeg"
    assert m.size_bytes == 1024


def test_job_model_init():
    b_id = uuid4()
    j = Job(
        business_id=b_id,
        kind="product_from_photo",
        status="queued",
        progress_step=0,
        progress_total=3,
        max_model_calls=8,
    )
    assert j.business_id == b_id
    assert j.kind == "product_from_photo"
    assert j.status == "queued"
    assert j.max_model_calls == 8


def test_audit_event_model_init():
    b_id = uuid4()
    ae = AuditEvent(
        business_id=b_id,
        actor_type="user",
        actor_id="user-123",
        action="product.created",
        entity_type="product",
        entity_id="prod-123",
        detail={"name": "Cotton Shirt"},
    )
    assert ae.business_id == b_id
    assert ae.actor_type == "user"
    assert ae.action == "product.created"


def test_product_repository_init():
    b_id = uuid4()
    repo = ProductRepository(session=None, business_id=b_id)  # type: ignore
    assert repo._business_id == b_id
