from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tree_collaborator import TreeCollaborator


class CollaboratorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_role(self, *, tree_id: int, user_id: int) -> str | None:
        result = await self.session.execute(
            select(TreeCollaborator.access_role).where(
                TreeCollaborator.tree_id == tree_id,
                TreeCollaborator.user_id == user_id,
                TreeCollaborator.status == "active",
            )
        )
        return result.scalar_one_or_none()
