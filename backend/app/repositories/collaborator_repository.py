from sqlalchemy.ext.asyncio import AsyncSession


class CollaboratorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

