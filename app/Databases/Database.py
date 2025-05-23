from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)

SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:305308@127.0.0.1:1488/db_xray_image_features"

# Create a postgresql engine instance
engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
async_session_local = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_local() as session:
        yield session
