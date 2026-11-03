"""Load the checked-in, development-only catalog and synthetic inbox fixture."""

import hashlib
import json
import secrets
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4, uuid5

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ConfigurationError, InvalidStateError
from app.core.tenancy import DEV_BUSINESS_ID, ensure_development_business
from app.models.domain import (
    AuditEvent,
    Business,
    Conversation,
    Evidence,
    Media,
    Message,
    Product,
    ProductVariant,
    PublicSession,
)
from app.services.demo_orders import seed_demo_orders
from app.services.uploads import UploadService

_FIXTURE_DIRECTORY = Path(__file__).resolve().parents[1] / "demo_data"
_FIXTURE_PATH = _FIXTURE_DIRECTORY / "demo-data.json"
_DEMO_NAMESPACE = UUID("f0db89a2-a678-4631-aa03-442d12bd74e4")


def load_demo_fixture() -> dict[str, Any]:
    """Load the committed fixture; malformed demo data should fail startup explicitly."""
    fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(fixture, dict) or fixture.get("version") != 1:
        raise ConfigurationError("Unsupported local demo fixture format.")
    if not isinstance(fixture.get("products"), list) or not isinstance(fixture.get("synthetic_chats"), list):
        raise ConfigurationError("Local demo fixture must contain product and synthetic chat lists.")
    return fixture


def _stable_id(kind: str, business_id: UUID, key: str) -> UUID:
    return uuid5(_DEMO_NAMESPACE, f"{kind}:{business_id}:{key}")


def _seed_synthetic_reply(
    session: Session,
    *,
    business_id: UUID,
    product: Product,
    scenario: dict[str, Any],
) -> tuple[str, list[UUID], str | None]:
    answer_kind = scenario.get("answer_kind")
    prefix = "Synthetic demo only (not a real listing): " if product.attributes.get("demo_only") else ""
    evidence: list[Evidence] = []

    def add_product_evidence(field: str, value: str) -> None:
        item = Evidence(
            id=_stable_id("evidence", business_id, f"{scenario['key']}:{field}"),
            business_id=business_id,
            source_kind="product",
            source_id=product.id,
            source_version=product.version,
            snapshot={"field": field, "value": value},
        )
        evidence.append(item)

    if answer_kind == "price":
        price = format(product.price_inr, ".2f")
        add_product_evidence("name", product.name)
        add_product_evidence("price_inr", price)
        text = f"{prefix}{product.name} is listed at ₹{price}."
        escalation_reason = None
    elif answer_kind == "stock":
        variants = session.execute(
            select(ProductVariant)
            .where(
                ProductVariant.business_id == business_id,
                ProductVariant.product_id == product.id,
            )
            .order_by(ProductVariant.id)
        ).scalars().all()
        if not variants:
            return (
                "I can’t confirm availability from the catalog, so I’ve asked the seller to review it.",
                [],
                "Product stock is not confirmed in the catalog.",
            )
        add_product_evidence("name", product.name)
        for variant in variants:
            evidence.append(
                Evidence(
                    id=_stable_id("evidence", business_id, f"{scenario['key']}:stock:{variant.id}"),
                    business_id=business_id,
                    source_kind="variant",
                    source_id=variant.id,
                    source_version=variant.stock_version,
                    snapshot={"field": "stock", "value": variant.stock},
                )
            )
        stock = sum(variant.stock for variant in variants)
        text = (
            f"{prefix}{product.name} is listed as out of stock."
            if stock == 0
            else f"{prefix}The catalog lists {stock} units of {product.name} in stock."
        )
        escalation_reason = None
    elif answer_kind == "refund":
        return (
            "I can’t verify charges or issue a refund here, so I’ve asked the seller to review this request.",
            [],
            "Payment or refund requests require seller review.",
        )
    else:
        raise ConfigurationError(f"Unsupported synthetic chat answer kind: {answer_kind!r}.")

    session.add_all(evidence)
    session.flush()
    return text, [item.id for item in evidence], escalation_reason


def seed_demo_catalog(session: Session, business_id: UUID) -> dict[str, int]:
    """Insert missing fixture products and verified photos without overwriting seller data."""
    if settings.ENV != "dev":
        raise InvalidStateError("Demo catalog data can only be seeded when ENV=dev.")

    fixture = load_demo_fixture()
    upload_service = UploadService(session)
    products_created = 0
    images_created = 0

    for item in fixture["products"]:
        sku = item["sku"]
        existing = session.execute(
            select(Product).where(Product.business_id == business_id, Product.sku == sku)
        ).scalar_one_or_none()
        if existing is not None:
            continue

        product_id = _stable_id("product", business_id, sku)
        product = Product(
            id=product_id,
            business_id=business_id,
            sku=sku,
            name=item["name"],
            description=item["description"],
            price_inr=Decimal(item["price_inr"]),
            field_sources={
                "name": {"source": "seller_confirmed"},
                "description": {"source": "seller_confirmed"},
                "price_inr": {"source": "seller_confirmed"},
            },
            attributes={"demo_fixture": "local-v1"},
            status="active",
            version=1,
        )
        session.add(product)
        session.flush()

        variant_id = _stable_id("variant", business_id, sku)
        session.add(
            ProductVariant(
                id=variant_id,
                business_id=business_id,
                product_id=product_id,
                color=None,
                size=None,
                stock=item["stock"],
                stock_version=1,
            )
        )

        relative_asset = Path(item["photo"])
        asset_path = (_FIXTURE_DIRECTORY / relative_asset).resolve()
        if relative_asset.is_absolute() or not asset_path.is_relative_to(_FIXTURE_DIRECTORY.resolve()):
            raise ConfigurationError(f"Invalid photo path in local demo fixture for SKU '{sku}'.")
        image_bytes = asset_path.read_bytes()
        if not UploadService.verify_file_signature("photo", "image/png", image_bytes[:16]):
            raise ConfigurationError(f"Photo for SKU '{sku}' is not a valid PNG.")

        media_id = _stable_id("media", business_id, sku)
        storage_key = f"{business_id}/uploads/demo/{media_id}.png"
        media_path = upload_service.media_path(storage_key)
        media_path.parent.mkdir(parents=True, exist_ok=True)
        if media_path.exists():
            if hashlib.sha256(media_path.read_bytes()).digest() != hashlib.sha256(image_bytes).digest():
                raise ConfigurationError(f"Existing demo photo for SKU '{sku}' does not match the fixture.")
        else:
            media_path.write_bytes(image_bytes)

        session.add(
            Media(
                id=media_id,
                business_id=business_id,
                product_id=product_id,
                kind="photo",
                storage_key=storage_key,
                mime="image/png",
                size_bytes=len(image_bytes),
                sha256=hashlib.sha256(image_bytes).hexdigest(),
                status="verified",
            )
        )
        session.flush()
        products_created += 1
        images_created += 1

    return {"products_created": products_created, "images_created": images_created}


def seed_demo_inbox(session: Session, business_id: UUID) -> list[Conversation]:
    """Create missing deterministic synthetic conversations grounded in tenant products."""
    if settings.ENV not in ("dev", "test"):
        raise InvalidStateError("Synthetic inbox data can only be seeded in development or tests.")

    business_exists = session.execute(
        select(Business.id).where(Business.id == business_id).with_for_update()
    ).scalar_one_or_none()
    if business_exists is None:
        raise InvalidStateError("Cannot seed a demo inbox for a missing business.")

    fixture = load_demo_fixture()
    products = session.execute(
        select(Product)
        .where(Product.business_id == business_id, Product.status == "active")
        .order_by(Product.created_at, Product.id)
    ).scalars().all()
    if not products:
        product = Product(
            business_id=business_id,
            sku=f"DEMO-TOY-{uuid4().hex[:8].upper()}",
            name="DEMO ONLY - Sample toy",
            description="Synthetic local demo item; not a real product and not for sale.",
            price_inr=Decimal("499.00"),
            field_sources={
                "name": {"source": "synthetic_demo", "confirmed": False},
                "price_inr": {"source": "synthetic_demo", "confirmed": False},
            },
            attributes={"demo_only": True},
            status="active",
            version=1,
        )
        session.add(product)
        session.flush()
        session.add(
            ProductVariant(
                business_id=business_id,
                product_id=product.id,
                color="Demo",
                size=None,
                stock=8,
                stock_version=1,
            )
        )
        session.flush()
        products = [product]

    product = products[0]
    product_name = product.name
    conversations: list[Conversation] = []
    now = datetime.now(UTC)

    for scenario in fixture["synthetic_chats"]:
        key = scenario["key"]
        conversation_id = _stable_id("conversation", business_id, key)
        existing = session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.business_id == business_id,
            )
        ).scalar_one_or_none()
        if existing is not None:
            conversations.append(existing)
            continue

        session_id = _stable_id("public-session", business_id, key)
        public_session = PublicSession(
            id=session_id,
            business_id=business_id,
            token_hash=bcrypt.hashpw(secrets.token_urlsafe(32).encode("utf-8"), bcrypt.gensalt()),
            status="open",
            ip_hash=None,
            expires_at=now + timedelta(days=1),
        )
        session.add(public_session)
        session.flush()

        customer_text = scenario["message"].format(product_name=product_name)
        conversation = Conversation(
            id=conversation_id,
            business_id=business_id,
            public_session_id=session_id,
            status="open",
            source="demo",
            customer_label=scenario["customer_name"],
        )
        session.add(conversation)
        session.flush()
        session.add(
            Message(
                id=_stable_id("customer-message", business_id, key),
                business_id=business_id,
                conversation_id=conversation_id,
                role="customer",
                body=customer_text,
                evidence_ids=[],
            )
        )

        reply_text, evidence_ids, escalation_reason = _seed_synthetic_reply(
            session,
            business_id=business_id,
            product=product,
            scenario=scenario,
        )
        session.add(
            Message(
                id=_stable_id("assistant-message", business_id, key),
                business_id=business_id,
                conversation_id=conversation_id,
                role="assistant",
                body=reply_text,
                evidence_ids=evidence_ids,
            )
        )
        if escalation_reason:
            conversation.status = "escalated"
            conversation.escalation_reason = escalation_reason
            public_session.status = "escalated"
            session.add(
                AuditEvent(
                    business_id=business_id,
                    actor_type="system",
                    action="customer_message_escalated",
                    entity_type="conversation",
                    entity_id=str(conversation_id),
                    detail={"reason": escalation_reason, "demo_sample": True},
                )
            )
        conversation.updated_at = now
        session.flush()
        conversations.append(conversation)

    return conversations


def seed_demo_data(session: Session) -> dict[str, int]:
    """Load local catalog, synthetic order examples, and synthetic inbox at dev startup."""
    if settings.ENV != "dev":
        raise InvalidStateError("Demo data can only be seeded when ENV=dev.")

    ensure_development_business(session)
    catalog_result = seed_demo_catalog(session, DEV_BUSINESS_ID)
    order_result = seed_demo_orders(session)
    conversations = seed_demo_inbox(session, DEV_BUSINESS_ID)
    return {
        **catalog_result,
        **order_result,
        "conversations_available": len(conversations),
    }


__all__ = ["load_demo_fixture", "seed_demo_catalog", "seed_demo_inbox", "seed_demo_data"]
