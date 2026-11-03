"""Create a shared rate-limit bucket table.

Revision ID: 79cdcda6ea28
Revises: 6e926e695573
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "79cdcda6ea28"
down_revision: Union[str, None] = "6e926e695573"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "public_rate_limit_bucket",
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "request_count > 0",
            name=op.f("ck_public_rate_limit_bucket_public_rate_limit_count_check"),
        ),
        sa.PrimaryKeyConstraint("key_hash", name=op.f("pk_public_rate_limit_bucket")),
    )
    op.create_index(
        "public_rate_limit_window_ix",
        "public_rate_limit_bucket",
        ["window_start"],
    )


def downgrade() -> None:
    op.drop_index("public_rate_limit_window_ix", table_name="public_rate_limit_bucket")
    op.drop_table("public_rate_limit_bucket")
