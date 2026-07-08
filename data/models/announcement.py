"""Classroom announcement (stream post) model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from data.database import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    classroom_id = Column(String(36), ForeignKey("classrooms.id"), nullable=False)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    classroom = relationship("Classroom")
    author = relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "classroom_id": self.classroom_id,
            "author_id": self.author_id,
            "author_name": self.author.name if self.author else None,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
