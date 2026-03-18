from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)

from Databases.Schema import Feature

SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:2716@127.0.0.1:1488/optg_images"

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


async def get_feature_by_identifier(
    identifier: str,
    db_session: AsyncSession = Depends(get_async_session)
):
    return db_session.query(Feature) \
                     .filter(Feature.identifier == identifier) \
                     .first()


async def create_feature(
    feature: dict,
    identifier: str,
    db_session: AsyncSession = Depends(get_async_session)
):
    db_feature = Feature(feature=feature, identifier=identifier)
    db_session.add(db_feature)
    db_session.commit()
    db_session.refresh(db_feature)
    return db_feature

