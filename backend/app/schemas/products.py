"""Pydantic schemas for product catalog and intake endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ProductFromPhotoRequest(BaseModel):
    """Payload to request product draft extraction from uploaded photos."""

    media_ids: list[UUID] = Field(min_length=1, max_length=4, description="1 to 4 uploaded photo media IDs")


class ProductFromVoiceRequest(BaseModel):
    """Payload to request product draft extraction from uploaded voice recording."""

    media_id: UUID = Field(description="Uploaded audio media ID")


class ProductCreateRequest(BaseModel):
    """Manual or from-draft confirmed product creation request."""

    sku: str | None = Field(default=None, description="Product SKU (generated if omitted)")
    name: str = Field(min_length=1, max_length=200, description="Product name")
    description: str | None = Field(default=None, max_length=5000)
    price_inr: Decimal = Field(gt=0, description="Confirmed product price in INR")
    stock: int = Field(default=0, ge=0, description="Initial stock quantity")
    color: str | None = Field(default=None, max_length=60)
    size: str | None = Field(default=None, max_length=60)
    from_draft_proposal_id: UUID | None = Field(default=None, description="Source draft proposal ID if converting")


class ProductPatchRequest(BaseModel):
    """Product attribute update with optimistic concurrency."""

    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    price_inr: Decimal | None = Field(default=None, ge=0)
    attributes: dict[str, Any] | None = None


class ProductStockAdjustmentRequest(BaseModel):
    """Atomic stock adjustment with expected version."""

    delta: int = Field(description="Stock change (positive for restock, negative for sale/reduction)")
    expected_stock_version: int = Field(ge=1, description="Expected variant stock_version")


class ProductResponse(BaseModel):
    """Confirmed catalog product."""

    id: UUID
    business_id: UUID
    sku: str
    name: str
    description: str | None = None
    price_inr: Decimal
    field_sources: dict[str, Any]
    attributes: dict[str, Any]
    status: str
    version: int
    stock: int = 0
    stock_version: int = 1
    created_at: datetime
    updated_at: datetime
