from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    PrimaryKeyConstraint,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TreeCollaborator(Base):
    __tablename__ = "tree_collaborator"
    __table_args__ = (
        PrimaryKeyConstraint("tree_id", "user_id"),
        CheckConstraint("access_role IN ('collaborator', 'reader')", name="chk_collab_role"),
        CheckConstraint("status IN ('active', 'revoked', 'pending')", name="chk_collab_status"),
        Index("idx_tree_collaborator_user_status_tree", "user_id", "status", "tree_id"),
        Index("idx_tree_collaborator_tree_status_user", "tree_id", "status", "user_id"),
    )

    tree_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("family_tree.tree_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_account.user_id"), nullable=False)
    access_role: Mapped[str] = mapped_column(String(20), nullable=False)
    invited_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_account.user_id"), nullable=False)
    invited_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active", nullable=False)
