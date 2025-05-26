import os

from jinja2 import Environment, FileSystemLoader

from fastapi.templating import Jinja2Templates
from fastapi import (
    APIRouter,
    Request,
    Depends,
    HTTPException,
    File,
    UploadFile,
)

# Build path to "Templates" folder from OS root folder
template_path = os.path.join(os.path.dirname(__file__), "Templates")
# Creating an environment with FileSystemLoader to collect relative
# folder paths to HTML templates
env = Environment(loader=FileSystemLoader(template_path))
# Connected templates that are in the environment
templates = Jinja2Templates(env=env)

main_router = APIRouter()


@main_router.get(path="/", summary="Home page")
async def get_index_html(request: Request):
    try:
        return templates.TemplateResponse(
            name="index.html",
            context={'request': request}
        )
    except:
        if "text/html" in request.headers.get("Accept"):
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


@main_router.get(path="/upload", summary="Upload page")
async def get_index_html(request: Request):
    try:
        return templates.TemplateResponse(
            name="upload.html",
            context={"request": request}
        )
    except:
        if "text/html" in request.headers.get("Accept"):
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


@main_router.get(path="/compare", summary="Compare page")
async def get_index_html(request: Request):
    try:
        print(request.headers.get("Accept"))
        return templates.TemplateResponse(
            name="compare.html",
            context={"request": request}
        )
    except:
        if "text/html" in request.headers.get("Accept"):
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
