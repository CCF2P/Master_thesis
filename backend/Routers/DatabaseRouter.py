import os
import uuid
from datetime import datetime
from typing import List
from pathlib import Path

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

from NNModels.ProcessingImage import get_val_transforms
from NNModels.NeuralNetworkModel import predict_pair_async
from Routers.MainRouter import model, device

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
    user_image1: UploadFile
):
    if not user_image.filename.endswith(('.dcm', '.png', '.jpg', '.jpeg')) \
       or not user_image1.filename.endswith(('.dcm', '.png', '.jpg', '.jpeg')):
        detail="Ошибка загрузки!<br>" \
            + "Разрешены файлы следующих форматов:" \
            + ".dcm, .png, .jpeg (.jpg)"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

    try:
        img_bytes1 = await user_image.read()
        img_bytes2 = await user_image1.read()
        filename1 = f"{uuid.uuid4()}_{user_image.filename}"
        filename2 = f"{uuid.uuid4()}_{user_image1.filename}"

        UPLOAD_DIR = Path(__file__).parent / Path("Templates/Static/Uploads")

        file_path1 = UPLOAD_DIR / filename1
        print(file_path1)
        file_path2 = UPLOAD_DIR / filename2
        with open(file_path1, "wb") as f:
            f.write(img_bytes1)
        with open(file_path2, "wb") as f:
            f.write(img_bytes2)

        img1_url = request.url_for("Static", path=f"Uploads/{filename1}")
        img2_url = request.url_for("Static", path=f"Uploads/{filename2}")

        prob = await predict_pair_async(
            model=model,
            img_bytes1=img_bytes1,
            img_bytes2=img_bytes2,
            base_tf=get_val_transforms(
                target_size=(224, 224)
            ),
            device=device
        )
    except Exception as e:
        if "file_path1" in locals() and file_path1.exists():
            os.remove(file_path1)
        if "file_path2" in locals() and file_path2.exists():
            os.remove(file_path2)

        raise HTTPException(
            status_code=500,
            detail=f"Ошибка сравнения: {str(e)}"
        )

    pred = 1 if prob > 0.9 else 0
    features = [
        {
            "name": "bla",
            "value1": user_image.filename,
            "value2": user_image1.filename,
            "similarity": f"prob is {prob}, pred is {pred}"
        }
    ]
    return templates.TemplateResponse(
        name="/RU/resultRU.html",
        context={
            "request": request,
            "img1_url": img1_url,
            "img2_url": img2_url,
            "similarity_score": round(prob * 100, 2),
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "features": features,

        }
    )


@database_router.post(
    path="/search/",
    summary="Search page"
)
async def search_files(
    request: Request,
    user_image: UploadFile,
    #db_session: AsyncSession=Depends(get_async_session)
):
    if not user_image.filename.endswith(('.dcm', '.png', '.jpg', '.jpeg')):
        detail="Ошибка загрузки!<br>" \
            + "Разрешены файлы следующих форматов::" \
            + ".dcm, .png, .jpeg (.jpg)"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

    return templates.TemplateResponse(
        name="/RU/errorRU.html",
        context={
            "request": request,
            "error_message": "дорабатывается страница, понятно"
        }
    )

