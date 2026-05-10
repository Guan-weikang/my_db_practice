from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_account import UserAccount


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_username(self, username: str) -> UserAccount | None:
        result = await self.session.execute(select(UserAccount).where(UserAccount.username == username))
        return result.scalar_one_or_none()

