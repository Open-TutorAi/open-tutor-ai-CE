"""Assignment domain models — teacher-authored assignments and student submissions."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from data.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rubric = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "rubric": self.rubric,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True)
    assignment_id = Column(
        String(36),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    extracted_text = Column(Text, nullable=True)
    ai_score = Column(Integer, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    teacher_score = Column(Integer, nullable=True)
    teacher_feedback = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="submitted")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    assignment = relationship("Assignment", backref="submissions")
    user = relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "extracted_text": self.extracted_text,
            "ai_score": self.ai_score,
            "ai_feedback": self.ai_feedback,
            "teacher_score": self.teacher_score,
            "teacher_feedback": self.teacher_feedback,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
