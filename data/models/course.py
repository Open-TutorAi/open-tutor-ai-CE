"""Course model for saving generated learning paths."""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from data.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    subject = Column(String(255), nullable=False)
    level = Column(String(50), nullable=False)
    objective = Column(String(255), nullable=False)
    chapters = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "subject": self.subject,
            "level": self.level,
            "objective": self.objective,
            "chapters": self.chapters,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
