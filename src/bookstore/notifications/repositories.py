from uuid import UUID
from typing import List
from datetime import datetime, timezone

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_notification(self, reader_id: UUID, message: str) -> Notification:
        notification = Notification(
            user_id=reader_id,
            message=message,
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.read_at.is_(None))

        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars()._allrows()

    async def mark_as_read(self, notification_id: UUID) -> Notification:
        query = update(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.read_at.is_(None),
            )
        ).values(
            read_at=datetime.now(timezone.utc),
        ).returning(Notification)

        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def mark_all_as_read(self, user_id: UUID) -> int:
        query = update(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
        ).values(read_at=datetime.now(timezone.utc))

        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount