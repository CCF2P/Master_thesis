import os
import hashlib
from typing import TypedDict, List
from datetime import datetime
from pathlib import Path

import torch
import numpy as np

from fastapi.responses import FileResponse, Response
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    status
)

from sqlalchemy.ext.asyncio import AsyncSession

from Routers.Template import templates
from Routers.MainRouter import model, device, extractor

from Databases.Database import get_async_session, get_image_records_by_ids
from VectorIndex.FAISSIndex import FAISSIndex


ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

COMPARE_THRESHOLD = 0.95

INDEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../VectorIndex")

faiss_index = FAISSIndex()
if os.path.exists(os.path.join(INDEX_DIR, "faiss_index.bin")):
    faiss_index.load(INDEX_DIR)
else:
    print("[WARN ] FAISS index not found. Search will be unavailable until index is built.")


class SearchResult(TypedDict):
    rank: int
    db_id: int
    db_filename: str
    similarity: float


def sanitize_filename(filename: str) -> str:
    """Remove path components from filename to prevent directory traversal."""
    return Path(filename).name


def get_file_md5(filepath: str) -> str:
    """Compute MD5 hash of a file."""
    h = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return "error"


def validate_extension(filename: str) -> bool:
    """Check if file has an allowed extension."""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


async def save_image(image: UploadFile) -> tuple[str, str]:
    """
    Save uploaded image to the uploads directory.
    Returns (filename, original_filename).
    """
    img_bytes = await image.read()
    filename = sanitize_filename(image.filename or "uploaded_image")

    UPLOAD_DIR = Path(__file__).parent / "Templates/Static/Uploads"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    file_path = UPLOAD_DIR / filename
    with open(file_path, "wb") as f:
        f.write(img_bytes)

    return filename, filename


def get_url_for_image(request: Request, image_path: str, static: bool = True) -> str:
    """Generate URL for images (static uploads or database files)."""
    if static:
        return str(request.url_for("Static", path=f"Uploads/{image_path}"))
    else:
        return str(request.url_for("get_nonstatic_files", filepath=image_path))


# ============================================================
# -------------------- GET ROUTERS ----------------------------
# ============================================================
database_router = APIRouter()


@database_router.get(
    path="/nonStaticFiles/{filepath:path}",
    summary="Serve non-static files from database storage"
)
async def get_nonstatic_files(filepath: str) -> FileResponse:
    """
    Serve files from database storage.
    Path traversal is blocked by validating the resolved path.
    """
    resolved = os.path.realpath(filepath)

    if not os.path.isfile(resolved):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return FileResponse(resolved)


# ============================================================
# -------------------- POST ROUTERS ---------------------------
# ============================================================
@database_router.post(
    path="/search/",
    summary="Search for similar images using FAISS vector index"
)
async def search_files(
    request: Request,
    user_image: UploadFile,
    db_session: AsyncSession = Depends(get_async_session)
) -> Response:
    """
    Search for similar images in database using FAISS vector search.
    Extracts embedding from uploaded image and finds top-k most similar.
    """
    if user_image.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось загрузить изображение для поиска в базе данных"
        )

    if not validate_extension(user_image.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка загрузки!<br>"
                   "Разрешены файлы следующих форматов: .png, .jpeg (.jpg)"
        )

    if not faiss_index.is_built():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Векторный индекс не построен. Обратитесь к администратору."
        )

    user_filename = "uploaded_image"
    try:
        user_filename, _ = await save_image(user_image)
    except Exception as e:
        print(f"[ERROR] Saving uploaded image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка сохранения изображения"
        )

    user_file_path = str(Path(__file__).parent / "Templates/Static/Uploads" / user_filename)

    try:
        print("[INFO ] Extracting embedding for search...")
        query_embedding = extractor.extract_from_path(user_file_path)
    except Exception as e:
        print(f"[ERROR] Embedding extraction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обработки изображения"
        )

    try:
        print("[INFO ] Searching FAISS index...")
        top_results = faiss_index.search(query_embedding, k=5)
    except Exception as e:
        print(f"[ERROR] FAISS search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка поиска в базе данных"
        )

    if not top_results:
        print("[WARN ] No similar images found")
        features: List[SearchResult] = []
        best_similarity = 0.0
        top_result_path = ""
    else:
        db_ids = [r[0] for r in top_results]
        records = await get_image_records_by_ids(db_session, db_ids)

        features = []
        for rank, (db_id, similarity_score) in enumerate(top_results, start=1):
            filename, storage_path = records.get(db_id, ("unknown", ""))
            features.append({
                "rank": rank,
                "db_id": db_id,
                "db_filename": filename,
                "db_path": storage_path,
                "similarity": round(similarity_score * 100, 2)
            })

        best_similarity = round(top_results[0][1] * 100, 2)
        top_db_id = top_results[0][0]
        _, top_result_path = records.get(top_db_id, ("", ""))
        print(f"[INFO ] Best match: db_id={top_db_id}, similarity={best_similarity}%")

        # ============================================================
        # DEBUG: File comparison diagnostics
        # ============================================================
        print("=" * 60)
        print("[DEBUG] Search diagnostics:")
        print(f"  Query file:    {user_file_path}")
        print(f"  Query MD5:     {get_file_md5(user_file_path)}")
        print(f"  Query size:    {os.path.getsize(user_file_path)} bytes")
        print(f"  Best match:    {top_result_path}")
        print(f"  Best MD5:      {get_file_md5(top_result_path)}")
        if os.path.exists(top_result_path):
            print(f"  Best size:     {os.path.getsize(top_result_path)} bytes")
        else:
            print(f"  Best size:     FILE NOT FOUND")
        print(f"  Files equal:   {get_file_md5(user_file_path) == get_file_md5(top_result_path)}")
        print(f"  Cosine sim:    {top_results[0][1]:.6f}")

        # Print all top-5 results for comparison
        for rank, (db_id, sim) in enumerate(top_results, start=1):
            fname, fpath = records.get(db_id, ("?", "?"))
            print(f"  [{rank}] db_id={db_id}, sim={sim:.4f}, file={fname}, path={fpath}")
        print("=" * 60)

    return templates.TemplateResponse(
        name="/RU/resultRU.html",
        context={
            "type": "search",
            "request": request,
            "img1_url": get_url_for_image(request, user_filename),
            "img2_url": get_url_for_image(request, top_result_path, static=False) if top_result_path else "",
            "similarity_score": best_similarity,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "features": features,
        }
    )


@database_router.post(
    path="/compare/",
    summary="Compare two uploaded images"
)
async def compare_files(
    request: Request,
    user_image: UploadFile,
    user_image1: UploadFile
) -> Response:
    """
    Compare two uploaded images directly using the siamese model.
    """
    if user_image.filename is None or user_image1.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось загрузить изображения для сравнения"
        )

    if not validate_extension(user_image.filename) or not validate_extension(user_image1.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка загрузки!<br>"
                   "Разрешены файлы следующих форматов: .png, .jpeg (.jpg)"
        )

    try:
        filename1, _ = await save_image(user_image)
        filename2, _ = await save_image(user_image1)

        file_path1 = str(Path(__file__).parent / "Templates/Static/Uploads" / filename1)
        file_path2 = str(Path(__file__).parent / "Templates/Static/Uploads" / filename2)

        emb1 = extractor.extract_from_path(file_path1)
        emb2 = extractor.extract_from_path(file_path2)

        emb1_tensor = torch.from_numpy(emb1).unsqueeze(0).to(device)
        emb2_tensor = torch.from_numpy(emb2).unsqueeze(0).to(device)

        with torch.no_grad():
            logits = model.classify_pair(emb1_tensor, emb2_tensor)
            prob = float(torch.sigmoid(logits).item())

        is_same = prob >= COMPARE_THRESHOLD
        verdict = "Один человек" if is_same else "Разные люди"

    except Exception as e:
        print(f"[ERROR] Comparison failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка сравнения изображений"
        )

    return templates.TemplateResponse(
        name="/RU/resultRU.html",
        context={
            "type": "compare",
            "request": request,
            "img1_url": get_url_for_image(request, filename1),
            "img2_url": get_url_for_image(request, filename2),
            "is_same": is_same,
            "verdict": verdict,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "features": [],
        }
    )
