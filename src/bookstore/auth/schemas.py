from uuid import UUID
from typing import Optional, Annotated
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, SecretStr

from .models import UserRole


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole
    is_active: bool


class UserCreate(UserBase):
    password: Annotated[SecretStr, Field(min_length=8)]

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "role": "reader",
                "is_active": True,
                "password": "password123",
            }
        }


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserinDB(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}


class UserResponse(UserinDB):
    pass

class UserDetails(UserResponse):
    api_keys: list["APIKeyResponse"] = []


class APIKeyBase(BaseModel):
    name: str


class APIKeyCreate(APIKeyBase):
    pass

class APIKeyResponse(APIKeyBase):
    id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}

class APIKeyFullResponse(APIKeyResponse):
    key: str

class APIKeyinDB(APIKeyBase):
    id: UUID    
    user_id: UUID
    api_key_hash: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    user_id: UUID


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user: UserResponse
    token: Token


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)