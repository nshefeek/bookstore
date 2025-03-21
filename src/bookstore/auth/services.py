from uuid import UUID
from typing import List

from jose import JWTError
from fastapi import Depends, HTTPException, status

from .utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
)

from bookstore.logger import get_logger

from .models import User, UserRole
from .repositories import UserRepository, APIKeyRepository
from .schemas import UserCreate, UserUpdate, UserResponse,TokenPayload, Token, APIKeyCreate, APIKeyFullResponse, LoginResponse


logger = get_logger("auth.services")

class AuthService:
    def __init__(
            self,
            user_repository: UserRepository = Depends(),
            api_key_repository: APIKeyRepository = Depends(),
    ):
        self.user_repository = user_repository
        self.api_key_repository = api_key_repository

    async def create_user(self, user: UserCreate) -> UserResponse:
        db_user = await self.user_repository.create_user(user)
        return UserResponse.model_validate(db_user)
    
    async def update_user(self, user_id: UUID, user: UserUpdate) -> UserResponse:
        db_user = await self.user_repository.update_user(user_id, user)
        return UserResponse.model_validate(db_user)
    
    async def delete_user(self, user_id: UUID) -> bool:
        result = await self.user_repository.delete_user(user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return True

    async def get_user_by_email(self, email: str) -> User:
        db_user = await self.user_repository.get_user_by_email(email)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return db_user
    
    async def get_user_by_id(self, user_id: UUID) -> User:
        db_user = await self.user_repository.get_user_by_id(user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return db_user
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        users = await self.user_repository.get_all_users(skip, limit)
        return [UserResponse.model_validate(user) for user in users]

    async def authenticate_user(self, email: str, password: str) -> LoginResponse:
        user = await self.get_user_by_email(email)
        if not user or verify_password(password, user.hashed_password) is False:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not active",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = await self.create_access_token(user.id)
        return LoginResponse(
            user=UserResponse.model_validate(user),
            token=Token(access_token=access_token, token_type="bearer")
        )

    async def change_password(self, user_id: UUID, old_password: str, new_password: str) -> UserResponse:
        user = await self.get_user_by_id(user_id)
        if not user or verify_password(old_password, user.hashed_password) is False:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        hashed_password = get_password_hash(new_password)
        user_update = UserUpdate(password=hashed_password)
        await self.user_repository.update_user(user_id, user_update)
        return UserResponse.model_validate(user)
    
    async def create_access_token(self, user_id: UUID) -> str:
        payload = TokenPayload(user_id=user_id)
        return create_access_token(payload)
    
    async def validate_token(self, token: str) -> User:
        try:
            logger.info("Validating token")
            payload = decode_token(token)
            user_id = payload.get("sub")

            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )

        user = await self.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not active",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user
        

    async def create_api_key(self, user_id: UUID, api_key_data: APIKeyCreate) -> APIKeyFullResponse:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        api_key, raw_key = await self.api_key_repository.create_api_key(user_id, api_key_data)
        
        api_key_response = APIKeyFullResponse(
            id=api_key.id,
            user_id=api_key.user_id,
            name=api_key.name,
            api_key_hash=api_key.api_key_hash,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at,
            last_used_at=api_key.last_used_at,
            key=raw_key,
        )

        return api_key_response
    
    async def get_api_keys(self, user_id: UUID) -> List[APIKeyFullResponse]:
        api_keys = await self.api_key_repository.get_for_user(user_id)
        return api_keys
    
    async def validate_api_key(self, raw_key: str) -> User:
        if not raw_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        api_key = await self.api_key_repository.verify_api_key(raw_key)

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await self.get_user_by_id(api_key.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not active or not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    async def delete_api_key(self, api_key_id: UUID) -> bool:
        result = await self.api_key_repository.delete(api_key_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )
        return True