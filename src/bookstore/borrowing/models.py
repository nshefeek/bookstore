import uuid

from enum import Enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import mapped_column, Mapped, relationship

from bookstore.database.models import Base, TimeStampMixin, UUIDMixin

if TYPE_CHECKING:
    from bookstore.auth.models import User
    from bookstore.books.models import Book, BookTitle


class BorrowStatus(str, Enum):
    BORROWED = "borrowed"
    RETURNED = "returned"
    OVERDUE = "overdue"
    LOST = "lost"


class BookRequestStatus(str, Enum):
    PENDING = "pending"
    NOTIFIED = "notified"
    FULFILLED = "fulfilled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class BorrowRecord(Base, TimeStampMixin, UUIDMixin):
    __tablename__ = "borrow_records"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    book_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("books.id"), primary_key=True)
    returned: Mapped[bool] = mapped_column(Boolean, default=False)
    borrowed_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    due_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )
    return_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )
    status: Mapped[BorrowStatus] = mapped_column(default=BorrowStatus.BORROWED, nullable=False)

    book: Mapped["Book"] = relationship(back_populates="borrow_records")
    user: Mapped["User"] = relationship(back_populates="borrow_records")


class BookRequest(Base, TimeStampMixin, UUIDMixin):
    __tablename__ = "book_requests"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    book_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("books.id"), primary_key=True)
    requested_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[BookRequestStatus] = mapped_column(
        default=BookRequestStatus.PENDING, nullable=False
    )
    book: Mapped["Book"] = relationship(back_populates="borrow_requests")
    user: Mapped["User"] = relationship(back_populates="borrow_requests")

