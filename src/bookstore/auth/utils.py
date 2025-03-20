import bcrypt

from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from bookstore.auth.schemas import TokenPayload
from bookstore.config import config

SECRET_KEY = config.auth.JWT_SECRET_KEY.get_secret_value()
ALGORITHM = config.auth.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = config.auth.JWT_ACCESS_TOKEN_EXPIRE_MINUTES


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: TokenPayload, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject.user_id)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    

def generate_api_key() -> str:
    return bcrypt.gensalt(12).hex()


def hash_api_key(api_key: str) -> str:
    return pwd_context.hash(api_key)


def verify_api_key(api_key: str, hashed_api_key: str) -> bool:
    return pwd_context.verify(api_key, hashed_api_key)