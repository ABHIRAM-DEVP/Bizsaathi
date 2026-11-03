"""Add email/password credentials to local development owner accounts."""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20261103_0015"
down_revision: Union[str, None] = "20261102_2137"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("app_user", sa.Column("local_email", sa.String(length=320), nullable=True))
    op.add_column("app_user", sa.Column("local_password_hash", sa.LargeBinary(), nullable=True))
    op.create_unique_constraint("uq_app_user_local_email", "app_user", ["local_email"])
    op.create_check_constraint(
        op.f("ck_app_user_app_user_local_credentials_check"),
        "app_user",
        "(identity_type = 'phone' AND local_email IS NULL AND local_password_hash IS NULL) "
        "OR (identity_type = 'local_dev' AND phone_e164 IS NULL AND "
        "((local_email IS NULL AND local_password_hash IS NULL) "
        "OR (local_email IS NOT NULL AND local_password_hash IS NOT NULL)))",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_app_user_app_user_local_credentials_check"), "app_user", type_="check")
    op.drop_constraint("uq_app_user_local_email", "app_user", type_="unique")
    op.drop_column("app_user", "local_password_hash")
    op.drop_column("app_user", "local_email")
