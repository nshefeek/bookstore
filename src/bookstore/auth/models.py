import uuid
from enum import Enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Boolean, ForeignKey, TIMESTAMP, UniqueConstraint
from bookstore.database.models import Base, TimeStampMixin, UUIDMixin


class UserRole(Enum):
    ADMIN = "admin"
    LIBRARIAN = "librarian"
    READER = "reader"


class User(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(default=UserRole.READER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class APIKey(Base, UUIDMixin, TimeStampMixin):
    __tablename__ = "api_keys"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    api_key_hash: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_used_ip: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="api_keys")

    __table_args__ = (UniqueConstraint("user_id", "name"),)