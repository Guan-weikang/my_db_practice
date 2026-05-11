from collections.abc import Mapping
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member


class MemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_tree_id(
        self,
        tree_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Member]:
        result = await self.session.execute(
            select(Member)
            .where(Member.tree_id == tree_id)
            .order_by(Member.generation_no.asc().nulls_last(), Member.birth_date.asc().nulls_last(), Member.member_id.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_tree_and_member_id(self, *, tree_id: int, member_id: int) -> Member | None:
        result = await self.session.execute(
            select(Member).where(Member.tree_id == tree_id, Member.member_id == member_id)
        )
        return result.scalar_one_or_none()

    async def count_by_tree_id(self, tree_id: int) -> int:
        result = await self.session.execute(select(func.count(Member.member_id)).where(Member.tree_id == tree_id))
        return int(result.scalar_one())

    async def create(self, *, tree_id: int, values: Mapping[str, object | None]) -> Member:
        member = Member(tree_id=tree_id, **values)
        self.session.add(member)
        await self.session.flush()
        return member

    async def update(self, member: Member, values: Mapping[str, object | None]) -> Member:
        for field_name, value in values.items():
            setattr(member, field_name, value)
        member.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.session.flush()
        return member

    async def delete(self, member: Member) -> None:
        await self.session.delete(member)
