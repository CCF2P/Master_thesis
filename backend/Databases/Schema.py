from datetime import datetime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import (
    Column,
    Integer,
    JSON,
    String
)

# Create a DeclarativeMeta instance
class Base (DeclarativeBase):
    pass


class TestTable(Base):
    __tablename__ = "test"
    id = Column(
        Integer,
        nullable=False,
        primary_key=True,
        autoincrement=True
    )
    msg = Column(String(40))


class ImagesTable(Base):
    __tablename__ = "images"
    id = Column(
        Integer,
        nullable=False,
        primary_key=True,
        autoincrement=True
    )
    patient_id = Column(
        Integer,
        nullable=False
    )
    filename = Column(
        String(50),
        nullable=False
    )
    storage_path = Column(
        String(255),
        nullable=False
    )
    upload_data = Column(
        DateTime,
        default=datetime.now
    )
    age = Column(Integer)
    sex = Column(String(1))
    metadata = Column(JSON)


class Feature(Base):
    __tablename__ = "features"
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    feature = Column(JSON)
    identifier = Column(String, unique=True)
