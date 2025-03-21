from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import query

from .models import Reader, Librarian


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_reader_by_id(self, reader_id: UUID) -> Reader | None:
        return await self.session.get(Reader, reader_id)

    async def get_librarian_by_id(self, librarian_id: UUID) -> Librarian | None:
        return await self.session.get(Librarian, librarian_id)

    async def get_reader_by_email(self, email: str) -> Reader | None:
        return await self.session.query(Reader).filter(Reader.user.email == email).first()

    async def get_librarian_by_email(self, email: str) -> Librarian | None:
        return await self.session.query(Librarian).filter(Librarian.user.email == email).first()

    