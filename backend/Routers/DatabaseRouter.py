import uuid
import asyncio
from datetime import datetime
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

from Routers.Template import templates
from Databases.Database import get_async_session, get_all_image_records

from NNModels.ProcessingImage import get_val_transforms
from NNModels.NeuralNetworkModel import predict_pair_async, get_image_bytes_by_path
from Routers.MainRouter import model, device

database_router = APIRouter()


async def save_image(image: UploadFile) -> tuple[Path, str]:
    file_path = None
    try:
        img_bytes = await image.read()
        filename = f"{image.filename}"

        UPLOAD_DIR = Path(__file__).parent / Path("Templates/Static/Uploads")
        UPLOAD_DIR.mkdir(exist_ok=True)

        file_path = UPLOAD_DIR / filename
        with open(file_path, "wb") as f:
            f.write(img_bytes)
    except Exception as e:
        raise Exception(e)
    return (file_path, filename)


def get_url_for_image(request, image_path) -> str:
    return request.url_for("Static", path=f"Uploads/{image_path}")


async def compare_images(file_path1, file_path2):
    try:
        img_bytes1 = await get_image_bytes_by_path(file_path1)
        img_bytes2 = await get_image_bytes_by_path(file_path2)

        if img_bytes1 is None or img_bytes2 is None:
            raise Exception("One of image have zero bytes")

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
        print(f"[ERROR] While compare images: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка сравнения одного из изображений"
        )
    return prob


async def compare_single_record(
    user_img_path,
    record: tuple[int, str, str]
):
    id_, name, path = record
    prob = await compare_images(user_img_path, path)
    if prob is not None:
        return (id_, path, name, prob)
    return None


async def find_top_similar(
    query_img_path,
    db_session: AsyncSession,
    top_k: int=5,
    parallel: bool=True
) -> list:
    """
    Находит топ-k похожих изображений в БД.
    Если parallel=True, использует asyncio.gather для параллельных сравнений.
    """
    print("[INFO ] Get all image records from database")
    records = await get_all_image_records(db_session)
    if not records:
        print("[WARN ] No images found in database")
        return []

    if parallel:
        print("[INFO ] Start parallel image search")
        tasks = [compare_single_record(query_img_path, record) for record in records] #type: ignore
        results = await asyncio.gather(*tasks)
        results = [r for r in results if r is not None]
    else:
        print("[INFO ] Start a sequential image search")
        results = []
        for record in records:
            res = compare_single_record(query_img_path, record) #type: ignore
            if res:
                results.append(res)

    # Сортировка по убыванию вероятности
    results.sort(key=lambda x: x[3], reverse=True)
    return results[:top_k]


# /////////////////////////////////////////////////////
# /////////////////// Post routers ////////////////////
# /////////////////////////////////////////////////////
@database_router.post(
    path="/search/",
    summary="Search page"
)
async def search_files(
    request: Request,
    user_image: UploadFile,
    db_session: AsyncSession=Depends(get_async_session)
):
    if user_image.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось загрузить изображение для поиска в базе данных"
        )
    if not user_image.filename.endswith(('.dcm', '.png', '.jpg', '.jpeg')):
        detail="Ошибка загрузки!<br>" \
            + "Разрешены файлы следующих форматов:" \
            + ".png, .jpeg (.jpg)"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

    user_file_path = None
    user_filename = "uploaded_image"
    print("[INFO ] Saving image for search in database")
    try:
        user_file_path, user_filename = await save_image(user_image)
    except Exception as e:
        print(f"[ERROR] Saving uploaded image for display: {e}")

    try:
        print("[INFO ] Start searching in database")
        top_results = await find_top_similar(
            query_img_path=user_file_path,
            db_session=db_session,
            top_k=5,
            parallel=True
        )
    except Exception as e:
        print(f"[ERROR] Search process failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка поиска в базе данных"
        )

    features = []
    for idx, (db_id, db_path, db_filename, similarity_prob) in enumerate(top_results):
        features.append({
            "rank": idx + 1,
            "db_id": db_id,
            "db_filename": db_filename,
            "db_path": "добавить ссылку для просмотра", # Отображать путь или URL?
            "similarity": round(similarity_prob * 100, 2)
        })
    best_similarity = round(top_results[0][3] * 100, 2) if top_results else 0.0

    return templates.TemplateResponse(
        name="/RU/resultRU.html",
        context={
            "type": "search",
            "request": request,
            "img1_url": get_url_for_image(request, user_filename),
            "img2_url": get_url_for_image(request, top_results[0][1]),
            "similarity_score": best_similarity,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "features": features,
        }
    )


@database_router.post(
    path="/compare/",
    summary="Compare page"
)
async def compare_files(
    request: Request,
    user_image: UploadFile,
    user_image1: UploadFile
):
    if user_image.filename is None or user_image1.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось загрузить изображения для сравнения"
        )
    if not user_image.filename.endswith(('.dcm', '.png', '.jpg', '.jpeg')) \
    and not user_image1.filename.endswith(('.dcm', '.png', '.jpg', '.jpeg')):
        detail="Ошибка загрузки!<br>" \
            + "Разрешены файлы следующих форматов:" \
            + ".png, .jpeg (.jpg)"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

    try:
        file_path1, filename1 = await save_image(user_image)
        file_path2, filename2 = await save_image(user_image1)

        prob = await compare_images(file_path1, file_path2)
    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка сравнения"
        )

    return templates.TemplateResponse(
        name="/RU/resultRU.html",
        context={
            "type": "compare",
            "request": request,
            "img1_url": get_url_for_image(request, filename1),
            "img2_url": get_url_for_image(request, filename2),
            "similarity_score": round(prob * 100, 2),
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "features": [],
        }
    )
