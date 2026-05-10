from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TreeCollaborator(Base):
    __tablename__ = "tree_collaborator"
    __table_args__ = (
        PrimaryKeyConstraint("tree_id", "user_id"),
    )

    tree_id: Mapped[int] = mapped_column(ForeignKey("family_tree.tree_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.user_id"), nullable=False)
    access_role: Mapped[str] = mapped_column(String(20), nullable=False)
    invited_by: Mapped[int] = mapped_column(ForeignKey("user_account.user_id"), nullable=False)
    invited_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

