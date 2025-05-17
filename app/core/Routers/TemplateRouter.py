import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader

# Build path to "Templates" folder from OS root folder
template_path = os.path.join(os.path.dirname(__file__), "Templates")
# Creating an environment with FileSystemLoader to collect relative
# folder paths to HTML templates
env = Environment(loader=FileSystemLoader(template_path))

template_router = APIRouter()
# Connected templates that are in the environment
templates = Jinja2Templates(env=env)

@template_router.get(path="/", summary="Home page")
async def get_index_html(request: Request):
    try:
        return templates.TemplateResponse(
                        name='index.html',
                        context={'request': request}
                    )
    except:
        return templates.TemplateResponse(
                        name='error.html',
                        context={
                            'request': request,
                            "error_message": "Opps! Some error occurred."
                        }
                    )

@template_router.get(path="/upload", summary="Upload page")
async def get_index_html(request: Request):
    try:
        return templates.TemplateResponse(
                            name='upload.html',
                            context={'request': request}
                        )
    except:
        return templates.TemplateResponse(
                        name='error.html',
                        context={
                            'request': request,
                            "error_message": "Opps! Some error occurred."
                        }
                    )

@template_router.get(path="/compare", summary="Compare page")
async def get_index_html(request: Request):
    try:
        return templates.TemplateResponse(
                            name='compare.html',
                            context={'request': request}
                        )
    except:
        return templates.TemplateResponse(
                        name='error.html',
                        context={
                            'request': request,
                            "error_message": "Opps! Some error occurred."
                        }
                    )
