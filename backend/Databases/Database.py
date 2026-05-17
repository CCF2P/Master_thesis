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
    pool_pre_ping=True,
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
    """Возвращает список кортежей (id, filename, storage_path) из таблицы images."""
    query: Select[Tuple[int, str, str]] = select(
        ImagesTable.id,
        ImagesTable.filename,
        ImagesTable.storage_path
    )
    result: Result[Tuple[int, str, str]] = await db_session.execute(query)
    return result.fetchall()


async def get_image_records_by_ids(
    db_session: AsyncSession,
    ids: list[int]
) -> dict[int, tuple[str, str]]:
    """
    Возвращает dict {id: (filename, storage_path)} для указанных ID.
    Используется для получения метаданных изображений после FAISS поиска.
    """
    if not ids:
        return {}

    query = select(
        ImagesTable.id,
        ImagesTable.filename,
        ImagesTable.storage_path
    ).where(ImagesTable.id.in_(ids))

    result: Result[Tuple[int, str, str]] = await db_session.execute(query)
    records = result.fetchall()

    return {row[0]: (row[1], row[2]) for row in records}
