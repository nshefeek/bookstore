from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from bookstore.database.session import get_session

from .services import BookService, BookCategoryService
from .repositories import BookRepository, BookTitleRepository, BookCategoryRepository

async def get_book_service(session: AsyncSession = Depends(get_session)) -> BookService:
    book_repository = BookRepository(session)
    book_title_repository = BookTitleRepository(session)
    book_category_repository = BookCategoryRepository(session)
    return BookService(
        book_repository=book_repository,
        book_title_repository=book_title_repository,
        book_category_repository=book_category_repository
    )

async def get_category_service(session: AsyncSession = Depends(get_session)) -> BookCategoryService:
    book_category_repository = BookCategoryRepository(session)
    return BookCategoryService(book_category_repository)