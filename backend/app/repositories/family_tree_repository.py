from sqlalchemy import case, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.family_tree import FamilyTree
from app.models.tree_collaborator import TreeCollaborator


class FamilyTreeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, tree_id: int) -> FamilyTree | None:
        result = await self.session.execute(select(FamilyTree).where(FamilyTree.tree_id == tree_id))
        return result.scalar_one_or_none()

    async def list_accessible_for_user(self, user_id: int) -> list[dict[str, object | None]]:
        access_role = case(
            (FamilyTree.creator_user_id == user_id, literal("creator")),
            else_=TreeCollaborator.access_role,
        )
        result = await self.session.execute(
            select(
                FamilyTree.tree_id,
                FamilyTree.tree_name,
                FamilyTree.surname,
                FamilyTree.compiled_at,
                FamilyTree.description,
                access_role.label("access_role"),
            )
            .outerjoin(
                TreeCollaborator,
                (TreeCollaborator.tree_id == FamilyTree.tree_id)
                & (TreeCollaborator.user_id == user_id)
                & (TreeCollaborator.status == "active"),
            )
            .where(
                or_(
                    FamilyTree.creator_user_id == user_id,
                    TreeCollaborator.user_id.is_not(None),
                )
            )
            .order_by(FamilyTree.tree_id.asc())
        )
        return [dict(row._mapping) for row in result.all()]
