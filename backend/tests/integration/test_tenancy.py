"""Integration tests verifying multi-tenant isolation.

Negative tests required: Tenant B cannot read, update, or archive Tenant A's products.
"""

from decimal import Decimal
from uuid import uuid4

from app.models.domain import AuditEvent, Business
from app.repositories.product import ProductRepository


def test_tenant_isolation_product_crud(db_session):
    # Setup two businesses
    b1_id = uuid4()
    b2_id = uuid4()

    b1 = Business(id=b1_id, name="Tenant One", slug=f"tenant-one-{b1_id.hex[:6]}")
    b2 = Business(id=b2_id, name="Tenant Two", slug=f"tenant-two-{b2_id.hex[:6]}")
    db_session.add_all([b1, b2])
    db_session.flush()

    repo1 = ProductRepository(session=db_session, business_id=b1_id)
    repo2 = ProductRepository(session=db_session, business_id=b2_id)

    # Tenant 1 creates product
    p1 = repo1.create(sku="SKU-SHARED", name="Product One", price_inr=Decimal("199.00"))
    assert p1.id is not None

    # Tenant 2 cannot see Tenant 1's product by ID
    p_cross = repo2.get_by_id(p1.id)
    assert p_cross is None, "Tenant B must NOT access Tenant A's product by ID"

    # Tenant 2 can create their OWN product with the SAME SKU
    p2 = repo2.create(sku="SKU-SHARED", name="Product Two", price_inr=Decimal("299.00"))
    assert p2.id != p1.id

    # Tenant 2 cannot update Tenant 1's product price
    stale_res = repo2.update_price(p1.id, Decimal("999.00"), expected_version=1)
    assert stale_res is None, "Tenant B must NOT update Tenant A's product"

    # Tenant 2 cannot archive Tenant 1's product
    archived = repo2.archive(p1.id)
    assert archived is False, "Tenant B must NOT archive Tenant A's product"

    # Verify Tenant 1 product is untouched
    p1_check = repo1.get_by_id(p1.id)
    assert p1_check is not None
    assert p1_check.price_inr == Decimal("199.00")
    assert p1_check.status == "active"


def test_audit_event_carries_business_id_and_actor(db_session):
    b_id = uuid4()
    b = Business(id=b_id, name="Audit Shop", slug=f"audit-shop-{b_id.hex[:6]}")
    db_session.add(b)
    db_session.flush()

    ae = AuditEvent(
        business_id=b_id,
        actor_type="user",
        actor_id="user-456",
        action="product.price_updated",
        entity_type="product",
        entity_id="prod-123",
        detail={"old_price": "100.00", "new_price": "150.00"},
        request_id="req-abc",
    )
    db_session.add(ae)
    db_session.flush()

    assert ae.id is not None
    assert ae.business_id == b_id
    assert ae.actor_type == "user"
    assert ae.action == "product.price_updated"
