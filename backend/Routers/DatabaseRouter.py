from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    delete,
    insert,
    select
)

from Routers.Template import templates
from Databases.Database import (
    get_async_session,
    get_feature_by_identifier
)

database_router = APIRouter()


'''@database_router.get("/")
async def test(db_session: AsyncSession = Depends(get_async_session)):
    query = select(TestTable)
    result = await db_session.execute(query)
    return result.scalars().all()'''


# /////////////////////////////////////////////////////
# /////////////////// Post routers ////////////////////
# /////////////////////////////////////////////////////
@database_router.post(path="/compareEN/", summary="Compare page")
def upload_files(
    request: Request,
    user_images: List[UploadFile],
    #db_session: AsyncSession=Depends(get_async_session)
):
    for user_image in user_images:
        if not user_image.filename.endswith('.dcm'):
            raise HTTPException(
                    status_code=400,
                    detail="Only DICOM files are allowed"
                )
        print(user_image.filename)
        '''existing_feature = get_feature_by_identifier(
            identifier=user_image.filename,
            db_session=db_session
        )
        if not existing_feature:
            features = compare.extract_features(user_image, vgg19_model)
            features = json.dumps(features.tolist())
            db_feature = crud.create_feature(
                db,
                features,
                identifier=user_image.filename
            )'''
