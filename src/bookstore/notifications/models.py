import uuid

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import String, TIMESTAMP

from bookstore.database.models import Base, TimeStampMixin, UUIDMixin

if TYPE_CHECKING:
    from bookstore.auth.models import User


class Notification(Base, TimeStampMixin, UUIDMixin):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    message: Mapped[str] = mapped_column(String, nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        onupdate=func.now(),
        nullable=False,
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )

    user: Mapped["User"] = relationship(back_populates="notifications")