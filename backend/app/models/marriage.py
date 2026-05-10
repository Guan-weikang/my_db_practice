from datetime import date

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Marriage(Base):
    __tablename__ = "marriage"
    __table_args__ = (
        PrimaryKeyConstraint("tree_id", "member_id_1", "member_id_2"),
        ForeignKeyConstraint(["tree_id", "member_id_1"], ["member.tree_id", "member.member_id"]),
        ForeignKeyConstraint(["tree_id", "member_id_2"], ["member.tree_id", "member.member_id"]),
        CheckConstraint("member_id_1 <> member_id_2", name="chk_marriage_distinct"),
        CheckConstraint("member_id_1 < member_id_2", name="chk_marriage_order"),
        CheckConstraint("status IN ('active', 'ended')", name="chk_marriage_status"),
        Index("idx_marriage_tree_member1", "tree_id", "member_id_1"),
        Index("idx_marriage_tree_member2", "tree_id", "member_id_2"),
    )

    tree_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    member_id_1: Mapped[int] = mapped_column(BigInteger, nullable=False)
    member_id_2: Mapped[int] = mapped_column(BigInteger, nullable=False)
    married_at: Mapped[date | None] = mapped_column(Date)
    ended_at: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active", nullable=False)
