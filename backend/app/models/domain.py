"""Core domain models: Business, AppUser, Product, Job, AuditEvent.

Based on docs/schema/reference_schema.sql and docs/02-data-model.md.
Every business-owned table includes business_id for tenant isolation.
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Business(TimestampMixin, Base):
    """Tenant entity. Top-level owner of all business data."""

    __tablename__ = "business"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(63), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    languages: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{en}")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")

    # Relationships
    users: Mapped[list["AppUser"]] = relationship(back_populates="business")
    products: Mapped[list["Product"]] = relationship(back_populates="business")
    jobs: Mapped[list["Job"]] = relationship(back_populates="business")

    __table_args__ = (CheckConstraint("status IN ('active', 'suspended')", name="business_status_check"),)


class AppUser(TimestampMixin, Base):
    """Application user, always belongs to a business tenant."""

    __tablename__ = "app_user"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False, index=True)
    phone_e164: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    language: Mapped[str] = mapped_column(String(5), nullable=False, server_default="en")

    # Relationships
    business: Mapped["Business"] = relationship(back_populates="users")

    __table_args__ = (
        CheckConstraint("role IN ('owner', 'operator')", name="app_user_role_check"),
        CheckConstraint("language IN ('en', 'hi', 'mr')", name="app_user_language_check"),
    )


class Product(TimestampMixin, Base):
    """Confirmed product facts. AI suggestions live in proposals until approved."""

    __tablename__ = "product"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(5000), nullable=True)
    price_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    field_sources: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("app_user.id"), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    business: Mapped["Business"] = relationship(back_populates="products")

    __table_args__ = (
        UniqueConstraint("business_id", "sku", name="product_business_sku_uq"),
        CheckConstraint("status IN ('active', 'archived')", name="product_status_check"),
        CheckConstraint("price_inr >= 0", name="product_price_check"),
        CheckConstraint("version >= 1", name="product_version_check"),
        Index("ix_product_business_status", "business_id", "status", "created_at"),
    )


class Media(Base):
    """Uploaded media files (photo, audio, generated_image)."""

    __tablename__ = "media"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    product_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("product.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    mime: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        CheckConstraint("kind IN ('photo', 'audio', 'generated_image')", name="media_kind_check"),
        CheckConstraint("status IN ('pending', 'verified', 'rejected')", name="media_status_check"),
        CheckConstraint("size_bytes > 0", name="media_size_check"),
        Index("ix_media_business", "business_id", "created_at"),
    )


class Job(Base):
    """Async processing job. Created by upload/action, tracks LangGraph execution."""

    __tablename__ = "job"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="queued")
    created_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("app_user.id"), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    progress_step: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    progress_total: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    result_ref: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_calls: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    max_model_calls: Mapped[int] = mapped_column(Integer, nullable=False, server_default="8")
    checkpoint_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    business: Mapped["Business"] = relationship(back_populates="jobs")

    __table_args__ = (
        CheckConstraint(
            "kind IN ('product_from_photo', 'product_from_voice', 'post_generate', "
            "'claim_check', 'customer_reply', 'eval_run', 'proposal_revalidate')",
            name="job_kind_check",
        ),
        CheckConstraint(
            "status IN ('queued', 'running', 'awaiting_approval', 'succeeded', 'blocked', 'failed', 'cancelled')",
            name="job_status_check",
        ),
        CheckConstraint("model_calls >= 0", name="job_model_calls_check"),
        CheckConstraint("max_model_calls >= 0", name="job_max_model_calls_check"),
        Index("ix_job_business", "business_id", "created_at"),
        UniqueConstraint("business_id", "idempotency_key", name="job_idem_uq"),
    )


class AuditEvent(Base):
    """Append-only audit log. Every tenant action is recorded."""

    __tablename__ = "audit_event"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "actor_type IN ('user', 'agent', 'system', 'public')",
            name="audit_event_actor_type_check",
        ),
        Index("ix_audit_event_business", "business_id", "at"),
        Index("ix_audit_event_entity", "business_id", "entity_type", "entity_id"),
    )


class Policy(Base):
    """Business policies (delivery, returns, discounts, payment, other)."""

    __tablename__ = "policy"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    body: Mapped[str] = mapped_column(String(5000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        CheckConstraint("kind IN ('delivery', 'returns', 'discounts', 'payment', 'other')", name="policy_kind_check"),
        CheckConstraint("version >= 1", name="policy_version_check"),
        UniqueConstraint("business_id", "kind", "version", name="policy_version_uq"),
    )


class ProductVariant(TimestampMixin, Base):
    """Specific SKU variants (color, size, stock quantity)."""

    __tablename__ = "product_variant"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    product_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("product.id"), nullable=False)
    color: Mapped[str | None] = mapped_column(String(60), nullable=True)
    size: Mapped[str | None] = mapped_column(String(60), nullable=True)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        CheckConstraint("stock >= 0", name="variant_stock_check"),
        CheckConstraint("stock_version >= 1", name="variant_stock_version_check"),
        Index("ix_product_variant_business", "business_id", "product_id"),
    )


class JobEvent(Base):
    """Sanitized trace events recorded during LangGraph execution. Never raw reasoning."""

    __tablename__ = "job_event"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    job_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("job.id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    node: Mapped[str] = mapped_column(String(50), nullable=False)
    event: Mapped[str] = mapped_column(String(30), nullable=False)
    tool: Mapped[str | None] = mapped_column(String(100), nullable=True)
    redacted_input: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    redacted_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    evidence_ids: Mapped[list[UUID]] = mapped_column(ARRAY(Uuid), nullable=False, server_default="{}")
    decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    retry: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        CheckConstraint("seq >= 1", name="job_event_seq_check"),
        CheckConstraint(
            "event IN ('step_started', 'step_finished', 'conflict_found', 'awaiting_approval', "
            "'blocked', 'retry', 'done', 'error')",
            name="job_event_event_check",
        ),
        UniqueConstraint("job_id", "seq", name="job_event_job_seq_uq"),
        Index("ix_job_event_business", "business_id", "job_id"),
    )


class Proposal(Base):
    """Proposal version. AI output lives here until explicitly approved by seller."""

    __tablename__ = "proposal"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    root_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    job_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("job.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('product_draft', 'product_create', 'product_update', 'post_publish', 'order_action', 'reply')",
            name="proposal_type_check",
        ),
        CheckConstraint(
            "status IN ('draft', 'pending', 'approved', 'rejected', 'invalidated', 'expired', 'executed')",
            name="proposal_status_check",
        ),
        CheckConstraint("version >= 1", name="proposal_version_check"),
        UniqueConstraint("root_id", "version", name="proposal_root_version_uq"),
        Index("ix_proposal_business", "business_id", "type", "status"),
    )


class Approval(Base):
    """Approval request bound to an exact proposal version."""

    __tablename__ = "approval"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    proposal_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("proposal.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    warnings: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    risk: Mapped[str] = mapped_column(String(10), nullable=False, default="low")
    side_effect: Mapped[dict] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decided_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("app_user.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('product_create', 'product_update', 'post_publish', 'order_action', 'reply')",
            name="approval_type_check",
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'expired', 'invalidated')",
            name="approval_status_check",
        ),
        CheckConstraint("risk IN ('low', 'medium', 'high')", name="approval_risk_check"),
        Index("ix_approval_business", "business_id", "status", "created_at"),
    )


class Execution(Base):
    """Immutable record of side effects applied by the Execution Service only."""

    __tablename__ = "execution"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    approval_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("approval.id"), nullable=False, unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    result_ref: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        CheckConstraint("status IN ('succeeded', 'failed')", name="execution_status_check"),
        UniqueConstraint("business_id", "idempotency_key", name="execution_business_idem_uq"),
    )


class Post(TimestampMixin, Base):
    """Marketing or social post draft."""

    __tablename__ = "post"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    product_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("product.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    text: Mapped[str] = mapped_column(String(4000), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "channel IN ('instagram', 'whatsapp_status', 'facebook', 'generic')",
            name="post_channel_check",
        ),
        CheckConstraint("language IN ('en', 'hi', 'mr')", name="post_language_check"),
        CheckConstraint(
            "status IN ('draft', 'checked', 'pending_approval', 'approved', 'exported')",
            name="post_status_check",
        ),
        CheckConstraint("version >= 1", name="post_version_check"),
        Index("ix_post_business", "business_id", "product_id", "status"),
    )


class PostRevision(Base):
    """Revision history for edited posts."""

    __tablename__ = "post_revision"

    post_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("post.id"), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (CheckConstraint("version >= 1", name="post_rev_version_check"),)


class Claim(Base):
    """Individual factual claim or opinion extracted from post text."""

    __tablename__ = "claim"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    post_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("post.id"), nullable=False)
    post_version: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    verdict: Mapped[str | None] = mapped_column(String(20), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(10), nullable=True)
    repair_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        CheckConstraint("kind IN ('fact', 'opinion')", name="claim_kind_check"),
        CheckConstraint("verdict IN ('supported', 'contradicted', 'unverified')", name="claim_verdict_check"),
        CheckConstraint("severity IN ('low', 'medium', 'high')", name="claim_severity_check"),
        CheckConstraint("post_version >= 1", name="claim_post_version_check"),
        Index("ix_claim_post", "business_id", "post_id", "post_version"),
    )


class Evidence(Base):
    """Grounding proof snapshot linked to a claim."""

    __tablename__ = "evidence"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    claim_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("claim.id"), nullable=True)
    source_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    source_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    source_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "source_kind IN ('product', 'variant', 'policy', 'order', 'transcript', 'media')",
            name="evidence_source_kind_check",
        ),
        CheckConstraint("source_version >= 1", name="evidence_source_version_check"),
        Index("ix_evidence_business", "business_id", "claim_id"),
    )


class ModelUsage(Base):
    """Model token and latency usage log per node/job."""

    __tablename__ = "model_usage"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), nullable=False)
    job_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("job.id"), nullable=True)
    node: Mapped[str] = mapped_column(String(50), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    media_units: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    est_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        CheckConstraint("mode IN ('live', 'mock')", name="model_usage_mode_check"),
        CheckConstraint("latency_ms >= 0", name="model_usage_latency_check"),
        Index("ix_model_usage_business", "business_id", "at"),
    )


class IdempotencyKeyRecord(Base):
    """Database idempotency locks and cached receipts."""

    __tablename__ = "idempotency_key"

    business_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("business.id"), primary_key=True)
    endpoint: Mapped[str] = mapped_column(String(100), primary_key=True)
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_hash: Mapped[bytes] = mapped_column(Text, nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
