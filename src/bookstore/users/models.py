import uuid

from typing import List, TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bookstore.database.models import Base, UUIDMixin, TimeStampMixin

if TYPE_CHECKING:
    from bookstore.auth.models import User
    from bookstore.borrowing.models import BorrowRecord, BookRequest


class Librarian(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "librarians"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    division: Mapped[str] = mapped_column(String, nullable=False)
    
    user: Mapped["User"] = relationship(back_populates="librarians")


class Reader(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "readers"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    reader_badge: Mapped[str] = mapped_column(String, nullable=False)

    user: Mapped["User"] = relationship(back_populates="readers")
    borrow_records: Mapped[List["BorrowRecord"]] = relationship(back_populates="reader")
    book_requests: Mapped[List["BookRequest"]] = relationship(back_populates="reader")

