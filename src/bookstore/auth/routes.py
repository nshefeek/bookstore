from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from .models import User, UserRole
from .schemas import UserCreate, UserUpdate, UserResponse, LoginResponse, APIKeyCreate, APIKeyFullResponse
from .services import AuthService
from .dependencies import (
    get_auth_service,
    get_current_active_user,
    user_is_librarian_or_admin,
)


router = APIRouter()


@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(
    user: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(user_is_librarian_or_admin),
):
    if not current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.LIBRARIAN and user.role != UserRole.READER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
    response = await auth_service.create_user(user)
    return response


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), auth_service: AuthService = Depends(get_auth_service)):
    response = await auth_service.authenticate_user(form_data.username, form_data.password)
    return response


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user(current_user: User = Depends(get_current_active_user)):
    return UserResponse.model_validate(current_user)


@router.get("/users", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(user_is_librarian_or_admin),
):
    response = await auth_service.get_all_users(skip, limit)
    return response


@router.get("/users/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_by_id(
    user_id: UUID,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(user_is_librarian_or_admin),
):
    response = await auth_service.get_user_by_id(user_id)
    return response


@router.put("/users/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: UUID,
    target_user: UserUpdate,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.LIBRARIAN and target_user.role != UserRole.READER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    elif current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    if target_user.role and current_user.role != UserRole.ADMIN:
        if target_user.role.value > current_user.role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

    response = await auth_service.update_user(user_id, target_user)
    return response


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(user_is_librarian_or_admin),
):
    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.LIBRARIAN:
        target_user = await auth_service.get_user_by_id(user_id)
        if target_user.role != UserRole.READER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        
    await auth_service.delete_user(user_id)


@router.post("/users/{user-id}/api-keys", response_model=APIKeyFullResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    user_id: UUID,
    api_key_data: APIKeyCreate,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.id != user_id or current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    response = await auth_service.create_api_key(user_id, api_key_data)
    return response


@router.get("/users/{user-id}/api-keys", response_model=list[APIKeyFullResponse], status_code=status.HTTP_200_OK)
async def get_api_keys(
    user_id: UUID,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.id != user_id or current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    response = await auth_service.get_api_keys(user_id)
    return response


@router.delete("/users/{user-id}/api-keys/{api-key-id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    user_id: UUID,
    api_key_id: UUID,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.id != user_id or current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    await auth_service.delete_api_key(api_key_id)