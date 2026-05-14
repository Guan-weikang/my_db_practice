from collections.abc import Mapping

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tree_collaborator import TreeCollaborator
from app.models.user_account import UserAccount


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

    async def delete_by_tree_id(self, tree_id: int) -> None:
        await self.session.execute(delete(TreeCollaborator).where(TreeCollaborator.tree_id == tree_id))
        await self.session.flush()

    async def count_for_tree(self, tree_id: int) -> int:
        result = await self.session.execute(select(func.count()).select_from(TreeCollaborator).where(TreeCollaborator.tree_id == tree_id))
        return int(result.scalar_one())

    async def list_for_tree(
        self,
        tree_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[dict[str, object | None]]:
        result = await self.session.execute(
            select(
                TreeCollaborator.user_id,
                UserAccount.username,
                UserAccount.display_name,
                TreeCollaborator.access_role,
                TreeCollaborator.status,
                TreeCollaborator.invited_by,
                TreeCollaborator.invited_at,
            )
            .join(UserAccount, UserAccount.user_id == TreeCollaborator.user_id)
            .where(TreeCollaborator.tree_id == tree_id)
            .order_by(TreeCollaborator.invited_at.desc(), TreeCollaborator.user_id.asc())
            .offset(offset)
            .limit(limit)
        )
        return [dict(row._mapping) for row in result.all()]

    async def get_by_tree_and_user(self, *, tree_id: int, user_id: int) -> TreeCollaborator | None:
        result = await self.session.execute(
            select(TreeCollaborator).where(
                TreeCollaborator.tree_id == tree_id,
                TreeCollaborator.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        tree_id: int,
        user_id: int,
        invited_by: int,
        access_role: str,
        status: str = "active",
    ) -> TreeCollaborator:
        collaborator = TreeCollaborator(
            tree_id=tree_id,
            user_id=user_id,
            invited_by=invited_by,
            access_role=access_role,
            status=status,
        )
        self.session.add(collaborator)
        await self.session.flush()
        return collaborator

    async def update(self, collaborator: TreeCollaborator, values: Mapping[str, object | None]) -> TreeCollaborator:
        for field_name, value in values.items():
            setattr(collaborator, field_name, value)
        await self.session.flush()
        return collaborator
