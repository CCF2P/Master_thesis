import os

from fastapi.responses import RedirectResponse
from fastapi import (
    APIRouter,
    Request
)

from Routers.Template import templates
from NNModels.NeuralNetworkModel import ModelLoader, SiameseMetricModel
from NNModels.FeatureExtractor import FeatureExtractor


main_router = APIRouter()

CHECKPOINT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../NNModels/PretrainedModels/final_model.pth"
)
BACKBONE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../../ForNNTrain/backbones/smiMIM_backbone_convnext_tiny_batch_24_final_correct.pth"
)

model_loader = ModelLoader()
model_loader.load(
    checkpoint_path=os.path.normpath(CHECKPOINT_PATH),
    backbone_name="convnext_tiny",
    embedding_dim=512,
    backbone_path=os.path.normpath(BACKBONE_PATH) if os.path.exists(os.path.normpath(BACKBONE_PATH)) else None,
    device="cuda"
)

model: SiameseMetricModel = model_loader.get_model()
device = model_loader.get_device()

extractor = FeatureExtractor()
extractor.initialize(model=model, device=device, target_size=(224, 224))


# ============================================================
# -------------------- PAGE ROUTERS ---------------------------
# ============================================================
@main_router.get(path="/", summary="Home page")
async def get_index_html(request: Request):
    try:
        return templates.TemplateResponse(
            name="/RU/indexRU.html",
            context={"request": request}
        )
    except Exception:
        return templates.TemplateResponse(
            name="/RU/errorRU.html",
            context={
                "request": request,
                "error_message": "Страница не найдена."
            },
            status_code=500
        )


@main_router.get(path="/upload/", summary="Upload page")
async def get_upload_html(request: Request):
    """Redirect to compare page which contains upload functionality."""
    return RedirectResponse(url="/compare/")


@main_router.get(path="/compare/", summary="Compare page")
async def get_compare_html(request: Request):
    try:
        return templates.TemplateResponse(
            name="/RU/compareRU.html",
            context={"request": request}
        )
    except Exception:
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
    return RedirectResponse(url="/compare/")
