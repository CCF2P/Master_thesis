from fastapi.responses import RedirectResponse
from fastapi import (
    APIRouter,
    Request
)

from Routers.Template import templates
from NNModels.NeuralNetworkModel import ModelLoader


# Main router for handling web page routes
main_router = APIRouter()

# Initialize neural network model loader
model_loader = ModelLoader()
# Load pretrained model from checkpoint with specified backbone and device
model_loader.load(
    checkpoint_path="NNModels/PretrainedModels/final_model.pth",
    backbone_name="convnext_tiny",
    device="cuda"
)
# Get loaded model instance for inference
model = model_loader.get_model()
# Get device (CPU/CUDA) where model is loaded
device = model_loader.get_device()


# /////////////////////////////////////////////////////
# /////////////////// Get routers /////////////////////
# /////////////////////////////////////////////////////
@main_router.get(path="/", summary="Home page")
async def get_index_html(request: Request):
    """Render main/home page with Russian language template"""
    try:
        return templates.TemplateResponse(
            name="/RU/indexRU.html",
            context={'request': request}
        )
    except:
        return templates.TemplateResponse(
            name="/RU/errorRU.html",
            context={
                "request": request,
                "error_message": "Страница не найдена."
            },
            status_code=500
        )


@main_router.get(path="/upload/", summary="Upload page")
async def get_uploadRU_html(request: Request):
    """Render upload page where users can upload images for processing"""
    try:
        return templates.TemplateResponse(
            name="/RU/uploadRU.html",
            context={"request": request}
        )
    except:
        return templates.TemplateResponse(
            name="/RU/errorRU.html",
            context={
                "request": request,
                "error_message": "Страница не найдена."
            },
            status_code=500
        )


@main_router.get(path="/compare/", summary="Compare page")
async def get_compareRU_html(request: Request):
    """Render compare page for comparing different images or results"""
    try:
        return templates.TemplateResponse(
            name="/RU/compareRU.html",
            context={"request": request}
        )
    except:
        return templates.TemplateResponse(
            name="/RU/errorRU.html",
            context={
                "request": request,
                "error_message": "Страница не найдена"
            },
            status_code=500
        )


@main_router.get(path="/result/", summary="Result page")
async def get_result_html(request: Request):
    """Redirect result page to upload page (result page is accessed after upload processing)"""
    return RedirectResponse(url="/upload/")


# ================== Features extraction pages ========================