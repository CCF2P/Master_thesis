from datetime import datetime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import (
    Column,
    DateTime,
    Text,
    Integer,
    JSON,
    String
)

# Create a DeclarativeMeta instance
class Base (DeclarativeBase):
    pass


class ImagesTable(Base):
    __tablename__ = "images"
    id = Column(
        Integer,
        nullable=False,
        primary_key=True,
        autoincrement=True
    )
    patient_id = Column(
        String(50),
        nullable=False
    )
    filename = Column(
        String(255),
        nullable=False
    )
    storage_path = Column(
        Text,
        nullable=False
    )
    upload_date = Column(
        DateTime,
        default=datetime.now
    )
    age = Column(Integer)
    sex = Column(String(1))
    metadata_ = Column("metadata", JSON)


class Feature(Base):
    __tablename__ = "features"
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    feature = Column(JSON)
    identifier = Column(String, unique=True)
