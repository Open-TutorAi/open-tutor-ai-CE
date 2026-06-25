"""Support request domain model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from data.database import Base


class Support(Base):
    __tablename__ = "supports"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    short_description = Column(Text, nullable=True)
    subject = Column(String(255), nullable=True)
    custom_subject = Column(String(255), nullable=True)
    course_id = Column(String(36), nullable=True)
    learning_objective = Column(Text, nullable=True)
    learning_type = Column(String(100), nullable=True)
    level = Column(String(100), nullable=True)
    content_language = Column(String(100), nullable=True, default="English")
    estimated_duration = Column(String(100), nullable=True)
    access_type = Column(String(50), nullable=True, default="Private")
    keywords = Column(Text, nullable=True)  # comma-separated
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    avatar_id = Column(String(36), nullable=True)
    chat_id = Column(String(36), nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="supports")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "short_description": self.short_description,
            "subject": self.subject,
            "custom_subject": self.custom_subject,
            "course_id": self.course_id,
            "learning_objective": self.learning_objective,
            "learning_type": self.learning_type,
            "level": self.level,
            "content_language": self.content_language,
            "estimated_duration": self.estimated_duration,
            "access_type": self.access_type,
            "keywords": self.keywords.split(",") if self.keywords else None,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "avatar_id": self.avatar_id,
            "chat_id": self.chat_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SupportFile(Base):
    __tablename__ = "support_files"

    id = Column(String(36), primary_key=True)
    support_id = Column(
        String(36), ForeignKey("supports.id", ondelete="CASCADE"), nullable=False
    )
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    support = relationship("Support", backref="files")
