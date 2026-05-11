from collections.abc import Mapping
from datetime import datetime

from sqlalchemy import case, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.family_tree import FamilyTree
from app.models.tree_collaborator import TreeCollaborator


class FamilyTreeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, tree_id: int) -> FamilyTree | None:
        result = await self.session.execute(select(FamilyTree).where(FamilyTree.tree_id == tree_id))
        return result.scalar_one_or_none()

    async def count_accessible_for_user(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(FamilyTree.tree_id.distinct()))
            .select_from(FamilyTree)
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
        )
        return int(result.scalar_one())

    async def list_accessible_for_user(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[dict[str, object | None]]:
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
            .order_by(FamilyTree.updated_at.desc(), FamilyTree.tree_id.desc())
            .offset(offset)
            .limit(limit)
        )
        return [dict(row._mapping) for row in result.all()]

    async def create(
        self,
        *,
        tree_name: str,
        surname: str,
        creator_user_id: int,
        compiled_at,
        description: str | None,
    ) -> FamilyTree:
        tree = FamilyTree(
            tree_name=tree_name,
            surname=surname,
            creator_user_id=creator_user_id,
            compiled_at=compiled_at,
            description=description,
        )
        self.session.add(tree)
        await self.session.flush()
        return tree

    async def update(self, tree: FamilyTree, values: Mapping[str, object | None]) -> FamilyTree:
        for field_name, value in values.items():
            setattr(tree, field_name, value)
        tree.updated_at = datetime.utcnow()
        await self.session.flush()
        return tree

    async def delete(self, tree: FamilyTree) -> None:
        await self.session.delete(tree)
