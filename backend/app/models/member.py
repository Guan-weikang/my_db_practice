from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Member(Base):
    __tablename__ = "member"
    __table_args__ = (UniqueConstraint("tree_id", "member_id"),)

    member_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tree_id: Mapped[int] = mapped_column(ForeignKey("family_tree.tree_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date)
    death_date: Mapped[date | None] = mapped_column(Date)
    generation_no: Mapped[int | None]
    generation_name: Mapped[str | None] = mapped_column(String(50))
    biography: Mapped[str | None] = mapped_column(Text)
    is_alive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

