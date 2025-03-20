from uuid import UUID
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Depends, HTTPException, status

from bookstore.books.models import BookStatus
from bookstore.books.repositories import BookRepository

from .models import BorrowRecord, BookRequest, BorrowStatus, BookRequestStatus
from .repositories import BorrowRecordRepository, BookRequestRepository
from .schemas import BookRequestCreate, BorrowRecordCreate, BorrowHistoryFilter, BookRequestFilter

class BorrowService:
    def __init__(
        self,
        borrow_record_repository: BorrowRecordRepository = Depends(),
        book_request_repository: BookRequestRepository = Depends(),
        book_repository: BookRepository = Depends(),
    ):
        self.borrow_record_repository = borrow_record_repository
        self.book_request_repository = book_request_repository
        self.book_repository = book_repository

    async def get_all_borrows(self, params: BorrowHistoryFilter) -> List[BorrowRecord]:
        return await self.borrow_record_repository.get_all(params)

    async def borrow_book(self, borrow_data: BorrowRecordCreate) -> BorrowRecord:
        book = self.book_repository.get_by_id(borrow_data.book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found",
            )

        if book.status != BookStatus.AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book is not available",
            )

        active_borrow = self.borrow_record_repository.get_active_borrow_for_book(borrow_data.book_id)
        if active_borrow:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book is already borrowed {active_borrow.status}",
            )

        if borrow_data.due_date is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due date cannot be empty",
            )
        
        if borrow_data.due_date < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due date cannot be in the past",
            )
        borrow = await self.borrow_record_repository.create_borrow_record(borrow_data)
        await self.book_repository.update_book_status(book_id=borrow_data.book_id, status=BookStatus.BORROWED)

        return borrow

    async def return_book(self, borrow_id: UUID) -> BorrowRecord:
        borrow_record = self.borrow_record_repository.get_by_id(borrow_id)
        if not borrow_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Borrow not found",
            )

        if borrow_record.status not in [BorrowStatus.BORROWED, BorrowStatus.OVERDUE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book is not borrowed {borrow_record.status}",
            )
        updated_record = await self.borrow_record_repository.mark_borrow_as_returned(borrow_id, return_date=datetime.now(timezone.utc))
        await self.book_repository.update_book_status(book_id=borrow_record.book_id, status=BookStatus.AVAILABLE)
        return updated_record

    async def mark_borrow_as_lost(self, borrow_id: UUID) -> BorrowRecord:
        borrow_record = self.borrow_record_repository.get_by_id(borrow_id)
        if not borrow_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Borrow not found",
            )

        if borrow_record.status not in [BorrowStatus.BORROWED, BorrowStatus.OVERDUE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book is not borrowed {borrow_record.status}",
            )
        updated_record = await self.borrow_record_repository.mark_borrow_as_lost(borrow_id)
        await self.book_repository.update_book_status(book_id=borrow_record.book_id, status=BookStatus.LOST)
        return updated_record

    async def get_reader_borrow_history(
        self,
        reader_id: UUID,
        status: Optional[List[BorrowStatus]] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[BorrowRecord]:
        return await self.borrow_record_repository.get_reader_borrow_history(reader_id, status, offset, limit)

    async def get_active_borrows_for_reader(self, reader_id: UUID) -> List[BorrowRecord]:
        return await self.borrow_record_repository.get_active_borrows_for_reader(reader_id)

    async def get_overdue_borrows_for_reader(self, reader_id: UUID) -> List[BorrowRecord]:
        return await self.borrow_record_repository.get_overdue_borrows_for_reader(reader_id)

    async def get_borrow_details(self, borrow_id: UUID) -> Tuple[BorrowRecord, Dict[str, Any]]:
        record = await self.borrow_record_repository.get_by_id(borrow_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Borrow not found",
            )
        
        book = await self.book_repository.get_by_id(record.book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found",
            )
        
        book_details = await self.cache.get(f"book:{book.id}")
        if not book_details:
            self.cache.set(
                f"book:{book.id}",
                {
                    "title": book.book_title,
                    "author": book.book_title.author,
                    "genre": book.book_title.category,
                    "description": book.book_title.description,
                    "barcode": book.barcode,
                }
            )
        
        return record, book_details

    async def request_book(self, request_data: BookRequestCreate) -> BookRequest:
        book = await self.book_repository.get_by_id(request_data.book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found",
            )
        
        if book.status == BookStatus.AVAILABLE: 
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book is already available",
            )
        
        pending_requests = await self.book_request_repository.get_pending_requests_for_book(request_data.book_id)
        if any(req.reader_id == request_data.reader_id for req in pending_requests):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already requested to borrow this book",
            )
        
        return await self.book_request_repository.create_book_request(request_data.reader_id, request_data.book_id)

    async def get_pending_requests(self, user_id: UUID) -> List[BookRequest]:
        return await self.book_request_repository.get_pending_requests_for_user(user_id)

    async def accept_request(self, request_id: UUID) -> BookRequest:
        request = await self.book_request_repository.get_by_id(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found",
            )
        
        if request.status != BookRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request is not pending",
            )
        
        await self.book_request_repository.mark_fulfilled(request_id)
        return request

    async def reject_request(self, request_id: UUID) -> BookRequest:
        request = await self.book_request_repository.get_by_id(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found",
            )
        
        if request.status != BookRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request is not pending",
            )
        
        await self.book_request_repository.mark_rejected(request_id)
        return request

    async def mark_expired(self, request_id: UUID) -> BookRequest:
        request = await self.book_request_repository.get_by_id(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found",
            )
        
        if request.status != BookRequestStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request is not pending",
            )
        
        await self.book_request_repository.mark_expired(request_id)
        return request

    async def get_all_requests(self, search_params: BookRequestFilter) -> List[BookRequest]:
        return await self.book_request_repository.get_all_requests(search_params)

    async def get_pending_requests_for_book(self, book_id: UUID) -> List[BookRequest]:
        return await self.book_request_repository.get_pending_requests_for_title(book_id)

    async def get_expired_requests(self) -> List[BookRequest]:
        return await self.book_request_repository.get_expired_requests()

    async def get_request_by_id(self, request_id: UUID) -> Optional[BookRequest]:
        return await self.book_request_repository.get_by_id(request_id)
