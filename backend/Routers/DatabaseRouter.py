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
    path="/compare/",
    summary="Compare page"
)
async def compare_files(
    request: Request,
    user_image: UploadFile,
    user_image1: UploadFile=None,
    #db_session: AsyncSession=Depends(get_async_session)
):
    if not user_image.filename.endswith('.dcm'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only DICOM files are allowed.\n" \
                + "Разрешены только DICOM файлы."
        )
    if user_image1 is not None:
        if not user_image1.filename.endswith('.dcm'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only DICOM files are allowed.\n" \
                    + "Разрешены только DICOM файлы."
            )
    # обработка изображений...
    features = [
        {"name": "bla", "value1": "bla", "value2": "bla", "similarity": "99"}
    ]
    if not request.headers.get("referer").find("EN") == -1:
        return templates.TemplateResponse(
            name="/EN/resultEN.html",
            context={
                "request": request,
                "image2_filename": "25.png",
                "result": 777,
                "similarity_score": 99,
                "identifier": "id_777",
                "analysis_date": "analysis_date",
                "features": features,

            }
        )
    elif not request.headers.get("referer").find("RU") == -1:
        return templates.TemplateResponse(
            name="/RU/resultRU.html",
            context={
                "request": request,
                "image2_filename": "25.png",
                "result": 777,
                "similarity_score": 99,
                "identifier": "id_777",
                "analysis_date": "analysis_date",
                "features": features,

            }
        )
    else:
        return templates.TemplateResponse(
            name="/EN/errorEN.html",
            context={
                "request": request,
                "error_message": "Server error."
            },
            status_code=500
        )
