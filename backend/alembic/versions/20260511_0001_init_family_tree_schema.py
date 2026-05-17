"""init family tree schema

Revision ID: 20260511_0001
Revises:
Create Date: 2026-05-11 00:00:01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260511_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "user_account",
        sa.Column("user_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'active'"), nullable=False),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="chk_user_status"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "family_tree",
        sa.Column("tree_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tree_name", sa.String(length=100), nullable=False),
        sa.Column("surname", sa.String(length=50), nullable=False),
        sa.Column("compiled_at", sa.Date(), nullable=True),
        sa.Column("creator_user_id", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["creator_user_id"], ["user_account.user_id"], name="fk_tree_creator"),
        sa.PrimaryKeyConstraint("tree_id"),
    )
    op.create_index("idx_family_tree_creator", "family_tree", ["creator_user_id"], unique=False)

    op.create_table(
        "tree_collaborator",
        sa.Column("tree_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("access_role", sa.String(length=20), nullable=False),
        sa.Column("invited_by", sa.BigInteger(), nullable=False),
        sa.Column("invited_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'active'"), nullable=False),
        sa.CheckConstraint("access_role IN ('collaborator', 'reader')", name="chk_collab_role"),
        sa.CheckConstraint("status IN ('active', 'revoked', 'pending')", name="chk_collab_status"),
        sa.ForeignKeyConstraint(["invited_by"], ["user_account.user_id"], name="fk_collab_invited_by"),
        sa.ForeignKeyConstraint(["tree_id"], ["family_tree.tree_id"], name="fk_collab_tree"),
        sa.ForeignKeyConstraint(["user_id"], ["user_account.user_id"], name="fk_collab_user"),
        sa.PrimaryKeyConstraint("tree_id", "user_id", name="pk_tree_collaborator"),
    )
    op.create_index(
        "idx_tree_collaborator_user_status_tree",
        "tree_collaborator",
        ["user_id", "status", "tree_id"],
        unique=False,
    )
    op.create_index(
        "idx_tree_collaborator_tree_status_user",
        "tree_collaborator",
        ["tree_id", "status", "user_id"],
        unique=False,
    )

    op.create_table(
        "member",
        sa.Column("member_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tree_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("gender", sa.String(length=10), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("death_date", sa.Date(), nullable=True),
        sa.Column("generation_no", sa.Integer(), nullable=True),
        sa.Column("generation_name", sa.String(length=50), nullable=True),
        sa.Column("biography", sa.Text(), nullable=True),
        sa.Column("is_alive", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("birth_date IS NULL OR death_date IS NULL OR death_date >= birth_date", name="chk_member_life_span"),
        sa.CheckConstraint("gender IN ('male', 'female', 'unknown')", name="chk_member_gender"),
        sa.CheckConstraint("generation_no IS NULL OR generation_no > 0", name="chk_generation_no_positive"),
        sa.CheckConstraint("is_alive = FALSE OR death_date IS NULL", name="chk_member_alive_death"),
        sa.ForeignKeyConstraint(["tree_id"], ["family_tree.tree_id"], name="fk_member_tree"),
        sa.PrimaryKeyConstraint("member_id"),
        sa.UniqueConstraint("tree_id", "member_id", name="uq_member_tree_member"),
    )
    op.create_index("idx_member_tree_name", "member", ["tree_id", "name"], unique=False)
    op.create_index("idx_member_tree_generation", "member", ["tree_id", "generation_no"], unique=False)
    op.create_index(
        "idx_member_tree_generation_birth_member",
        "member",
        ["tree_id", sa.text("generation_no ASC NULLS LAST"), sa.text("birth_date ASC NULLS LAST"), "member_id"],
        unique=False,
    )
    op.create_index("idx_member_tree_gender_birth", "member", ["tree_id", "gender", "birth_date"], unique=False)
    op.create_index(
        "idx_member_name_trgm",
        "member",
        ["name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )

    op.create_table(
        "parent_child",
        sa.Column("tree_id", sa.BigInteger(), nullable=False),
        sa.Column("parent_member_id", sa.BigInteger(), nullable=False),
        sa.Column("child_member_id", sa.BigInteger(), nullable=False),
        sa.Column("parent_role", sa.String(length=10), nullable=False),
        sa.CheckConstraint("parent_member_id <> child_member_id", name="chk_parent_not_self"),
        sa.CheckConstraint("parent_role IN ('father', 'mother')", name="chk_parent_role"),
        sa.ForeignKeyConstraint(
            ["tree_id", "child_member_id"],
            ["member.tree_id", "member.member_id"],
            name="fk_pc_child",
        ),
        sa.ForeignKeyConstraint(
            ["tree_id", "parent_member_id"],
            ["member.tree_id", "member.member_id"],
            name="fk_pc_parent",
        ),
        sa.PrimaryKeyConstraint("tree_id", "parent_member_id", "child_member_id", "parent_role", name="pk_parent_child"),
        sa.UniqueConstraint("tree_id", "child_member_id", "parent_role", name="uq_child_parent_role"),
    )
    op.create_index("idx_parent_child_tree_parent", "parent_child", ["tree_id", "parent_member_id"], unique=False)
    op.create_index("idx_parent_child_tree_child", "parent_child", ["tree_id", "child_member_id"], unique=False)

    op.create_table(
        "marriage",
        sa.Column("tree_id", sa.BigInteger(), nullable=False),
        sa.Column("member_id_1", sa.BigInteger(), nullable=False),
        sa.Column("member_id_2", sa.BigInteger(), nullable=False),
        sa.Column("married_at", sa.Date(), nullable=True),
        sa.Column("ended_at", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'active'")),
        sa.CheckConstraint("member_id_1 < member_id_2", name="chk_marriage_order"),
        sa.CheckConstraint("member_id_1 <> member_id_2", name="chk_marriage_distinct"),
        sa.CheckConstraint("status IN ('active', 'ended')", name="chk_marriage_status"),
        sa.ForeignKeyConstraint(
            ["tree_id", "member_id_1"],
            ["member.tree_id", "member.member_id"],
            name="fk_marriage_member_1",
        ),
        sa.ForeignKeyConstraint(
            ["tree_id", "member_id_2"],
            ["member.tree_id", "member.member_id"],
            name="fk_marriage_member_2",
        ),
        sa.PrimaryKeyConstraint("tree_id", "member_id_1", "member_id_2", name="pk_marriage"),
    )
    op.create_index("idx_marriage_tree_member1", "marriage", ["tree_id", "member_id_1"], unique=False)
    op.create_index("idx_marriage_tree_member2", "marriage", ["tree_id", "member_id_2"], unique=False)
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

    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_parent_child_cycle()
        RETURNS TRIGGER AS $$
        DECLARE
            cycle_found BOOLEAN;
        BEGIN
            IF NEW.parent_member_id = NEW.child_member_id THEN
                RAISE EXCEPTION 'parent_member_id and child_member_id cannot be identical';
            END IF;

            WITH RECURSIVE ancestor_path AS (
                SELECT
                    pc.tree_id,
                    pc.parent_member_id,
                    pc.child_member_id
                FROM parent_child pc
                WHERE pc.tree_id = NEW.tree_id
                  AND pc.child_member_id = NEW.parent_member_id

                UNION ALL

                SELECT
                    pc.tree_id,
                    pc.parent_member_id,
                    pc.child_member_id
                FROM ancestor_path ap
                JOIN parent_child pc
                  ON pc.tree_id = ap.tree_id
                 AND pc.child_member_id = ap.parent_member_id
            )
            SELECT EXISTS (
                SELECT 1
                FROM ancestor_path
                WHERE parent_member_id = NEW.child_member_id
            )
            INTO cycle_found;

            IF cycle_found THEN
                RAISE EXCEPTION
                    'adding parent-child relation (tree_id=%, parent_member_id=%, child_member_id=%) would create an ancestor cycle',
                    NEW.tree_id, NEW.parent_member_id, NEW.child_member_id;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_prevent_parent_child_cycle
        BEFORE INSERT OR UPDATE ON parent_child
        FOR EACH ROW
        EXECUTE FUNCTION prevent_parent_child_cycle();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_parent_child_cycle ON parent_child")
    op.execute("DROP FUNCTION IF EXISTS prevent_parent_child_cycle()")

    op.drop_index("idx_marriage_tree_member2", table_name="marriage")
    op.drop_index("idx_marriage_tree_member1", table_name="marriage")
    op.drop_index("idx_marriage_tree_member2_active", table_name="marriage")
    op.drop_index("idx_marriage_tree_member1_active", table_name="marriage")
    op.drop_table("marriage")

    op.drop_index("idx_parent_child_tree_child", table_name="parent_child")
    op.drop_index("idx_parent_child_tree_parent", table_name="parent_child")
    op.drop_table("parent_child")

    op.drop_index("idx_member_name_trgm", table_name="member")
    op.drop_index("idx_member_tree_gender_birth", table_name="member")
    op.drop_index("idx_member_tree_generation_birth_member", table_name="member")
    op.drop_index("idx_member_tree_generation", table_name="member")
    op.drop_index("idx_member_tree_name", table_name="member")
    op.drop_table("member")

    op.drop_index("idx_tree_collaborator_tree_status_user", table_name="tree_collaborator")
    op.drop_index("idx_tree_collaborator_user_status_tree", table_name="tree_collaborator")
    op.drop_table("tree_collaborator")

    op.drop_index("idx_family_tree_creator", table_name="family_tree")
    op.drop_table("family_tree")

    op.drop_table("user_account")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
