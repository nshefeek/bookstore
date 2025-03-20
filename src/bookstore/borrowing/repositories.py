from uuid import UUID
from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, desc

from .models import BorrowRecord, BorrowStatus, BookRequest, BookRequestStatus
from .schemas import BorrowRecordCreate, BorrowHistoryFilter, BookRequestFilter


class BorrowRecordRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_borrow_for_book(self, book_id: UUID) -> Optional[BorrowRecord]:
        active_statuses = (BorrowStatus.ACCEPTED, BorrowStatus.OVERDUE)
        query = select(BorrowRecord).filter(
            BorrowRecord.book_id == book_id,
            BorrowRecord.status.in_(active_statuses),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_reader_borrow_history(
        self,
        user_id: UUID,
        status: Optional[List[BorrowStatus]] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[BorrowRecord]:
        query = select(BorrowRecord).where(BorrowRecord.user_id == user_id)

        if status:
            query = query.filter(BorrowRecord.status.in_(status))

        query = query.order_by(desc(BorrowRecord.borrowed_date)).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars()._allrows()

    async def get_active_borrows_for_reader(self, user_id: UUID) -> Optional[BorrowRecord]:
        active_statuses = (BorrowStatus.ACCEPTED, BorrowStatus.OVERDUE)
        query = select(BorrowRecord).where(
            and_(
                BorrowRecord.user_id == user_id,
                BorrowRecord.status.in_(active_statuses),
            )
        ).order_by(BorrowRecord.due_date)

        result = await self.session.execute(query)
        return result.scalars()._allrows()

    async def get_overdue_borrows_for_reader(self, user_id: UUID) -> List[BorrowRecord]:
        query = select(BorrowRecord).where(
            and_(
                BorrowRecord.user_id == user_id,
                BorrowRecord.status == BorrowStatus.OVERDUE,
            )
        )._order_by(desc(BorrowRecord.due_date))

        result = await self.session.execute(query)
        return result.scalars()._allrows()

    async def mark_borrow_as_returned(
        self,
        borrow_id: UUID,
        returned_date: Optional[datetime] = None,
    ) -> Optional[BorrowRecord]:
        return_date = returned_date or datetime.now(timezone.utc)

        query = update(BorrowRecord).where(
            and_(
                BorrowRecord.id == borrow_id,
                or_(
                    BorrowRecord.status == BorrowStatus.BORROWED,
                    BorrowRecord.status == BorrowStatus.OVERDUE,
                )
            )
        ).values(
            return_date=return_date,
            status=BorrowStatus.RETURNED,
        ).returning(BorrowRecord)

        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def mark_borrow_as_lost(self, borrow_id: UUID) -> Optional[BorrowRecord]:
        query = update(BorrowRecord).where(
            and_(
                BorrowRecord.id == borrow_id,
                or_(
                    BorrowRecord.status == BorrowStatus.BORROWED,
                    BorrowRecord.status == BorrowStatus.OVERDUE,
                )
            )
        ).values(
            status=BorrowStatus.LOST,
        ).returning(BorrowRecord)

        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def mark_borrow_as_overdue(self, borrow_id: UUID) -> Optional[BorrowRecord]:
        query = update(BorrowRecord).where(
            and_(
                BorrowRecord.id == borrow_id,
                or_(
                    BorrowRecord.status == BorrowStatus.BORROWED,
                    BorrowRecord.due_date < datetime.now(timezone.utc),
                )
            )
        ).values(
            status=BorrowStatus.OVERDUE,
        ).returning(BorrowRecord)

        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def create_borrow_record(self, data: BorrowRecordCreate) -> BorrowRecord:
        new_record = BorrowRecord(**data)
        self.session.add(new_record)
        await self.session.commit()
        await self.session.refresh(new_record)
        return new_record

    async def get_by_id(self, record_id: UUID) -> Optional[BorrowRecord]:
        query = select(BorrowRecord).filter(BorrowRecord.id == record_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, params: BorrowHistoryFilter) -> List[BorrowRecord]:
        query = select(BorrowRecord)
        result = await self.session.execute(query)
        return result.scalars().all()


class BookRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_book_request(self, user_id: UUID, data: Any) -> BookRequest:
        new_request = BookRequest(user_id=user_id, **data)
        self.session.add(new_request)
        await self.session.commit()
        await self.session.refresh(new_request)
        return new_request

    async def get_all_requests(self, params: BookRequestFilter) -> List[BookRequest]:
        query = select(BookRequest)
        if params.user_id:
            query = query.filter(BookRequest.user_id == params.user_id)
        if params.title_id:
            query = query.filter(BookRequest.title_id == params.title_id)
        if params.status:
            query = query.filter(BookRequest.status == BookRequestStatus(params.status))
        result = await self.session.execute(query).limit(params.limit).offset(params.offset)
        return result.scalars().all()

    async def get_by_id(self, request_id: UUID) -> Optional[BookRequest]:
        query = select(BookRequest).filter(BookRequest.id == request_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_for_user(self, user_id: UUID) -> List[BookRequest]:
        query = select(BookRequest).filter(BookRequest.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_pending_requests_for_user(self, user_id: UUID) -> List[BookRequest]:
        query = select(BookRequest).filter(
            BookRequest.user_id == user_id,
            BookRequest.status == BookRequestStatus.PENDING,
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_pending_request_for_title(self, title_id: UUID) -> Optional[BookRequest]:
        query = select(BookRequest).filter(
            BookRequest.title_id == title_id,
            BookRequest.status == BookRequestStatus.PENDING,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def mark_fulfilled(self, request_id: UUID) -> Optional[BookRequest]:
        query = update(BookRequest).filter(
            BookRequest.id == request_id,
            BookRequest.status == BookRequestStatus.PENDING,
        ).values(status=BookRequestStatus.FULFILLED)

        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def mark_rejected(self, request_id: UUID) -> Optional[BookRequest]:
        query = update(BookRequest).filter(
            BookRequest.id == request_id,
            BookRequest.status == BookRequestStatus.PENDING,
        ).values(status=BookRequestStatus.REJECTED)

        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def mark_expired(self, request_id: UUID) -> Optional[BookRequest]:
        query = update(BookRequest).filter(
            BookRequest.id == request_id,
            BookRequest.status == BookRequestStatus.PENDING,
        ).values(status=BookRequestStatus.EXPIRED)

        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()