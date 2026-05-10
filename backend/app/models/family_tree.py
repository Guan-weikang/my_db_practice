from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FamilyTree(Base):
    __tablename__ = "family_tree"
    __table_args__ = (
        Index("idx_family_tree_creator", "creator_user_id"),
    )

    tree_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tree_name: Mapped[str] = mapped_column(String(100), nullable=False)
    surname: Mapped[str] = mapped_column(String(50), nullable=False)
    compiled_at: Mapped[date | None] = mapped_column(Date)
    creator_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_account.user_id"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
