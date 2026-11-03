"""phase4 customer and orders

Revision ID: 5aa6ba177a21
Revises: 0002_phase2_tables
Create Date: 2026-10-28 22:01:33.857840

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5aa6ba177a21"
down_revision: Union[str, None] = "0002_phase2_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # public_session
    op.create_table(
        "public_session",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('open', 'escalated', 'closed', 'blocked')",
            name=op.f("ck_public_session_status_check"),
        ),
        sa.ForeignKeyConstraint(
            ["business_id"], ["business.id"], name=op.f("fk_public_session_business_id_business")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_public_session")),
    )
    op.create_index(
        "public_session_token_uq",
        "public_session",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "public_session_business_ix",
        "public_session",
        ["business_id", sa.text("created_at DESC")],
        unique=False,
    )

    # conversation
    op.create_table(
        "conversation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("public_session_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("escalation_reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('open', 'escalated', 'closed')", name=op.f("ck_conversation_status_check")
        ),
        sa.ForeignKeyConstraint(
            ["business_id"], ["business.id"], name=op.f("fk_conversation_business_id_business")
        ),
        sa.ForeignKeyConstraint(
            ["public_session_id"],
            ["public_session.id"],
            name=op.f("fk_conversation_public_session_id_public_session"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation")),
        sa.UniqueConstraint("public_session_id", name="conversation_session_uq"),
    )
    op.create_index(
        "conversation_business_ix",
        "conversation",
        ["business_id", "status", sa.text("updated_at DESC")],
        unique=False,
    )

    # message
    op.create_table(
        "message",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("body", sa.String(length=4000), nullable=False),
        sa.Column("evidence_ids", postgresql.ARRAY(sa.Uuid()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "role IN ('customer', 'assistant', 'owner', 'system')", name=op.f("ck_message_role_check")
        ),
        sa.CheckConstraint("char_length(body) <= 4000", name=op.f("ck_message_body_length_check")),
        sa.ForeignKeyConstraint(["business_id"], ["business.id"], name=op.f("fk_message_business_id_business")),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversation.id"], name=op.f("fk_message_conversation_id_conversation")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_message")),
    )
    op.create_index(
        "message_conversation_ix",
        "message",
        ["business_id", "conversation_id", "created_at"],
        unique=False,
    )

    # Add message_id FK to evidence (references message table created above)
    op.add_column("evidence", sa.Column("message_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_evidence_message_id_message"), "evidence", "message", ["message_id"], ["id"]
    )

    # customer_order
    op.create_table(
        "customer_order",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("public_session_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("customer_name", sa.String(length=120), nullable=False),
        sa.Column("delivery_note", sa.String(length=500), nullable=True),
        sa.Column("total_inr", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("payment_method", sa.String(length=20), nullable=True),
        sa.Column("payment_reference", sa.String(length=200), nullable=True),
        sa.Column("payment_recorded_by", sa.Uuid(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'AWAITING_PAYMENT', 'PAID', 'FULFILLED', 'CANCELLED', 'FAILED')",
            name=op.f("ck_customer_order_status_check"),
        ),
        sa.CheckConstraint(
            "char_length(customer_name) BETWEEN 1 AND 120",
            name=op.f("ck_customer_order_name_check"),
        ),
        sa.CheckConstraint(
            "delivery_note IS NULL OR char_length(delivery_note) <= 500",
            name=op.f("ck_customer_order_note_check"),
        ),
        sa.CheckConstraint("total_inr >= 0", name=op.f("ck_customer_order_total_check")),
        sa.CheckConstraint(
            "payment_method IS NULL OR payment_method IN ('cash', 'upi', 'bank', 'other')",
            name=op.f("ck_customer_order_payment_method_check"),
        ),
        sa.ForeignKeyConstraint(
            ["business_id"], ["business.id"], name=op.f("fk_customer_order_business_id_business")
        ),
        sa.ForeignKeyConstraint(
            ["public_session_id"],
            ["public_session.id"],
            name=op.f("fk_customer_order_public_session_id_public_session"),
        ),
        sa.ForeignKeyConstraint(
            ["payment_recorded_by"],
            ["app_user.id"],
            name=op.f("fk_customer_order_payment_recorded_by_app_user"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_order")),
        sa.UniqueConstraint("business_id", "idempotency_key", name="customer_order_idempotency_uq"),
    )
    op.create_index(
        "customer_order_business_ix",
        "customer_order",
        ["business_id", "status", sa.text("created_at DESC")],
        unique=False,
    )

    # order_item
    op.create_table(
        "order_item",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("variant_id", sa.Uuid(), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("unit_price_inr", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.CheckConstraint("qty > 0 AND qty <= 100", name=op.f("ck_order_item_qty_check")),
        sa.CheckConstraint("unit_price_inr >= 0", name=op.f("ck_order_item_price_check")),
        sa.ForeignKeyConstraint(
            ["business_id"], ["business.id"], name=op.f("fk_order_item_business_id_business")
        ),
        sa.ForeignKeyConstraint(
            ["order_id"], ["customer_order.id"], name=op.f("fk_order_item_order_id_customer_order")
        ),
        sa.ForeignKeyConstraint(
            ["variant_id"], ["product_variant.id"], name=op.f("fk_order_item_variant_id_product_variant")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_item")),
    )
    op.create_index("order_item_order_ix", "order_item", ["business_id", "order_id"], unique=False)

    # order_status_history
    op.create_table(
        "order_status_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("from_status", sa.String(length=30), nullable=True),
        sa.Column("to_status", sa.String(length=30), nullable=False),
        sa.Column("actor_type", sa.String(length=30), nullable=False),
        sa.Column("actor_id", sa.String(length=200), nullable=True),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "actor_type IN ('user', 'system', 'execution_service')",
            name=op.f("ck_order_status_history_actor_type_check"),
        ),
        sa.ForeignKeyConstraint(
            ["business_id"], ["business.id"], name=op.f("fk_order_status_history_business_id_business")
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["customer_order.id"],
            name=op.f("fk_order_status_history_order_id_customer_order"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_status_history")),
    )
    op.create_index(
        "order_status_history_ix",
        "order_status_history",
        ["business_id", "order_id", "at"],
        unique=False,
    )

    # audit_event is created by the initial revision; widen its audit actor and entity fields here.
    op.alter_column(
        "audit_event", "actor_type", existing_type=sa.String(length=20), type_=sa.String(length=30),
        existing_nullable=False,
    )
    op.alter_column(
        "audit_event", "actor_id", existing_type=sa.String(length=100), type_=sa.String(length=200),
        existing_nullable=True,
    )
    op.alter_column(
        "audit_event", "entity_id", existing_type=sa.String(length=100), type_=sa.String(length=200),
        existing_nullable=True,
    )
    op.create_index(
        "audit_event_business_ix", "audit_event", ["business_id", sa.text("at DESC")], unique=False
    )
    op.create_index(
        "audit_event_entity_ix",
        "audit_event",
        ["business_id", "entity_type", "entity_id"],
        unique=False,
    )

    # Create trigger to make audit_event append-only
    op.execute(
        """
        CREATE FUNCTION audit_event_block_mutation() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'audit_event is append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER audit_event_no_update
          BEFORE UPDATE ON audit_event
          FOR EACH ROW EXECUTE FUNCTION audit_event_block_mutation();
        """
    )

    op.execute(
        """
        CREATE TRIGGER audit_event_no_delete
          BEFORE DELETE ON audit_event
          FOR EACH ROW EXECUTE FUNCTION audit_event_block_mutation();
        """
    )


def downgrade() -> None:
    # Drop triggers and function
    op.execute("DROP TRIGGER IF EXISTS audit_event_no_delete ON audit_event")
    op.execute("DROP TRIGGER IF EXISTS audit_event_no_update ON audit_event")
    op.execute("DROP FUNCTION IF EXISTS audit_event_block_mutation()")

    # Drop tables in reverse dependency order
    op.drop_index("audit_event_entity_ix", table_name="audit_event")
    op.drop_index("audit_event_business_ix", table_name="audit_event")
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM audit_event
            WHERE char_length(actor_type) > 20
               OR char_length(actor_id) > 100
               OR char_length(entity_id) > 100
          ) THEN
            RAISE EXCEPTION 'Cannot downgrade audit_event fields without truncating data';
          END IF;
        END;
        $$;
        """
    )
    op.alter_column(
        "audit_event", "entity_id", existing_type=sa.String(length=200), type_=sa.String(length=100),
        existing_nullable=True,
    )
    op.alter_column(
        "audit_event", "actor_id", existing_type=sa.String(length=200), type_=sa.String(length=100),
        existing_nullable=True,
    )
    op.alter_column(
        "audit_event", "actor_type", existing_type=sa.String(length=30), type_=sa.String(length=20),
        existing_nullable=False,
    )

    op.drop_index("order_status_history_ix", table_name="order_status_history")
    op.drop_table("order_status_history")

    op.drop_index("order_item_order_ix", table_name="order_item")
    op.drop_table("order_item")

    op.drop_index("customer_order_business_ix", table_name="customer_order")
    op.drop_table("customer_order")

    # Drop message_id FK from evidence
    op.drop_constraint(op.f("fk_evidence_message_id_message"), "evidence", type_="foreignkey")
    op.drop_column("evidence", "message_id")

    op.drop_index("message_conversation_ix", table_name="message")
    op.drop_table("message")

    op.drop_index("conversation_business_ix", table_name="conversation")
    op.drop_table("conversation")

    op.drop_index("public_session_business_ix", table_name="public_session")
    op.drop_index("public_session_token_uq", table_name="public_session")
    op.drop_table("public_session")
