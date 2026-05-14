from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Member(Base):
    __tablename__ = "member"
    __table_args__ = (
        UniqueConstraint("tree_id", "member_id", name="uq_member_tree_member"),
        CheckConstraint("gender IN ('male', 'female', 'unknown')", name="chk_member_gender"),
        CheckConstraint(
            "birth_date IS NULL OR death_date IS NULL OR death_date >= birth_date",
            name="chk_member_life_span",
        ),
        CheckConstraint("is_alive = FALSE OR death_date IS NULL", name="chk_member_alive_death"),
        CheckConstraint("generation_no IS NULL OR generation_no > 0", name="chk_generation_no_positive"),
        Index("idx_member_tree_name", "tree_id", "name"),
        Index("idx_member_tree_generation", "tree_id", "generation_no"),
        Index("idx_member_tree_gender_birth", "tree_id", "gender", "birth_date"),
        Index(
            "idx_member_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    member_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tree_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("family_tree.tree_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date)
    death_date: Mapped[date | None] = mapped_column(Date)
    generation_no: Mapped[int | None] = mapped_column(Integer)
    generation_name: Mapped[str | None] = mapped_column(String(50))
    biography: Mapped[str | None] = mapped_column(Text)
    is_alive: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa.true(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
