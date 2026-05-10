from sqlalchemy.ext.asyncio import AsyncSession


class FamilyTreeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

