from uuid import UUID
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .models import BookStatus


class BookCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class BookCategoryCreate(BookCategoryBase):
    pass


class BookCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class BookCategoryResponse(BookCategoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}


class BookTitleBase(BaseModel):
    title: str
    author: str
    isbn: str
    description: Optional[str] = None
    publisher: str
    category_id: UUID

    class Config:
        json_encoders = {UUID: str}


class BookTitleCreate(BookTitleBase):
    pass


class BookTitleUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    description: Optional[str] = None
    publisher: Optional[str] = None
    category_id: Optional[UUID] = None


class BookBase(BaseModel):
    book_title_id: UUID
    edition: str
    published_year: int
    barcode: str
    status: BookStatus = Field(default=BookStatus.AVAILABLE)

    class Config:
        json_encoders = {UUID: str}


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title_id: Optional[UUID] = None
    edition: Optional[str] = None
    published_year: Optional[int] = None
    barcode: Optional[str] = None
    status: Optional[BookStatus] = None

    class Config:
        json_encoders = {UUID: str}


class BookResponse(BookBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}


class BookTitleResponse(BookTitleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    category: BookCategoryResponse
    available_copies: int = 0
    total_copies: int = 0

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}


class BookTitleDetailResponse(BookTitleResponse):
    copies: List[BookResponse] = []


class BookTitleSearchParams(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    category_name: Optional[str] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)


class BookTitleSearchResponse(BaseModel):
    items: List[BookTitleResponse]
    total: int = Field(default=0)
    page: int = Field(default=1)
    limit: int = Field(default=10)
    pages: int = Field(default=1)

    @property
    def previous_page(self) -> Optional[int]:
        return self.page - 1 if self.page > 1 else None

    @property
    def next_page(self) -> Optional[int]:
        return self.page + 1 if self.page < self.pages else None
