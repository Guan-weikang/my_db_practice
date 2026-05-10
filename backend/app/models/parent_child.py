from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ParentChild(Base):
    __tablename__ = "parent_child"
    __table_args__ = (
        PrimaryKeyConstraint("tree_id", "parent_member_id", "child_member_id", "parent_role"),
        UniqueConstraint("tree_id", "child_member_id", "parent_role"),
        ForeignKeyConstraint(["tree_id", "parent_member_id"], ["member.tree_id", "member.member_id"]),
        ForeignKeyConstraint(["tree_id", "child_member_id"], ["member.tree_id", "member.member_id"]),
    )

    tree_id: Mapped[int] = mapped_column(nullable=False)
    parent_member_id: Mapped[int] = mapped_column(nullable=False)
    child_member_id: Mapped[int] = mapped_column(nullable=False)
    parent_role: Mapped[str] = mapped_column(String(10), nullable=False)

