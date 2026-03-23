from datetime import datetime
from pydantic import BaseModel

class ImageTable(BaseModel):
    id: int
    patient_id: str
    filename: str
    storage_path: str
    upload_date: datetime
    age: int
    sex: int
    metadata_: dict={}

class ImageOut(ImageTable):
    id: int
    upload_date: datetime

    class Config:
        from_attributes=True

