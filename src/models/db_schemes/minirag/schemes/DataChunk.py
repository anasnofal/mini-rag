from .minirag_base import SqlAlchemyBase
from sqlalchemy import Column, Integer, DateTime, String, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Index
import uuid


class DataChunk(SqlAlchemyBase):
    __tablename__ = "chunks"

    chunk_id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_uuid = Column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )

    chunk_text = Column(String, nullable=False)
    chunk_metadata = Column(JSONB, nullable=True)
    chunk_order = Column(Integer, nullable=False)
    chunk_project_id = Column(
        Integer, ForeignKey("projects.project_id"), nullable=False
    )
    chunk_asset_id = Column(Integer, ForeignKey("assets.asset_id"), nullable=False)

    project = relationship("Project", back_populates="chunks")
    asset = relationship("Asset", back_populates="chunks")

    __table_args__ = (
        Index("ix_chunk_project_id", chunk_project_id),
        Index("ix_chunk_asset_id", chunk_asset_id),
    )
