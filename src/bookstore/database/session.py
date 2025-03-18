from typing import Final, Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy import create_engine, NullPool
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker

from bookstore.config import config


SQLALCHEMY_DATABASE_URL = str(config.database.DATABASE_URI)

engine: Final[AsyncEngine] = AsyncEngine(create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,
    poolclass=NullPool,
    future=True,
))

async_session_maker: Final[async_sessionmaker[AsyncSession]] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


session = Annotated[AsyncSession, Depends(get_session)]