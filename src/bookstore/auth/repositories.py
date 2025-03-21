from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, APIKey
from .utils import get_password_hash, generate_api_key, hash_api_key
from .schemas import UserCreate, UserUpdate, APIKeyCreate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.session.execute(select(User).offset(skip).limit(limit))
        return result.scalars()._allrows()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalars().first()
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def user_exists(self, email: str) -> bool:
        user = await self.get_user_by_email(email)
        return user is not None

    async def create_user(self, user: UserCreate) -> User:
        if not self.user_exists(user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        hashed_password = get_password_hash(user.password.get_secret_value())
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            role=user.role,
            is_active=user.is_active,
        )
        
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user
    
    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> User:
        update_data = user_update.model_dump(exclude_unset=True)

        if update_data.get("email"):
            if self.user_exists(update_data["email"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )
            
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        if "password" in update_data:
            password = update_data.pop("password")
            update_data["hashed_password"] = get_password_hash(password)

        await self.session.execute(
            update(User).where(User.id == user_id).values(**update_data)
        )

        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user
    
    async def delete_user(self, user_id: UUID) -> bool:
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        await self.session.execute(delete(User).where(User.id == user_id))
        await self.session.commit()
        return True


class APIKeyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_api_key(self, user_id: UUID, api_key_create: APIKeyCreate) -> tuple[APIKey, str]:
        api_key_name = api_key_create.name
        existing = await self.get_by_name(api_key_name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key already exists",
            )
        raw_key = generate_api_key()
        hashed_key = hash_api_key(raw_key)
        api_key = APIKey(user_id=user_id, api_key_hash=hashed_key, **api_key_create.model_dump())
        self.session.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)
        return api_key, raw_key

    async def get_by_name(self, api_key_name: str) -> Optional[APIKey]:
        result = await self.session.execute(select(APIKey).where(APIKey.name == api_key_name))
        return result.scalars().first()
    
    async def get_by_id(self, api_key_id: UUID) -> Optional[APIKey]:
        result = await self.session.execute(select(APIKey).where(APIKey.id == api_key_id))
        return result.scalars().first()
    
    async def get_by_hash(self, api_key_hash: str) -> Optional[APIKey]:
        result = await self.session.execute(select(APIKey).where(APIKey.api_key_hash == api_key_hash))
        return result.scalars().first()
    
    async def get_for_user(self, user_id: UUID) -> List[APIKey]:
        result = await self.session.execute(select(APIKey).where(APIKey.user_id == user_id))
        return result.scalars()._allrows()
    
    async def delete(self, api_key_id: UUID) -> bool:
        api_key = await self.get_by_id(api_key_id)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )
        await self.session.execute(delete(APIKey).where(APIKey.id == api_key_id))
        await self.session.commit()
        return True
    
    async def update_last_used(self, api_key_id: UUID) -> bool:
        api_key = await self.get_by_id(api_key_id)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )
        api_key.last_used_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True

    async def verify_api_key(self, raw_key: str) -> Optional[APIKey]:
        if not raw_key:
            return None
        
        hashed_key = hash_api_key(raw_key)
        result = await self.session.execute(select(APIKey).where(
                APIKey.api_key_hash == hashed_key,
                APIKey.is_active
            )
        )
        api_key = result.scalars().first()

        if not api_key:
            return None
        
        return api_key