"""Allow evidence to cite a tenant's saved shop profile."""

from typing import Sequence, Union

from alembic import op

revision: str = "20261102_2137"
down_revision: Union[str, None] = "79cdcda6ea28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        op.f("ck_evidence_evidence_source_kind_check"),
        "evidence",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_evidence_evidence_source_kind_check"),
        "evidence",
        "source_kind IN ('business', 'product', 'variant', 'policy', 'order', 'transcript', 'media')",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_evidence_evidence_source_kind_check"),
        "evidence",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_evidence_evidence_source_kind_check"),
        "evidence",
        "source_kind IN ('product', 'variant', 'policy', 'order', 'transcript', 'media')",
    )
