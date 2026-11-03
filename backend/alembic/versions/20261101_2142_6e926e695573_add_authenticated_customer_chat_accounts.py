"""Add customer accounts and bind chat to authenticated accounts.

Revision ID: 6e926e695573
Revises: 20261102_0010
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "6e926e695573"
down_revision: Union[str, None] = "20261102_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customer_account",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "char_length(email) BETWEEN 3 AND 320",
            name=op.f("ck_customer_account_customer_account_email_check"),
        ),
        sa.CheckConstraint(
            "char_length(display_name) BETWEEN 1 AND 120",
            name=op.f("ck_customer_account_customer_account_name_check"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_account")),
        sa.UniqueConstraint("email", name=op.f("uq_customer_account_email")),
    )
    op.create_table(
        "customer_auth_session",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("customer_account_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["customer_account_id"],
            ["customer_account.id"],
            name=op.f("fk_customer_auth_session_customer_account_id_customer_account"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_auth_session")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_customer_auth_session_token_hash")),
    )
    op.create_index(
        "customer_auth_session_account_ix",
        "customer_auth_session",
        ["customer_account_id", "expires_at"],
    )
    op.add_column("message", sa.Column("read_by_owner_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("public_session", sa.Column("customer_account_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_public_session_customer_account_id_customer_account"),
        "public_session",
        "customer_account",
        ["customer_account_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column(
        "public_session",
        "token_hash",
        existing_type=sa.LargeBinary(),
        nullable=True,
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_public_session_customer_account_id_customer_account"),
        "public_session",
        type_="foreignkey",
    )
    op.execute(
        "UPDATE public_session SET token_hash = decode(md5(id::text), 'hex') "
        "WHERE token_hash IS NULL"
    )
    op.alter_column(
        "public_session",
        "token_hash",
        existing_type=sa.LargeBinary(),
        nullable=False,
    )
    op.drop_column("public_session", "customer_account_id")
    op.drop_column("message", "read_by_owner_at")
    op.drop_index("customer_auth_session_account_ix", table_name="customer_auth_session")
    op.drop_table("customer_auth_session")
    op.drop_table("customer_account")
