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


class Feature(Base):
    __tablename__ = "features"
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    feature = Column(JSON)
    identifier = Column(String, unique=True)
