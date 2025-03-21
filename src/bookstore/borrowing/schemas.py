from uuid import UUID
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field

from bookstore.books.schemas import BookDetailResponse

from .models import BorrowStatus, BookRequestStatus


class BorrowRecord(BaseModel):
    book_id: UUID
    user_id: Optional[UUID] = None
    borrowed_date: Optional[datetime] = datetime.now(timezone.utc)
    due_date: Optional[datetime] = None

    class Config:
        json_encoders = {UUID: str}


class BorrowRecordCreate(BorrowRecord):
    pass


class BorrowRecordResponse(BorrowRecord):
    id: UUID
    book_id: UUID
    user_id: UUID
    borrowed_date: datetime
    due_date: datetime
    return_date: Optional[datetime]
    status: BorrowStatus
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}


class ReturnRequest(BaseModel):
    borrow_id: UUID
    returned_date: datetime = datetime.now(timezone.utc)

    class Config:
        json_encoders = {UUID: str}


class BorrowHistoryFilter(BaseModel):
    borrow_status: Optional[List[BorrowStatus]] = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=100)


class BorrowRecordDetail(BaseModel):
    borrow_record: BorrowRecordResponse
    book_details: BookDetailResponse

class BookRequest(BaseModel):
    book_id: UUID
    reader_id: UUID

    class Config:
        json_encoders = {UUID: str}


class BookRequestCreate(BookRequest):
    pass


class BookRequestResponse(BookRequest):
    id: UUID
    user_id: UUID
    book_id: UUID
    status: BookRequestStatus
    requested_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}


class BookRequestUpdate(BookRequest):
    status: Optional[BookRequestStatus] = None


class BookRequestFilter(BaseModel):
    book_id: Optional[UUID] = None
    reader_id: Optional[UUID] = None
    status: Optional[List[BookRequestStatus]] = None

    class Config:
        json_encoders = {UUID: str}