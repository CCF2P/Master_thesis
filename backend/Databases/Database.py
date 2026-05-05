from typing import Any, AsyncGenerator, Sequence, Tuple

import os
from dotenv import load_dotenv

from sqlalchemy import select, Row, Select, Result
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker
)

from Databases.Schema import ImagesTable


dotenv_path: str = os.path.join(os.path.dirname(__file__), 'db_config.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

SQLALCHEMY_DATABASE_URL: str | None = os.getenv("SQLALCHEMY_DATABASE_URL")
if SQLALCHEMY_DATABASE_URL is None:
    print("[ERROR] Cannot load config for database")

# Create a postgresql engine instance
engine: AsyncEngine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, # type: ignore
    echo=True,
    pool_pre_ping=True, # Check for successfull connection
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


async def get_all_image_records(db_session: AsyncSession) -> Sequence[Row[Tuple[int, str, str]]]:
    """Возвращает список кортежей (id, storage_path, filename) из таблицы images."""
    query: Select[Tuple[int, str, str]] = select(
        ImagesTable.id,
        ImagesTable.filename,
        ImagesTable.storage_path
    )
    result: Result[Tuple[int, str, str]] = await db_session.execute(query)
    return result.fetchall()
