from pydantic import BaseModel

class FeatureCreate(BaseModel):
    feature: dict
    identifier: str

class Feature(BaseModel):
    feature: float
    identifier: str

class Config:
    from_attributes = True

class TestTest(BaseModel):
    message: str
