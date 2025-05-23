from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import (
    Column,
    Integer,
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
