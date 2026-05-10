from datetime import date

from sqlalchemy import Date, ForeignKeyConstraint, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Marriage(Base):
    __tablename__ = "marriage"
    __table_args__ = (
        PrimaryKeyConstraint("tree_id", "member_id_1", "member_id_2"),
        ForeignKeyConstraint(["tree_id", "member_id_1"], ["member.tree_id", "member.member_id"]),
        ForeignKeyConstraint(["tree_id", "member_id_2"], ["member.tree_id", "member.member_id"]),
    )

    tree_id: Mapped[int] = mapped_column(nullable=False)
    member_id_1: Mapped[int] = mapped_column(nullable=False)
    member_id_2: Mapped[int] = mapped_column(nullable=False)
    married_at: Mapped[date | None] = mapped_column(Date)
    ended_at: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(20), default="active")

