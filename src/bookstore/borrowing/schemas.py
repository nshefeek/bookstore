from uuid import UUID
from datetime import datetime, timezone
from typing import List, Optional


from pydantic import BaseModel, Field

from .models import BorrowStatus, BookRequestStatus


class BorrowRecord(BaseModel):
    book_id: UUID
    user_id: Optional[UUID] = None
    borrowed_date: Optional[datetime] = datetime.now(timezone.utc)
    due_date: Optional[datetime] = None


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


class ReturnRequest(BaseModel):
    borrow_id: UUID


class BorrowHistoryFilter(BaseModel):
    status: Optional[List[BorrowStatus]] = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=100)


class BookRequest(BaseModel):
    book_id: UUID
    reader_id: UUID


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


class BookRequestUpdate(BookRequest):
    status: Optional[BookRequestStatus] = None


class BookRequestFilter(BaseModel):
    book_id: Optional[UUID] = None
    reader_id: Optional[UUID] = None
    status: Optional[List[BookRequestStatus]] = None