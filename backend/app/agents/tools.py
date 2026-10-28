"""Read-only database tools for agent context gathering.

MANDATORY: Every tool accepts business_id and scopes queries strictly to that tenant.
Cross-tenant leakage is strictly prevented at the query level.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Policy, Product, ProductVariant


def get_product_by_sku(session: Session, business_id: UUID, sku: str) -> dict[str, Any] | None:
    """Fetch product by SKU within the tenant scope."""
    stmt = select(Product).where(
        Product.business_id == business_id,
        Product.sku == sku,
        Product.status == "active",
    )
    product = session.execute(stmt).scalar_one_or_none()
    if not product:
        return None
    return {
        "id": str(product.id),
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "price_inr": float(product.price_inr),
        "attributes": product.attributes,
        "version": product.version,
    }


def list_products_by_name(session: Session, business_id: UUID, query: str) -> list[dict[str, Any]]:
    """Search products by name within tenant scope."""
    stmt = (
        select(Product)
        .where(
            Product.business_id == business_id,
            Product.name.ilike(f"%{query}%"),
            Product.status == "active",
        )
        .limit(10)
    )
    products = session.execute(stmt).scalars().all()
    return [
        {
            "id": str(p.id),
            "sku": p.sku,
            "name": p.name,
            "price_inr": float(p.price_inr),
            "attributes": p.attributes,
        }
        for p in products
    ]


def list_variants(session: Session, business_id: UUID, product_id: UUID) -> list[dict[str, Any]]:
    """List confirmed variants for a product within tenant scope."""
    stmt = select(ProductVariant).where(
        ProductVariant.business_id == business_id,
        ProductVariant.product_id == product_id,
    )
    variants = session.execute(stmt).scalars().all()
    return [
        {
            "id": str(v.id),
            "color": v.color,
            "size": v.size,
            "stock": v.stock,
            "stock_version": v.stock_version,
        }
        for v in variants
    ]


def get_policy(session: Session, business_id: UUID, kind: str) -> dict[str, Any] | None:
    """Get active policy for kind within tenant scope."""
    stmt = (
        select(Policy)
        .where(
            Policy.business_id == business_id,
            Policy.kind == kind,
        )
        .order_by(Policy.version.desc())
        .limit(1)
    )
    pol = session.execute(stmt).scalar_one_or_none()
    if not pol:
        return None
    return {
        "id": str(pol.id),
        "kind": pol.kind,
        "version": pol.version,
        "body": pol.body,
    }
