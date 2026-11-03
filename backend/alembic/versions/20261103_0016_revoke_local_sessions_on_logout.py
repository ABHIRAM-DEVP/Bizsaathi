"""Revoke persistent local development sessions when an owner signs out."""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20261103_0016"
down_revision: Union[str, None] = "20261103_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_user",
        sa.Column("local_session_version", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_check_constraint(
        op.f("ck_app_user_app_user_local_session_version_check"),
        "app_user",
        "local_session_version >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_app_user_app_user_local_session_version_check"),
        "app_user",
        type_="check",
    )
    op.drop_column("app_user", "local_session_version")
