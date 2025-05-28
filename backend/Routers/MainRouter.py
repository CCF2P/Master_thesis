from fastapi import (
    APIRouter,
    HTTPException,
    Request
)

from Routers.Template import templates

main_router = APIRouter()


# /////////////////////////////////////////////////////
# /////////////////// Get routers /////////////////////
# /////////////////////////////////////////////////////
@main_router.get(path="/", summary="Home page")
async def get_index_html(request: Request):
    if "text/html" in request.headers.get("Accept"):
        try:
            return templates.TemplateResponse(
                name="/RU/indexRU.html",
                context={'request': request}
            )
        except:
            return templates.TemplateResponse(
                name="error.html",
                context={
                    "request": request,
                    "error_message": "Страница не найдена."
                },
                status_code=500
            )
    elif "application/json" in request.headers.get("Accept"):
        return HTTPException(
            detail="Страница не найдена.",
            status_code=500
        )
    

@main_router.get(path="/en", summary="Home page")
async def get_index_html(request: Request):
    if "text/html" in request.headers.get("Accept"):
        try:
            return templates.TemplateResponse(
                name="/EN/indexEN.html",
                context={'request': request}
            )
        except:
            return templates.TemplateResponse(
                name="error.html",
                context={
                    "request": request,
                    "error_message": "Page is not found."
                },
                status_code=500
            )
    elif "application/json" in request.headers.get("Accept"):
        return HTTPException(
            detail="Page is not found.",
            status_code=500
        )


@main_router.get(path="/uploadEN/", summary="Upload page")
async def get_index_html(request: Request):
    if "text/html" in request.headers.get("Accept"):
        try:
            return templates.TemplateResponse(
                name="EN/upload.html",
                context={"request": request}
            )
        except:
            return templates.TemplateResponse(
                name="error.html",
                context={
                    "request": request,
                    "error_message": "Page is not found."
                },
                status_code=500
            )
    elif "application/json" in request.headers.get("Accept"):
            return HTTPException(
                detail="Page is not found.",
                status_code=500
            )


@main_router.get(path="/compareRU/", summary="Compare page")
async def get_index_html(request: Request):
    if "text/html" in request.headers.get("Accept"):
        try:
            return templates.TemplateResponse(
                name="/RU/compareRU.html",
                context={"request": request}
            )
        except:
            return templates.TemplateResponse(
                name="error.html",
                context={
                    "request": request,
                    "error_message": "Страница не найдена"
                },
                status_code=500
            )
    elif "application/json" in request.headers.get("Accept"):
        return HTTPException(
            detail="Страница не найдена",
            status_code=500
        )


@main_router.get(path="/compareEN/", summary="Compare page")
async def get_index_html(request: Request):
    if "text/html" in request.headers.get("Accept"):
        try:
            return templates.TemplateResponse(
                name="/EN/compareEN.html",
                context={"request": request}
            )
        except:
            return templates.TemplateResponse(
                name="error.html",
                context={
                    "request": request,
                    "error_message": "Page is not found."
                },
                status_code=500
            )
    elif "application/json" in request.headers.get("Accept"):
        return HTTPException(
            detail="Page is not found.",
            status_code=500
        )
