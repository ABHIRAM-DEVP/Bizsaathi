"""Product variant repository for variant querying and atomic stock adjustment."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import InvalidStateError, StaleVersionError
from app.models.domain import ProductVariant


class VariantRepository:
    """Tenant-scoped variant data access and stock adjustments."""

    def __init__(self, session: Session, business_id: UUID):
        self._session = session
        self._business_id = business_id

    def get_by_id(self, variant_id: UUID) -> ProductVariant | None:
        """Retrieve variant within tenant scope."""
        stmt = select(ProductVariant).where(
            ProductVariant.id == variant_id,
            ProductVariant.business_id == self._business_id,
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def get_first_for_product(self, product_id: UUID) -> ProductVariant | None:
        """Get primary/first variant for product within tenant scope."""
        stmt = (
            select(ProductVariant)
            .where(
                ProductVariant.product_id == product_id,
                ProductVariant.business_id == self._business_id,
            )
            .limit(1)
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def adjust_stock(
        self,
        variant_id: UUID,
        delta: int,
        expected_stock_version: int,
    ) -> ProductVariant:
        """Adjust stock with optimistic concurrency (version check) and negative stock prevention."""
        variant = self.get_by_id(variant_id)
        if not variant:
            raise InvalidStateError("Variant not found")

        if variant.stock_version != expected_stock_version:
            raise StaleVersionError(
                "Concurrent stock update detected. "
                f"Expected stock_version {expected_stock_version}, current {variant.stock_version}."
            )

        new_stock = variant.stock + delta
        if new_stock < 0:
            raise InvalidStateError(f"Resulting stock ({new_stock}) cannot be negative.")

        variant.stock = new_stock
        variant.stock_version = expected_stock_version + 1
        self._session.flush()
        return variant
