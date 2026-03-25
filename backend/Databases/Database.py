from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)

from Databases.Schema import ImagesTable


SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:2716@127.0.0.1:1488/optg_database"

# Create a postgresql engine instance
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,
    pool_pre_ping=True, # Проверка соединений
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    connect_args={
        "command_timeout": 60,
        "server_settings": {
            "application_name": "optg_app"
        }
    }
)
async_session_local = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_local() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_all_image_records(db_session: AsyncSession):
    """Возвращает список кортежей (id, storage_path, filename) из таблицы images."""
    query = select(
        ImagesTable.id,        
        ImagesTable.filename,          
        ImagesTable.storage_path       
    )                                 
    result = await db_session.execute(query)
    return result.fetchall()

