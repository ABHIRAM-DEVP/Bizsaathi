"""Add source and synthetic customer labels to conversations.

Revision ID: 20261102_0010
Revises: 3b7c9f1d2a44
Create Date: 2026-11-02 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20261102_0010"
down_revision: Union[str, None] = "3b7c9f1d2a44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation",
        sa.Column("source", sa.String(length=20), server_default="public", nullable=False),
    )
    op.add_column("conversation", sa.Column("customer_label", sa.String(length=100), nullable=True))
    op.create_check_constraint(
        "ck_conversation_conversation_source_check",
        "conversation",
        "source IN ('public', 'demo')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_conversation_conversation_source_check", "conversation", type_="check")
    op.drop_column("conversation", "customer_label")
    op.drop_column("conversation", "source")
