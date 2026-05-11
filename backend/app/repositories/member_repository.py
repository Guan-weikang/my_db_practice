from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member


class MemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def count_by_tree_id(self, tree_id: int) -> int:
        result = await self.session.execute(select(func.count(Member.member_id)).where(Member.tree_id == tree_id))
        return int(result.scalar_one())
