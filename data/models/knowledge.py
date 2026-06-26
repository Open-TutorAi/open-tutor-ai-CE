"""Knowledge base and file models."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text

from data.database import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    data = Column(JSON, nullable=True)
    meta = Column(JSON, nullable=True)  # stores access_control + tags
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "data": self.data,
            "meta": self.meta,
            "access_control": self.meta,  # UI expects access_control
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class KnowledgeFile(Base):
    __tablename__ = "knowledge_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_id = Column(
        String(36), ForeignKey("knowledge_bases.id"), nullable=False, index=True
    )
    file_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "knowledge_id": self.knowledge_id,
            "file_id": self.file_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
