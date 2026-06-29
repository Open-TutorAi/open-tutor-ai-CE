"""File record domain model."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from data.database import Base


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    filename = Column(Text, nullable=False)
    path = Column(Text, nullable=True)  # disk path; None if content stored in data
    content_type = Column(String(255), nullable=True)
    size = Column(Integer, nullable=True)
    data = Column(JSON, nullable=True)  # extracted text / structured content
    meta = Column(JSON, nullable=True)  # arbitrary metadata (tags, source, …)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "content_type": self.content_type,
            "size": self.size,
            "data": self.data,
            "meta": self.meta,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
