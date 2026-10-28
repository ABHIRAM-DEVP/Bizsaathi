"""Pydantic schemas for BizSaathi API request and response models."""

from app.schemas.approvals import (
    ApprovalDecisionRequest,
    ApprovalEditRequest,
    ApprovalResponse,
)
from app.schemas.jobs import JobResponse
from app.schemas.posts import (
    ClaimResponse,
    PostGenerateRequest,
    PostPatchRequest,
    PostResponse,
)
from app.schemas.products import (
    ProductCreateRequest,
    ProductFromPhotoRequest,
    ProductFromVoiceRequest,
    ProductPatchRequest,
    ProductResponse,
    ProductStockAdjustmentRequest,
)
from app.schemas.uploads import UploadRequest, UploadResponse

__all__ = [
    "UploadRequest",
    "UploadResponse",
    "JobResponse",
    "ProductFromPhotoRequest",
    "ProductFromVoiceRequest",
    "ProductCreateRequest",
    "ProductPatchRequest",
    "ProductStockAdjustmentRequest",
    "ProductResponse",
    "ApprovalResponse",
    "ApprovalDecisionRequest",
    "ApprovalEditRequest",
    "PostGenerateRequest",
    "PostPatchRequest",
    "PostResponse",
    "ClaimResponse",
]
