from enum import Enum
from uuid import UUID
from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Integer

from bookstore.database.models import Base, TimeStampMixin, UUIDMixin

if TYPE_CHECKING:
    from bookstore.borrowing.models import BookRequest, BorrowRecord


class BookStatus(str, Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    LOST = "lost"


class BookCategory(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "book_categories"

    name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(String, nullable=True)

    books: Mapped["BookTitle"] = relationship(back_populates="category")


class BookTitle(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "book_titles"

    title: Mapped[str] = mapped_column(String, nullable=False, index=True)
    author: Mapped[str] = mapped_column(String, nullable=False, index=True)
    isbn: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    publisher: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[UUID] = mapped_column(ForeignKey("book_categories.id"), nullable=False)

    category: Mapped[BookCategory] = relationship(
        back_populates="books",
        lazy="selectin"
    )
    copies: Mapped[List["Book"]] = relationship(
        back_populates="book_title",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class Book(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "books"

    book_title_id: Mapped[UUID] = mapped_column(ForeignKey("book_titles.id"), nullable=False)
    edition: Mapped[str] = mapped_column(String, nullable=False)
    published_year: Mapped[int] = mapped_column(Integer, nullable=False)
    barcode: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    status: Mapped[BookStatus] = mapped_column(default=BookStatus.AVAILABLE, nullable=False)

    book_title: Mapped[BookTitle] = relationship(back_populates="copies", lazy="selectin")
    borrow_records: Mapped[List["BorrowRecord"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    book_requests: Mapped[List["BookRequest"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
        lazy="selectin"
    )