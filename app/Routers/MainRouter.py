import os

from jinja2 import Environment, FileSystemLoader

from fastapi.templating import Jinja2Templates
from fastapi import (
    APIRouter,
    Request,
    Depends,
    HTTPException,
    File,
    UploadFile
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


@main_router.get(path="/upload", summary="Upload page")
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


@main_router.get(path="/compare", summary="Compare page")
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


'''@main_router.post(path="/upload/")
def upload_files(
    user_images: List[UploadFile]=File(...),
    db: Session=Depends(get_db)
):
    for user_image in user_images:
        if not user_image.filename.endswith('.dcm'):
            raise HTTPException(status_code=400, detail="Only DICOM files are allowed")
        
        existing_feature = crud.get_feature_by_identifier(db, user_image.filename)
        if existing_feature:
            continue

        features = compare.extract_features(user_image, vgg19_model)
        features = json.dumps(features.tolist())
        db_feature = crud.create_feature(db, features, identifier=user_image.filename)
    
    return RedirectResponse(url="/", status_code=303)'''
