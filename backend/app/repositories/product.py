"""Product repository with mandatory tenant scoping.

Every query filters on business_id. Cross-tenant access is impossible by design.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Product


class ProductRepository:
    """Tenant-scoped product data access."""

    def __init__(self, session: Session, business_id: UUID):
        self._session = session
        self._business_id = business_id

    def get_by_id(self, product_id: UUID) -> Product | None:
        """Get a product by ID within the tenant scope."""
        stmt = select(Product).where(
            Product.business_id == self._business_id,
            Product.id == product_id,
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def get_by_sku(self, sku: str) -> Product | None:
        """Get a product by SKU within the tenant scope."""
        stmt = select(Product).where(
            Product.business_id == self._business_id,
            Product.sku == sku,
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def list_active(self, limit: int = 50, offset: int = 0) -> list[Product]:
        """List active products for the tenant."""
        stmt = (
            select(Product)
            .where(
                Product.business_id == self._business_id,
                Product.status == "active",
            )
            .order_by(Product.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.execute(stmt).scalars().all())

    def create(
        self,
        sku: str,
        name: str,
        price_inr: Decimal,
        description: str | None = None,
        created_by: UUID | None = None,
    ) -> Product:
        """Create a new product in the tenant scope."""
        product = Product(
            business_id=self._business_id,
            sku=sku,
            name=name,
            price_inr=price_inr,
            description=description,
            created_by=created_by,
        )
        self._session.add(product)
        self._session.flush()
        return product

    def update_price(self, product_id: UUID, new_price: Decimal, expected_version: int) -> Product | None:
        """Update product price with optimistic concurrency (version check)."""
        product = self.get_by_id(product_id)
        if product is None:
            return None
        if product.version != expected_version:
            return None  # Stale version
        product.price_inr = new_price
        product.version = expected_version + 1
        self._session.flush()
        return product

    def archive(self, product_id: UUID) -> bool:
        """Archive a product (soft delete) within tenant scope."""
        from datetime import datetime, timezone

        product = self.get_by_id(product_id)
        if product is None:
            return False
        product.status = "archived"
        product.archived_at = datetime.now(timezone.utc)
        self._session.flush()
        return True
