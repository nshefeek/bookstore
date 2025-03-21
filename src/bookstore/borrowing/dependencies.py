from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from bookstore.database.session import get_session
from bookstore.books.repositories import BookRepository

from .services import BorrowService
from .repositories import BorrowRecordRepository, BookRequestRepository


async def get_borrow_service(
    session: AsyncSession = Depends(get_session),
) -> BorrowService:
    book_request_repository = BookRequestRepository(session)
    borrow_record_repository = BorrowRecordRepository(session)
    book_repository = BookRepository(session)
    return BorrowService(
        borrow_record_repository=borrow_record_repository,
        book_request_repository=book_request_repository,
        book_repository=book_repository,
    )