"""Support local development identities without unverified phone numbers.

Revision ID: 3b7c9f1d2a44
Revises: 5aa6ba177a21
Create Date: 2026-10-31 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "3b7c9f1d2a44"
down_revision: Union[str, None] = "5aa6ba177a21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_user",
        sa.Column("identity_type", sa.String(length=20), server_default="phone", nullable=False),
    )
    op.alter_column("app_user", "phone_e164", existing_type=sa.String(length=16), nullable=True)
    op.create_check_constraint(
        "ck_app_user_identity_type_check",
        "app_user",
        "identity_type IN ('phone', 'local_dev')",
    )
    op.create_check_constraint(
        "ck_app_user_phone_identity_check",
        "app_user",
        "(identity_type = 'phone' AND phone_e164 IS NOT NULL) "
        "OR (identity_type = 'local_dev' AND phone_e164 IS NULL)",
    )


def downgrade() -> None:
    connection = op.get_bind()
    local_accounts = connection.execute(
        sa.text("SELECT count(*) FROM app_user WHERE identity_type = 'local_dev'")
    ).scalar_one()
    if local_accounts:
        raise RuntimeError("Cannot downgrade while local development accounts exist.")

    op.drop_constraint("ck_app_user_phone_identity_check", "app_user", type_="check")
    op.drop_constraint("ck_app_user_identity_type_check", "app_user", type_="check")
    op.drop_column("app_user", "identity_type")
    op.alter_column("app_user", "phone_e164", existing_type=sa.String(length=16), nullable=False)
