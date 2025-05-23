from fastapi import APIRouter, Depends

from sqlalchemy import insert, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from Databases.Schema import TestTable
from Databases.Database import get_async_session

database_router = APIRouter(prefix="/test", tags=["Main routers"])


@database_router.get("/")
async def get_films(session: AsyncSession = Depends(get_async_session)):
    query = select(TestTable)
    result = await session.execute(query)
    return result.scalars().all()
