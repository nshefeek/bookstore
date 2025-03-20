from uuid import UUID
from typing import List, Optional, Tuple

from fastapi import Depends, HTTPException, status

from .models import BookCategory, BookTitle, Book, BookStatus
from .repositories import BookCategoryRepository, BookTitleRepository, BookRepository
from .schemas import BookCategoryCreate, BookCategoryUpdate, BookTitleCreate, BookTitleUpdate, BookTitleSearchParams, BookCreate, BookUpdate

class BookCategoryService:
    def __init__(self, repository: BookCategoryRepository = Depends()):
        self.repository = repository

    async def get_all_categories(self) -> List[BookCategory]:
        return await self.repository.get_all()
    
    async def get_category_by_id(self, category_id: UUID) -> Optional[BookCategory]:
        return await self.repository.get_by_id(category_id)

    async def create_category(self, category_data: BookCategoryCreate) -> BookCategory:
        existing = await self.repository.get_by_name(category_data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category already exists",
            )
        return await self.repository.create_category(category_data)
    
    async def update_category(self, category_id: UUID, category_data: BookCategoryUpdate) -> BookCategory:
        existing = await self.repository.get_by_id(category_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        return await self.repository.update_category(category_id, category_data)
    
    async def delete_category(self, category_id: UUID) -> bool:
        category = await self.repository.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        
        if category.books:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category has books",
            )
        
        return await self.repository.delete_category(category_id)
    

class BookService:
    def __init__(
            self,
            book_repository: BookRepository = Depends(),
            book_title_repository: BookTitleRepository = Depends(),
            book_category_repository: BookCategoryRepository = Depends(),
    ):
        self.book_repository = book_repository
        self.book_title_repository = book_title_repository
        self.book_category_repository = book_category_repository

    async def get_title_by_id(self, title_id: UUID, include_copies: bool = False) -> Optional[BookTitle]:
        return await self.book_title_repository.get_by_id(title_id, include_copies)
    
    async def get_title_by_isbn(self, isbn: str, include_copies: bool = False) -> Optional[BookTitle]:
        return await self.book_title_repository.get_by_isbn(isbn, include_copies)
    
    async def get_all_titles(self, limit: int = 100, offset: int = 0) -> List[BookTitle]:
        result = await self.book_title_repository.get_all(limit, offset)
        return result
    
    async def create_title(self, title_data: BookTitleCreate) -> BookTitle:
        category = await self.book_category_repository.get_by_id(title_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        existing = await self.book_title_repository.get_by_isbn(title_data.isbn)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title already exists",
            )
        
        book_title = await self.book_title_repository.create_title(title_data)
        return book_title
    
    async def update_title(self, title_id: UUID, title_data: BookTitleUpdate) -> BookTitle:
        if title_data.category_id:
            category = await self.book_category_repository.get_by_id(title_data.category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found",
                )

        return await self.book_title_repository.update_title(title_id, title_data)
    
    async def delete_title(self, title_id: UUID) -> bool:
        copies = await self.book_repository.get_all_for_title(title_id)
        if copies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title has copies",
            )
        return await self.book_title_repository.delete_title(title_id)
    
    async def search_titles(self, search_params: BookTitleSearchParams) -> Tuple[List[BookTitle], int]:
        books, total = await self.book_title_repository.search(search_params)
        return books, total
    
    async def get_book_by_id(self, book_id: UUID) -> Optional[Book]:
        return await self.book_repository.get_by_id(book_id)
    
    async def get_book_by_barcode(self, barcode: str) -> Optional[Book]:
        return await self.book_repository.get_by_barcode(barcode)
    
    async def get_all_books(self, limit: int = 100, offset: int = 0) -> List[Book]:
        return await self.book_repository.get_all(limit, offset)
    
    async def get_all_books_for_title(self, title_id: UUID) -> List[Book]:
        return await self.book_repository.get_all_for_title(title_id)
    
    async def get_all_available_books_for_title(self, title_id: UUID) -> List[Book]:
        return await self.book_repository.get_all_available_for_title(title_id)
    
    async def create_book(self, book_data: BookCreate) -> Book:
        title = await self.book_title_repository.get_by_id(book_data.book_title_id)
        if not title:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Title not found",
            )
        return await self.book_repository.create_book(book_data)
    
    async def update_book(self, book_id: UUID, book_data: BookUpdate) -> Book:
        if book_data.title_id:
            title = await self.book_title_repository.get_by_id(book_data.title_id)
            if not title:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Title not found",
                )
        return await self.book_repository.update_book(book_id, book_data)
    
    async def update_book_status(self, book_id: UUID, book_status: BookStatus) -> Book:
        return await self.book_repository.update_status(book_id, book_status)
    
    async def delete_book(self, book_id: UUID) -> bool:
        return await self.book_repository.delete_book(book_id)
