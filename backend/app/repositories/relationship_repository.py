from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marriage import Marriage
from app.models.member import Member
from app.models.parent_child import ParentChild

class RelationshipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_parent_child(
        self,
        *,
        tree_id: int,
        parent_member_id: int,
        child_member_id: int,
        parent_role: str,
    ) -> ParentChild | None:
        result = await self.session.execute(
            select(ParentChild).where(
                ParentChild.tree_id == tree_id,
                ParentChild.parent_member_id == parent_member_id,
                ParentChild.child_member_id == child_member_id,
                ParentChild.parent_role == parent_role,
            )
        )
        return result.scalar_one_or_none()

    async def get_parent_by_child_and_role(self, *, tree_id: int, child_member_id: int, parent_role: str) -> ParentChild | None:
        result = await self.session.execute(
            select(ParentChild).where(
                ParentChild.tree_id == tree_id,
                ParentChild.child_member_id == child_member_id,
                ParentChild.parent_role == parent_role,
            )
        )
        return result.scalar_one_or_none()

    async def create_parent_child(self, *, tree_id: int, parent_member_id: int, child_member_id: int, parent_role: str) -> ParentChild:
        relation = ParentChild(
            tree_id=tree_id,
            parent_member_id=parent_member_id,
            child_member_id=child_member_id,
            parent_role=parent_role,
        )
        self.session.add(relation)
        await self.session.flush()
        return relation

    async def delete_parent_child(self, relation: ParentChild) -> None:
        await self.session.delete(relation)

    async def list_parents_for_member(self, *, tree_id: int, member_id: int) -> list[dict[str, object | None]]:
        parent_member = Member.__table__.alias("parent_member")
        result = await self.session.execute(
            select(
                ParentChild.parent_member_id,
                ParentChild.parent_role,
                parent_member.c.name,
                parent_member.c.gender,
                parent_member.c.birth_date,
                parent_member.c.death_date,
                parent_member.c.generation_no,
                parent_member.c.generation_name,
            )
            .select_from(ParentChild)
            .join(
                parent_member,
                (parent_member.c.tree_id == ParentChild.tree_id) & (parent_member.c.member_id == ParentChild.parent_member_id),
            )
            .where(ParentChild.tree_id == tree_id, ParentChild.child_member_id == member_id)
            .order_by(ParentChild.parent_role.asc(), ParentChild.parent_member_id.asc())
        )
        return [dict(row._mapping) for row in result.all()]

    async def list_children_for_member(self, *, tree_id: int, member_id: int) -> list[dict[str, object | None]]:
        child_member = Member.__table__.alias("child_member")
        result = await self.session.execute(
            select(
                ParentChild.child_member_id,
                ParentChild.parent_role,
                child_member.c.name,
                child_member.c.gender,
                child_member.c.birth_date,
                child_member.c.death_date,
                child_member.c.generation_no,
                child_member.c.generation_name,
            )
            .select_from(ParentChild)
            .join(
                child_member,
                (child_member.c.tree_id == ParentChild.tree_id) & (child_member.c.member_id == ParentChild.child_member_id),
            )
            .where(ParentChild.tree_id == tree_id, ParentChild.parent_member_id == member_id)
            .order_by(child_member.c.birth_date.asc().nulls_last(), ParentChild.child_member_id.asc())
        )
        return [dict(row._mapping) for row in result.all()]

    async def would_create_cycle(self, *, tree_id: int, parent_member_id: int, child_member_id: int) -> bool:
        seed = (
            select(
                ParentChild.parent_member_id.label("parent_member_id"),
                ParentChild.child_member_id.label("child_member_id"),
            )
            .where(ParentChild.tree_id == tree_id, ParentChild.child_member_id == parent_member_id)
            .cte(name="ancestor_path", recursive=True)
        )
        recursive = seed.union_all(
            select(
                ParentChild.parent_member_id.label("parent_member_id"),
                ParentChild.child_member_id.label("child_member_id"),
            )
            .select_from(seed)
            .join(
                ParentChild,
                (ParentChild.tree_id == tree_id) & (ParentChild.child_member_id == seed.c.parent_member_id),
            )
        )
        result = await self.session.execute(
            select(recursive.c.parent_member_id).where(recursive.c.parent_member_id == child_member_id).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_marriage(self, *, tree_id: int, member_id_1: int, member_id_2: int) -> Marriage | None:
        result = await self.session.execute(
            select(Marriage).where(
                Marriage.tree_id == tree_id,
                Marriage.member_id_1 == member_id_1,
                Marriage.member_id_2 == member_id_2,
            )
        )
        return result.scalar_one_or_none()

    async def create_marriage(
        self,
        *,
        tree_id: int,
        member_id_1: int,
        member_id_2: int,
        married_at,
        ended_at,
        status: str,
    ) -> Marriage:
        marriage = Marriage(
            tree_id=tree_id,
            member_id_1=member_id_1,
            member_id_2=member_id_2,
            married_at=married_at,
            ended_at=ended_at,
            status=status,
        )
        self.session.add(marriage)
        await self.session.flush()
        return marriage

    async def update_marriage(self, marriage: Marriage, *, married_at, ended_at, status: str) -> Marriage:
        marriage.married_at = married_at
        marriage.ended_at = ended_at
        marriage.status = status
        await self.session.flush()
        return marriage

    async def delete_marriage(self, marriage: Marriage) -> None:
        await self.session.delete(marriage)

    async def list_spouses_for_member(self, *, tree_id: int, member_id: int) -> list[dict[str, object | None]]:
        spouse_member = Member.__table__.alias("spouse_member")
        result = await self.session.execute(
            select(
                spouse_member.c.member_id.label("spouse_member_id"),
                spouse_member.c.name,
                spouse_member.c.gender,
                spouse_member.c.birth_date,
                spouse_member.c.death_date,
                spouse_member.c.generation_no,
                spouse_member.c.generation_name,
                Marriage.married_at,
                Marriage.ended_at,
                Marriage.status,
            )
            .select_from(Marriage)
            .join(
                spouse_member,
                (
                    (spouse_member.c.tree_id == Marriage.tree_id)
                    & (
                        ((Marriage.member_id_1 == member_id) & (spouse_member.c.member_id == Marriage.member_id_2))
                        | ((Marriage.member_id_2 == member_id) & (spouse_member.c.member_id == Marriage.member_id_1))
                    )
                ),
            )
            .where(Marriage.tree_id == tree_id, or_(Marriage.member_id_1 == member_id, Marriage.member_id_2 == member_id))
            .order_by(spouse_member.c.member_id.asc())
        )
        return [dict(row._mapping) for row in result.all()]

    async def delete_relations_for_member(self, *, tree_id: int, member_id: int) -> None:
        await self.session.execute(
            delete(ParentChild).where(
                ParentChild.tree_id == tree_id,
                or_(ParentChild.parent_member_id == member_id, ParentChild.child_member_id == member_id),
            )
        )
        await self.session.execute(
            delete(Marriage).where(
                Marriage.tree_id == tree_id,
                or_(Marriage.member_id_1 == member_id, Marriage.member_id_2 == member_id),
            )
        )
