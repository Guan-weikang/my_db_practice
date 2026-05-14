from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_account import UserAccount


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_username(self, username: str) -> UserAccount | None:
        result = await self.session.execute(select(UserAccount).where(UserAccount.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserAccount | None:
        result = await self.session.execute(select(UserAccount).where(UserAccount.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> UserAccount | None:
        result = await self.session.execute(select(UserAccount).where(UserAccount.user_id == user_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        username: str,
        password_hash: str,
        display_name: str,
        email: str | None,
        status: str = "active",
    ) -> UserAccount:
        user = UserAccount(
            username=username,
            password_hash=password_hash,
            display_name=display_name,
            email=email,
            status=status,
        )
        self.session.add(user)
        await self.session.flush()
        return user
