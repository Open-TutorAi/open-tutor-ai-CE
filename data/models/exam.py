"""Exam (proctoring) models — Epic E10.

An *exam* is a proctored assignment: marking an assignment with an `ExamConfig`
turns it into one. Each student attempt is an `ExamSession`; every time the student
leaves the exam page (or breaks a rule) an `ExamViolation` is recorded. A browser
cannot truly *prevent* leaving, so this layer is detection + accountability, not a
hard lock (true lockdown needs a managed device / lockdown browser).
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from data.database import Base

# What to do when a student racks up violations.
ON_VIOLATION = ("warn", "flag", "auto_submit")


class ExamConfig(Base):
    """Turns an assignment into a proctored exam (1:1 with the assignment)."""

    __tablename__ = "exam_configs"

    id = Column(String(36), primary_key=True)
    assignment_id = Column(
        String(36),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    time_limit_minutes = Column(Integer, nullable=True)  # None = no timer
    max_violations = Column(Integer, nullable=True)  # None = unlimited (log only)
    on_violation = Column(
        String(20), nullable=False, default="flag"
    )  # see ON_VIOLATION
    require_fullscreen = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "assignment_id": self.assignment_id,
            "time_limit_minutes": self.time_limit_minutes,
            "max_violations": self.max_violations,
            "on_violation": self.on_violation,
            "require_fullscreen": self.require_fullscreen,
        }


class ExamSession(Base):
    """One student's attempt at an exam."""

    __tablename__ = "exam_sessions"
    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="uq_exam_session"),
    )

    id = Column(String(36), primary_key=True)
    assignment_id = Column(
        String(36),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    # in_progress | submitted | terminated
    status = Column(String(20), nullable=False, default="in_progress")
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    violation_count = Column(Integer, nullable=False, default=0)

    violations = relationship(
        "ExamViolation", cascade="all, delete-orphan", passive_deletes=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "student_id": self.student_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "submitted_at": (
                self.submitted_at.isoformat() if self.submitted_at else None
            ),
            "violation_count": self.violation_count,
        }


class ExamViolation(Base):
    """An append-only record of a proctoring event during an exam session."""

    __tablename__ = "exam_violations"

    id = Column(String(36), primary_key=True)
    session_id = Column(
        String(36),
        ForeignKey("exam_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    # left_page | fullscreen_exit | reload | blur
    type = Column(String(40), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "student_id": self.student_id,
            "type": self.type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
