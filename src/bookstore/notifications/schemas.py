from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class NotificationCreate(BaseModel):
    message: str


class NotificationUpdate(BaseModel):
    read_at: Optional[datetime]


class NotificationSchema(BaseModel):
    id: UUID
    message: str
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationFilterSchema(BaseModel):
    unread_only: Optional[bool] = False
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=100)