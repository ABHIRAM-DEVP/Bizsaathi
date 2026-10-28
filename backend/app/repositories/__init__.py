"""Repositories package for tenant-scoped database access."""

from app.repositories.product import ProductRepository
from app.repositories.variant import VariantRepository

__all__ = [
    "ProductRepository",
    "VariantRepository",
]
