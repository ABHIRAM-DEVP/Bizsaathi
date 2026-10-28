"""phase 2 tables

Revision ID: 0002_phase2_tables
Revises: 0001_initial_schema
Create Date: 2026-10-28 13:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_phase2_tables"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # policy
    op.create_table(
        "policy",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("body", sa.String(length=5000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "kind IN ('delivery', 'returns', 'discounts', 'payment', 'other')", name=op.f("ck_policy_policy_kind_check")
        ),
        sa.CheckConstraint("version >= 1", name=op.f("ck_policy_policy_version_check")),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_policy_business_id_business")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_policy")),
        sa.UniqueConstraint("business_id", "kind", "version", name="policy_version_uq"),
    )

    # product_variant
    op.create_table(
        "product_variant",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("color", sa.String(length=60), nullable=True),
        sa.Column("size", sa.String(length=60), nullable=True),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("stock_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("stock >= 0", name=op.f("ck_product_variant_variant_stock_check")),
        sa.CheckConstraint("stock_version >= 1", name=op.f("ck_product_variant_variant_stock_version_check")),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_product_variant_business_id_business")),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], name=op.f("fk_product_variant_product_id_product")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_variant")),
    )
    op.create_index("ix_product_variant_business", "product_variant", ["business_id", "product_id"], unique=False)

    # job_event
    op.create_table(
        "job_event",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("node", sa.String(length=50), nullable=False),
        sa.Column("event", sa.String(length=30), nullable=False),
        sa.Column("tool", sa.String(length=100), nullable=True),
        sa.Column("redacted_input", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("redacted_output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("evidence_ids", postgresql.ARRAY(sa.Uuid()), server_default="{}", nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=True),
        sa.Column("retry", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "event IN ('step_started', 'step_finished', 'conflict_found', 'awaiting_approval', "
            "'blocked', 'retry', 'done', 'error')",
            name=op.f("ck_job_event_job_event_event_check"),
        ),
        sa.CheckConstraint("seq >= 1", name=op.f("ck_job_event_job_event_seq_check")),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_job_event_business_id_business")),
        sa.ForeignKeyConstraint(["job_id"], ["job.id"], name=op.f("fk_job_event_job_id_job")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_event")),
        sa.UniqueConstraint("job_id", "seq", name="job_event_job_seq_uq"),
    )
    op.create_index("ix_job_event_business", "job_event", ["business_id", "job_id"], unique=False)

    # proposal
    op.create_table(
        "proposal",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("root_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft', 'pending', 'approved', 'rejected', 'invalidated', 'expired', 'executed')",
            name=op.f("ck_proposal_proposal_status_check"),
        ),
        sa.CheckConstraint(
            "type IN ('product_draft', 'product_create', 'product_update', 'post_publish', 'order_action', 'reply')",
            name=op.f("ck_proposal_proposal_type_check"),
        ),
        sa.CheckConstraint("version >= 1", name=op.f("ck_proposal_proposal_version_check")),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_proposal_business_id_business")),
        sa.ForeignKeyConstraint(["job_id"], ["job.id"], name=op.f("fk_proposal_job_id_job")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_proposal")),
        sa.UniqueConstraint("root_id", "version", name="proposal_root_version_uq"),
    )
    op.create_index("ix_proposal_business", "proposal", ["business_id", "type", "status"], unique=False)

    # approval
    op.create_table(
        "approval",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("proposal_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("risk", sa.String(length=10), nullable=False),
        sa.Column("side_effect", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_by", sa.Uuid(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("risk IN ('low', 'medium', 'high')", name=op.f("ck_approval_approval_risk_check")),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'expired', 'invalidated')",
            name=op.f("ck_approval_approval_status_check"),
        ),
        sa.CheckConstraint(
            "type IN ('product_create', 'product_update', 'post_publish', 'order_action', 'reply')",
            name=op.f("ck_approval_approval_type_check"),
        ),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_approval_business_id_business")),
        sa.ForeignKeyConstraint(["decided_by"], ["app_user.id"], name=op.f("fk_approval_decided_by_app_user")),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposal.id"], name=op.f("fk_approval_proposal_id_proposal")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_approval")),
    )
    op.create_index("ix_approval_business", "approval", ["business_id", "status", "created_at"], unique=False)

    # execution
    op.create_table(
        "execution",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("approval_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("result_ref", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('succeeded', 'failed')", name=op.f("ck_execution_execution_status_check")),
        sa.ForeignKeyConstraint(["approval_id"], ["approval.id"], name=op.f("fk_execution_approval_id_approval")),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_execution_business_id_business")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_execution")),
        sa.UniqueConstraint("approval_id", name=op.f("uq_execution_approval_id")),
        sa.UniqueConstraint("business_id", "idempotency_key", name="execution_business_idem_uq"),
    )

    # post
    op.create_table(
        "post",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("text", sa.String(length=4000), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "channel IN ('instagram', 'whatsapp_status', 'facebook', 'generic')",
            name=op.f("ck_post_post_channel_check"),
        ),
        sa.CheckConstraint("language IN ('en', 'hi', 'mr')", name=op.f("ck_post_post_language_check")),
        sa.CheckConstraint(
            "status IN ('draft', 'checked', 'pending_approval', 'approved', 'exported')",
            name=op.f("ck_post_post_status_check"),
        ),
        sa.CheckConstraint("version >= 1", name=op.f("ck_post_post_version_check")),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_post_business_id_business")),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], name=op.f("fk_post_product_id_product")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_post")),
    )
    op.create_index("ix_post_business", "post", ["business_id", "product_id", "status"], unique=False)

    # post_revision
    op.create_table(
        "post_revision",
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version >= 1", name=op.f("ck_post_revision_post_rev_version_check")),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_post_revision_business_id_business")),
        sa.ForeignKeyConstraint(["post_id"], ["post.id"], name=op.f("fk_post_revision_post_id_post")),
        sa.PrimaryKeyConstraint("post_id", "version", name=op.f("pk_post_revision")),
    )

    # claim
    op.create_table(
        "claim",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("post_version", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("verdict", sa.String(length=20), nullable=True),
        sa.Column("severity", sa.String(length=10), nullable=True),
        sa.Column("repair_suggestion", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('fact', 'opinion')", name=op.f("ck_claim_claim_kind_check")),
        sa.CheckConstraint("post_version >= 1", name=op.f("ck_claim_claim_post_version_check")),
        sa.CheckConstraint("severity IN ('low', 'medium', 'high')", name=op.f("ck_claim_claim_severity_check")),
        sa.CheckConstraint(
            "verdict IN ('supported', 'contradicted', 'unverified')", name=op.f("ck_claim_claim_verdict_check")
        ),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_claim_business_id_business")),
        sa.ForeignKeyConstraint(["post_id"], ["post.id"], name=op.f("fk_claim_post_id_post")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_claim")),
    )
    op.create_index("ix_claim_post", "claim", ["business_id", "post_id", "post_version"], unique=False)

    # evidence
    op.create_table(
        "evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=True),
        sa.Column("source_kind", sa.String(length=20), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("source_version", sa.Integer(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source_kind IN ('product', 'variant', 'policy', 'order', 'transcript', 'media')",
            name=op.f("ck_evidence_evidence_source_kind_check"),
        ),
        sa.CheckConstraint("source_version >= 1", name=op.f("ck_evidence_evidence_source_version_check")),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_evidence_business_id_business")),
        sa.ForeignKeyConstraint(["claim_id"], ["claim.id"], name=op.f("fk_evidence_claim_id_claim")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence")),
    )
    op.create_index("ix_evidence_business", "evidence", ["business_id", "claim_id"], unique=False)

    # model_usage
    op.create_table(
        "model_usage",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("node", sa.String(length=50), nullable=False),
        sa.Column("model_id", sa.String(length=100), nullable=False),
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("media_units", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("est_cost_usd", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("latency_ms >= 0", name=op.f("ck_model_usage_model_usage_latency_check")),
        sa.CheckConstraint("mode IN ('live', 'mock')", name=op.f("ck_model_usage_model_usage_mode_check")),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_model_usage_business_id_business")),
        sa.ForeignKeyConstraint(["job_id"], ["job.id"], name=op.f("fk_model_usage_job_id_job")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_usage")),
    )
    op.create_index("ix_model_usage_business", "model_usage", ["business_id", "at"], unique=False)

    # idempotency_key
    op.create_table(
        "idempotency_key",
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("endpoint", sa.String(length=100), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("request_hash", sa.Text(), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_idempotency_key_business_id_business")),
        sa.PrimaryKeyConstraint("business_id", "endpoint", "key", name=op.f("pk_idempotency_key")),
    )


def downgrade() -> None:
    op.drop_table("idempotency_key")
    op.drop_index("ix_model_usage_business", table_name="model_usage")
    op.drop_table("model_usage")
    op.drop_index("ix_evidence_business", table_name="evidence")
    op.drop_table("evidence")
    op.drop_index("ix_claim_post", table_name="claim")
    op.drop_table("claim")
    op.drop_table("post_revision")
    op.drop_index("ix_post_business", table_name="post")
    op.drop_table("post")
    op.drop_table("execution")
    op.drop_index("ix_approval_business", table_name="approval")
    op.drop_table("approval")
    op.drop_index("ix_proposal_business", table_name="proposal")
    op.drop_table("proposal")
    op.drop_index("ix_job_event_business", table_name="job_event")
    op.drop_table("job_event")
    op.drop_index("ix_product_variant_business", table_name="product_variant")
    op.drop_table("product_variant")
    op.drop_table("policy")
