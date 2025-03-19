from uuid import UUID
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select, func, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import BookCategory, BookTitle, Book, BookStatus
from .schemas import (
    BookCategoryCreate,
    BookCategoryUpdate,
    BookTitleCreate,
    BookTitleUpdate,
    BookCreate,
    BookUpdate,
    BookTitleSearchParams,
)


class BookCategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_name(self, name: str) -> Optional[BookCategory]:
        result = await self.session.execute(select(BookCategory).where(BookCategory.name == name))
        return result.scalars().first()
    
    async def get_by_id(self, category_id: UUID) -> Optional[BookCategory]:
        result = await self.session.execute(select(BookCategory).where(BookCategory.id == category_id))
        return result.scalars().first()
    
    async def get_all(self) -> List[BookCategory]:
        result = await self.session.execute(select(BookCategory))
        return result.scalars()._allrows()

    async def create_category(self, category_data: BookCategoryCreate) -> BookCategory:
        category = await self.get_by_name(category_data.name)
        if category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category already exists",
            )
        category = BookCategory(**category_data.model_dump())
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def update_category(self, category_id: UUID, category_data: BookCategoryUpdate) -> BookCategory:
        category = await self.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        await self.session.execute(
            update(BookCategory).where(BookCategory.id == category_id).values(**category_data.model_dump())
        )
        
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def delete_category(self, category_id: UUID) -> bool:
        category = await self.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        await self.session.execute(delete(BookCategory).where(BookCategory.id == category_id))
        await self.session.commit()
        return True
    

class BookTitleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[BookTitle]:
        result = await self.session.execute(
            select(BookTitle)
            .options(selectinload(BookTitle.category))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars()._allrows()

    async def get_by_isbn(self, isbn: str, include_copies: bool = False) -> Optional[BookTitle]:
        query = select(BookTitle).where(BookTitle.isbn == isbn)

        if include_copies:
            query = query.options(
                selectinload(BookTitle.category),
                selectinload(BookTitle.copies),
            )

        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_id(self, title_id: UUID, include_copies: bool = False) -> Optional[BookTitle]:
        query = select(BookTitle).where(BookTitle.id == title_id)

        if include_copies:
            query = query.options(
                selectinload(BookTitle.category),
                selectinload(BookTitle.copies),
            )

        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def create_title(self, title_data: BookTitleCreate) -> BookTitle:
        title = await self.get_by_isbn(title_data.isbn)
        if title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title already exists",
            )
        title = BookTitle(**title_data.model_dump())
        self.session.add(title)
        await self.session.commit()
        await self.session.refresh(title)
        return title
    
    async def update_title(self, title_id: UUID, title_data: BookTitleUpdate) -> BookTitle:
        title = await self.get_by_id(title_id)
        if not title:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Title not found",
            )
        
        if title_data.isbn and title_data.isbn != title.isbn:
            existing = await self.get_by_isbn(title_data.isbn)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Title already exists",
                )

        await self.session.execute(
            update(BookTitle).where(BookTitle.id == title_id).values(**title_data.model_dump(exclude_unset=True))
        )
        
        await self.session.commit()
        await self.session.refresh(title)
        return title
    
    async def delete_title(self, title_id: UUID) -> bool:
        title = await self.get_by_id(title_id)
        if not title:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Title not found",
            )
        await self.session.execute(delete(BookTitle).where(BookTitle.id == title_id))
        await self.session.commit()
        return True
    
    async def search(self, search_params: BookTitleSearchParams) -> Tuple[List[BookTitle], int]:
        query = select(BookTitle).options(selectinload(BookTitle.category))

        if search_params.title:
            query = query.where(BookTitle.title.ilike(f"%{search_params.title}%"))

        if search_params.author:
            query = query.where(BookTitle.author.ilike(f"%{search_params.author}%"))

        if search_params.isbn:
            query = query.where(BookTitle.isbn == search_params.isbn)

        if search_params.category_name:
            query = query.where(BookTitle.category.ilike(f"%{search_params.category_name}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total_count = await self.session.execute(count_query)
        total = total_count.scalar_one()

        query = query.limit(search_params.limit).offset((search_params.page - 1) * search_params.limit)

        result = await self.session.execute(query)
        return result.scalars()._allrows(), total
    
    async def get_copy_counts(self, title_id: UUID) -> Dict[str, int]:
        total_query = select(func.count(Book.id)).where(Book.title_id == title_id)
        total_result = await self.session.execute(total_query)
        total_copies = total_result.scalar_one()

        available_query = select(func.count(Book.id)).where(
            and_(Book.title_id == title_id, Book.status == BookStatus.AVAILABLE)
        )
        available_result = await self.session.execute(available_query)
        available_copies = available_result.scalar_one()

        return {"total": total_copies, "available": available_copies}

        result = await self.session.execute(
            select(Book.status, func.count(Book.id))
            .where(Book.title_id == title_id)
            .group_by(Book.status)
        )
        return {row[0]: row[1] for row in result.all()}
    

class BookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Book]:
        result = await self.session.execute(
            select(Book)
            .options(selectinload(Book.book_title))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars()._allrows()
    
    async def get_all_for_title(self, title_id: UUID) -> List[Book]:
        result = await self.session.execute(
            select(Book)
            .where(Book.title_id == title_id)
            .options(selectinload(Book.book_title))
        )
        return result.scalars()._allrows()
    
    async def get_all_available_for_title(self, title_id: UUID) -> List[Book]:
        result = await self.session.execute(
            select(Book)
            .where(Book.title_id == title_id, Book.status == BookStatus.AVAILABLE)
            .options(selectinload(Book.book_title))
        )
        return result.scalars()._allrows()
    
    async def get_by_id(self, book_id: UUID) -> Optional[Book]:
        result = await self.session.execute(
            select(Book)
            .where(Book.id == book_id)
            .options(selectinload(Book.book_title))
        )
        return result.scalars().first()
    
    async def get_by_barcode(self, barcode: str) -> Optional[Book]:
        result = await self.session.execute(
            select(Book)
            .where(Book.barcode == barcode)
            .options(selectinload(Book.book_title))
        )
        return result.scalars().first()
    
    async def create_book(self, book_data: BookCreate) -> Book:
        book = await self.get_by_barcode(book_data.barcode)
        if book:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book already exists",
            )
        book = Book(**book_data.model_dump())
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book
    
    async def update_book(self, book_id: UUID, book_data: BookUpdate) -> Book:
        book = await self.get_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found",
            )
        await self.session.execute(
            update(Book).where(Book.id == book_id).values(**book_data.model_dump(exclude_unset=True))
        )
        
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def delete_book(self, book_id: UUID) -> bool:
        book = await self.get_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found",
            )
        await self.session.execute(delete(Book).where(Book.id == book_id))
        await self.session.commit()
        return True
    
    async def update_status(self, book_id: UUID, book_status: BookStatus) -> Book:
        book = await self.get_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found",
            )
        await self.session.execute(update(Book).where(Book.id == book_id).values(status=book_status))
        return book