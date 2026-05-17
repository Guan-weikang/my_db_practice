"""add query optimization indexes

Revision ID: 20260515_0003
Revises: 20260512_0002
Create Date: 2026-05-15 00:03:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260515_0003"
down_revision: Union[str, Sequence[str], None] = "20260512_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "idx_member_tree_generation_birth_member",
        "member",
        ["tree_id", sa.text("generation_no ASC NULLS LAST"), sa.text("birth_date ASC NULLS LAST"), "member_id"],
        unique=False,
    )
    op.create_index(
        "idx_marriage_tree_member1_active",
        "marriage",
        ["tree_id", "member_id_1"],
        unique=False,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "idx_marriage_tree_member2_active",
        "marriage",
        ["tree_id", "member_id_2"],
        unique=False,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("idx_marriage_tree_member2_active", table_name="marriage")
    op.drop_index("idx_marriage_tree_member1_active", table_name="marriage")
    op.drop_index("idx_member_tree_generation_birth_member", table_name="member")
