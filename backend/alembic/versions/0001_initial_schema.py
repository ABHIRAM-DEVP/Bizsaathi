"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-28 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # business
    op.create_table(
        "business",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=63), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("languages", postgresql.ARRAY(sa.Text()), server_default="{en}", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('active', 'suspended')", name=op.f("ck_business_business_status_check")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_business")),
        sa.UniqueConstraint("slug", name=op.f("uq_business_slug")),
    )

    # app_user
    op.create_table(
        "app_user",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("phone_e164", sa.String(length=16), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("language", sa.String(length=5), server_default="en", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('owner', 'operator')", name=op.f("ck_app_user_app_user_role_check")),
        sa.CheckConstraint("language IN ('en', 'hi', 'mr')", name=op.f("ck_app_user_app_user_language_check")),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_app_user_business_id_business")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_app_user")),
        sa.UniqueConstraint("phone_e164", name=op.f("uq_app_user_phone_e164")),
    )
    op.create_index(op.f("ix_app_user_business_id"), "app_user", ["business_id"], unique=False)

    # product
    op.create_table(
        "product",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=5000), nullable=True),
        sa.Column("price_inr", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("field_sources", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('active', 'archived')", name=op.f("ck_product_product_status_check")),
        sa.CheckConstraint("price_inr >= 0", name=op.f("ck_product_product_price_check")),
        sa.CheckConstraint("version >= 1", name=op.f("ck_product_product_version_check")),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_product_business_id_business")),
        sa.ForeignKeyConstraint(["created_by"], ["app_user.id"], name=op.f("fk_product_created_by_app_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product")),
        sa.UniqueConstraint("business_id", "sku", name="product_business_sku_uq"),
    )
    op.create_index("ix_product_business_status", "product", ["business_id", "status", "created_at"], unique=False)

    # media
    op.create_table(
        "media",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("mime", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('photo', 'audio', 'generated_image')", name=op.f("ck_media_media_kind_check")),
        sa.CheckConstraint("status IN ('pending', 'verified', 'rejected')", name=op.f("ck_media_media_status_check")),
        sa.CheckConstraint("size_bytes > 0", name=op.f("ck_media_media_size_check")),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_media_business_id_business")),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], name=op.f("fk_media_product_id_product")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_media")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_media_storage_key")),
    )
    op.create_index("ix_media_business", "media", ["business_id", "created_at"], unique=False)

    # job
    op.create_table(
        "job",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="queued", nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
        sa.Column("progress_step", sa.Integer(), server_default="0", nullable=False),
        sa.Column("progress_total", sa.Integer(), server_default="0", nullable=False),
        sa.Column("result_ref", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("model_calls", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_model_calls", sa.Integer(), server_default="8", nullable=False),
        sa.Column("checkpoint_ref", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "kind IN ('product_from_photo', 'product_from_voice', 'post_generate', "
            "'claim_check', 'customer_reply', 'eval_run', 'proposal_revalidate')",
            name=op.f("ck_job_job_kind_check"),
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'awaiting_approval', 'succeeded', 'blocked', 'failed', 'cancelled')",
            name=op.f("ck_job_job_status_check"),
        ),
        sa.CheckConstraint("model_calls >= 0", name=op.f("ck_job_job_model_calls_check")),
        sa.CheckConstraint("max_model_calls >= 0", name=op.f("ck_job_job_max_model_calls_check")),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_job_business_id_business")),
        sa.ForeignKeyConstraint(["created_by"], ["app_user.id"], name=op.f("fk_job_created_by_app_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job")),
        sa.UniqueConstraint("business_id", "idempotency_key", name="job_idem_uq"),
    )
    op.create_index("ix_job_business", "job", ["business_id", "created_at"], unique=False)

    # audit_event
    op.create_table(
        "audit_event",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("actor_type", sa.String(length=20), nullable=False),
        sa.Column("actor_id", sa.String(length=100), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=True),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("request_id", sa.String(length=100), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "actor_type IN ('user', 'agent', 'system', 'public')",
            name=op.f("ck_audit_event_audit_event_actor_type_check"),
        ),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_audit_event_business_id_business")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_event")),
    )
    op.create_index("ix_audit_event_business", "audit_event", ["business_id", "at"], unique=False)
    op.create_index("ix_audit_event_entity", "audit_event", ["business_id", "entity_type", "entity_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_event_entity", table_name="audit_event")
    op.drop_index("ix_audit_event_business", table_name="audit_event")
    op.drop_table("audit_event")
    op.drop_index("ix_job_business", table_name="job")
    op.drop_table("job")
    op.drop_index("ix_media_business", table_name="media")
    op.drop_table("media")
    op.drop_index("ix_product_business_status", table_name="product")
    op.drop_table("product")
    op.drop_index(op.f("ix_app_user_business_id"), table_name="app_user")
    op.drop_table("app_user")
    op.drop_table("business")
