from typing import Tuple, Sequence, TypedDict, List

import asyncio
from datetime import datetime
from pathlib import Path

from fastapi.responses import FileResponse, Response
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    status
)

from sqlalchemy import Row
from sqlalchemy.ext.asyncio import AsyncSession

from Routers.Template import templates
from Routers.MainRouter import model, device

from Databases.Database import get_async_session, get_all_image_records

from NNModels.ProcessingImage import get_val_transforms
from NNModels.NeuralNetworkModel import predict_pair_async, get_image_bytes_by_path


# Dictionary structure for storing image similarity search results
class FeatureDict(TypedDict):
    rank: int          # Rank position in search results (1st, 2nd, etc.)
    db_id: int         # Database record ID
    db_filename: str   # Original filename in database
    db_path: str       # File path in database
    similarity: float  # Similarity score as percentage


# Router for handling database-related operations (search, compare)
database_router = APIRouter()


async def save_image(image: UploadFile) -> Tuple[str, str]:
    """
    Save uploaded image to the uploads directory and return file path with filename
    """
    try:
        img_bytes: bytes = await image.read()
        filename = f"{image.filename}"

        # Directory where uploaded images are stored
        UPLOAD_DIR: Path = Path(__file__).parent / Path("Templates/Static/Uploads")
        UPLOAD_DIR.mkdir(exist_ok=True)

        file_path: Path = UPLOAD_DIR / filename
        # Write image bytes to file
        with open(file_path, "wb") as f:
            f.write(img_bytes)
    except Exception as e:
        raise Exception(e)
    else:
        return (str(file_path), filename)


def get_url_for_image(
    request: Request,
    image_path: str,
    static: bool=True
) -> str:
    """
    Generate accessible URL for images (static uploads or non-static database files)
    """
    # Static images are served via FastAPI's built-in static files mount
    if static:
        return str(request.url_for("Static", path=f"Uploads/{image_path}"))
    else:
        # Non-static files (e.g., database-stored images) use dedicated endpoint
        return str(request.url_for('get_nonstatic_files', filename=image_path))


async def compare_images(file_path1: str, file_path2: str) -> float:
    """
    Compare two images using neural network model and return similarity probability (0-1)
    """
    try:
        img_bytes1: bytes | None = await get_image_bytes_by_path(file_path1)
        img_bytes2: bytes | None = await get_image_bytes_by_path(file_path2)

        if img_bytes1 is None or img_bytes2 is None:
            raise Exception("One of image have zero bytes")

        # Predict similarity using loaded model and validation transforms
        prob = float(await predict_pair_async(
            model=model,
            img_bytes1=img_bytes1,
            img_bytes2=img_bytes2,
            base_tf=get_val_transforms(
                target_size=(224, 224)
            ),
            device=device
        ))
    except Exception as e:
        print(f"[ERROR] While compare images: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка сравнения одного из изображений"
        )
    else:
        return prob


async def compare_single_record(
    user_img_path: str,
    record: Row[Tuple[int, str, str]]
) -> Tuple[int, str, str, float] | None:
    """
    Compare user uploaded image with a single database record and return similarity result
    Returns tuple of (db_id, db_path, db_filename, similarity_prob) or None if comparison fails
    """
    id_, file_name, file_path = record
    # Compare user image with database image and get similarity probability
    prob: float = await compare_images(user_img_path, file_path)
    if prob is not None:
        return (id_, file_path, file_name, prob)
    return None


async def find_top_similar(
    query_img_path: str,
    db_session: AsyncSession,
    top_k: int=5,
    parallel: bool=True
) -> List[Tuple[int, str, str, float]]:
    """
    Find top-k similar images in database by comparing query image with all database records
    Uses neural network model to compute similarity scores for each comparison
    If parallel=True, uses asyncio.gather for concurrent comparisons (faster)
    """
    print("[INFO ] Get all image records from database")
    # Fetch all image records from database: each record is (id, filename, filepath)
    records: Sequence[Row[Tuple[int, str, str]]] = await get_all_image_records(db_session)
    if not records:
        print("[WARN ] No images found in database")
        return []

    # Compare query image with all database records
    if parallel:
        # Parallel mode: create tasks for all comparisons and run them concurrently
        print("[INFO ] Start parallel image search")
        tasks = [compare_single_record(query_img_path, record) for record in records]
        results = await asyncio.gather(*tasks)
        # Filter out None results (failed comparisons)
        results = [r for r in results if r is not None]
    else:
        # Sequential mode: compare images one by one
        print("[INFO ] Start a sequential image search")
        results = []
        for record in records:
            res = await compare_single_record(query_img_path, record)
            if res:
                results.append(res)

    # Sort results by similarity probability in descending order (highest first)
    results.sort(key=lambda x: x[3], reverse=True)
    return results[:top_k]


# /////////////////////////////////////////////////////
# /////////////////// GET routers /////////////////////
# /////////////////////////////////////////////////////
@database_router.get(
    path="/nonStaticFiles/{filepath}",
    summary="For sending non static files"
)
async def get_nonstatic_files(filepath: str) -> FileResponse:
    """
    Serve non-static files (e.g., database-stored images) not in the static directory
    Used to retrieve files that are not part of the default static assets
    """
    return FileResponse(filepath)


# /////////////////////////////////////////////////////
# /////////////////// POST routers ////////////////////
# /////////////////////////////////////////////////////
@database_router.post(
    path="/search/",
    summary="Search page"
)
async def search_files(
    request: Request,
    user_image: UploadFile,
    db_session: AsyncSession=Depends(get_async_session)
) -> Response:
    """
    Handle image search in database - find top similar images to uploaded query image
    """
    # Validate that image was properly uploaded
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

    user_file_path: str | None = None
    user_filename = "uploaded_image"
    print("[INFO ] Saving image for search in database")
    try:
        # Save uploaded image to uploads directory
        user_file_path, user_filename = await save_image(user_image)
    except Exception as e:
        print(f"[ERROR] Saving uploaded image for display: {e}")

    try:
        print("[INFO ] Start searching in database")
        if user_file_path is not None:
            # Find top 5 similar images in database using parallel comparison
            top_results = await find_top_similar(
                query_img_path=user_file_path,
                db_session=db_session,
                top_k=5,
                parallel=True
            )
        else:
            raise Exception(f"[ERROR] Saving uploaded image for display")
    except Exception as e:
        print(f"[ERROR] Search process failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка поиска в базе данных"
        )

    # Build feature list for template rendering with ranked results
    features: List[FeatureDict] = []
    for idx, (db_id, db_path, db_filename, similarity_prob) in enumerate(top_results):
        features.append({
            "rank": idx + 1,
            "db_id": db_id,
            "db_filename": db_filename,
            "db_path": db_path,  # Store path for potential display
            "similarity": round(similarity_prob * 100, 2)  # Convert to percentage
        })
    best_similarity: float = round(top_results[0][3] * 100, 2) if top_results else 0.0
    print(top_results[0])
    return templates.TemplateResponse(
        name="/RU/resultRU.html",
        context={
            "type": "search",
            "request": request,
            "img1_url": get_url_for_image(request, user_filename),
            "img2_url": get_url_for_image(request, "25.png"),  # TODO: use actual top result
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
) -> Response:
    """
    Handle direct comparison between two uploaded images
    """
    # Validate both images are properly uploaded
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
        file_path1: str = ""
        filename1: str = ""
        file_path2: str = ""
        filename2: str = ""

        # Save both uploaded images to uploads directory
        file_path1, filename1 = await save_image(user_image)
        file_path2, filename2 = await save_image(user_image1)

        # Compare the two images using neural network model
        prob: float = await compare_images(file_path1, file_path2)
    except Exception as e:
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
            "similarity_score": round(prob * 100, 2),  # Convert to percentage
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "features": [],  # No feature list for direct comparison
        }
    )
