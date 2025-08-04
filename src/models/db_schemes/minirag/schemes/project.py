from .minirag_base import SqlAlchemyBase
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Project(SqlAlchemyBase):

    __tablename__ = "projects"

    project_id = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    project_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)  # type: ignore

    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)  # type: ignore
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)  # type: ignore
