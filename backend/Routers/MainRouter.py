from fastapi import (
    APIRouter,
    HTTPException,
    Request
)

from Routers.Template import templates
from NNModels.NeuralNetworkModel import ModelLoader, predict_pair_async

main_router = APIRouter()

model_loader = ModelLoader()
model_loader.load(
    checkpoint_path="NNModels/PretrainedModels/final_model.pth",
    backbone_name="convnext_tiny",
    device="cuda"
)
model = model_loader.get_model()
device = model_loader.get_device()

# /////////////////////////////////////////////////////
# /////////////////// Get routers /////////////////////
# /////////////////////////////////////////////////////

# ================== Home pages ========================
@main_router.get(path="/", summary="Home page")
async def get_index_html(request: Request):
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


# ================== Upload pages ========================
@main_router.get(path="/upload/", summary="Upload page")
async def get_uploadRU_html(request: Request):
    try:
        return templates.TemplateResponse(
            name="RU/uploadRU.html",
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


# ================== Compare pages ========================
@main_router.get(path="/compare/", summary="Compare page")
async def get_compareRU_html(request: Request):
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


# ================== Result pages ========================
@main_router.get(path="/result/", summary="Result page")
async def get_result_html(request: Request):
    try:
        features = [
            {"name": "bla", "value1": "bla", "value2": "bla", "similarity": "99"}
        ]
        return templates.TemplateResponse(
            name="/RU/resultRU.html",
            context={
                "request": request,
                "image2_filename": "25.png",
                "result": 777,
                "similarity_score": 99,
                "identifier": "id_777",
                "analysis_date": "analysis_date",
                "features": features,
            }
        )
    except:
        return templates.TemplateResponse(
            name="/EN/errorEN.html",
            context={
                "request": request,
                "error_message": "Страница не найдена."
            },
            status_code=500
        )


# ================== Features extraction pages ========================