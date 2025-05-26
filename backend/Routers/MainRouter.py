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
                name="index.html",
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


@main_router.get(path="/upload/", summary="Upload page")
async def get_index_html(request: Request):
    if "text/html" in request.headers.get("Accept"):
        try:
            return templates.TemplateResponse(
                name="upload.html",
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


@main_router.get(path="/compare/", summary="Compare page")
async def get_index_html(request: Request):
    if "text/html" in request.headers.get("Accept"):
        try:
            print(request.headers.get("Accept"))
            return templates.TemplateResponse(
                name="compare.html",
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
