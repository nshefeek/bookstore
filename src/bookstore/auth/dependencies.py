from typing import Annotated, Optional

from click import Option
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from bookstore.config import config
from bookstore.logger import get_logger
from bookstore.database.session import get_session

from .models import User, UserRole
from .repositories import UserRepository,APIKeyRepository
from .services import AuthService


logger = get_logger("auth.dependencies")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{config.API_V1_STR}/auth/token")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    user_repository = UserRepository(session)
    api_key_repository = APIKeyRepository(session)
    return AuthService(user_repository, api_key_repository)


async def get_current_user(
    token: Annotated[Optional[str], Security(oauth2_scheme)],
    api_key: Annotated[Optional[str], Security(api_key_header)],
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    logger.debug("Getting current user")
    logger.debug(f"API key: {api_key}")
    logger.debug(f"Token: {token}")
    if api_key:
        return await auth_service.validate_api_key(api_key)
    elif token:
        return await auth_service.validate_token(token)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer or API Key"},
        )
    

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    logger.info(current_user)
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def user_is_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


def user_is_librarian(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != UserRole.LIBRARIAN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


def user_is_librarian_or_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role not in [UserRole.LIBRARIAN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


def user_is_reader(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != UserRole.READER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
