from typing import List

from fastapi.responses import RedirectResponse
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    delete,
    insert,
    select
)

from Routers.Template import templates
from Models.Model import Feature
from Databases.Database import (
    get_async_session,
    get_feature_by_identifier
)

database_router = APIRouter()


'''@database_router.get("/")
async def test(db_session: AsyncSession = Depends(get_async_session)):
    query = select(TestTable)
    result = await db_session.execute(query)
    return result.scalars().all()'''


# /////////////////////////////////////////////////////
# /////////////////// Post routers ////////////////////
# /////////////////////////////////////////////////////
@database_router.post(
    path="/compareEN/",
    summary="Compare page",
    response_model=Feature
)
async def compare_files(
    request: Request,
    user_images: List[UploadFile],
    #db_session: AsyncSession=Depends(get_async_session)
):
    for user_image in user_images:
        if not user_image.filename.endswith('.dcm'):
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only DICOM files are allowed"
                )
        print(user_image.filename)
    return templates.TemplateResponse(
        name="/EN/resultEN.html",
        context={
            "request": request,
            "result": "test",
            "identifier": "test"
        }
    )
