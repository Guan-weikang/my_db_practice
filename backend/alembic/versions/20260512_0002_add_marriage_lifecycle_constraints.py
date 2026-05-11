"""add marriage lifecycle constraints

Revision ID: 20260512_0002
Revises: 20260511_0001
Create Date: 2026-05-12 00:20:00
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260512_0002"
down_revision: Union[str, Sequence[str], None] = "20260511_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "chk_marriage_date_order",
        "marriage",
        "married_at IS NULL OR ended_at IS NULL OR ended_at >= married_at",
    )
    op.create_check_constraint(
        "chk_marriage_active_ended_at",
        "marriage",
        "status <> 'active' OR ended_at IS NULL",
    )
    op.create_check_constraint(
        "chk_marriage_ended_requires_date",
        "marriage",
        "status <> 'ended' OR ended_at IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint("chk_marriage_ended_requires_date", "marriage", type_="check")
    op.drop_constraint("chk_marriage_active_ended_at", "marriage", type_="check")
    op.drop_constraint("chk_marriage_date_order", "marriage", type_="check")

