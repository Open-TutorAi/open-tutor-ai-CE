"""Assignment domain models — assignments + submissions.

Part of the `assignments` bounded context. An assignment belongs to a classroom;
each enrolled student may submit once. Per-student status (missed/on-time/late/graded)
is a computed read model, not a stored field.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from data.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String(36), primary_key=True)
    classroom_id = Column(
        String(36),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    instructions = Column(Text, nullable=True)
    attachment_id = Column(String(36), nullable=True)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    submissions = relationship(
        "Submission", back_populates="assignment", cascade="all, delete-orphan"
    )
    # Exam (proctoring) data is purged with the assignment. SQLite FK enforcement is
    # off, so cascade is handled at the ORM level here.
    exam_config = relationship(
        "ExamConfig", cascade="all, delete-orphan", passive_deletes=False
    )
    exam_sessions = relationship(
        "ExamSession", cascade="all, delete-orphan", passive_deletes=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "classroom_id": self.classroom_id,
            "created_by": self.created_by,
            "title": self.title,
            "instructions": self.instructions,
            "attachment_id": self.attachment_id,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint(
            "assignment_id", "student_id", name="uq_submission_assignment_student"
        ),
    )

    id = Column(String(36), primary_key=True)
    assignment_id = Column(
        String(36),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=True)
    attachment_id = Column(String(36), nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_late = Column(Boolean, default=False, nullable=False)
    grade = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    graded_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="submitted")

    assignment = relationship("Assignment", back_populates="submissions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "student_id": self.student_id,
            "content": self.content,
            "attachment_id": self.attachment_id,
            "submitted_at": (
                self.submitted_at.isoformat() if self.submitted_at else None
            ),
            "is_late": self.is_late,
            "grade": self.grade,
            "feedback": self.feedback,
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
            "status": self.status,
        }
