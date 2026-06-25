"""Classroom domain models — classes (with pedagogical profile), roster, invitations.

Part of the `classrooms` bounded context. `Classroom` mirrors the existing `Support`
pedagogical fields (+ competencies), captured via the guided create wizard (E1-S1).
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from data.database import Base


class Classroom(Base):
    """A class owned by a teacher. Aggregate root of the classrooms context."""

    __tablename__ = "classrooms"

    id = Column(String(36), primary_key=True)
    teacher_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Pedagogical profile (mirrors Support; all required via the wizard / service).
    name = Column(String(255), nullable=False)
    short_description = Column(Text, nullable=True)
    subject = Column(String(255), nullable=True)
    custom_subject = Column(String(255), nullable=True)
    course = Column(String(255), nullable=True)  # programme reference
    learning_objective = Column(Text, nullable=True)  # objectifs
    competencies = Column(Text, nullable=True)  # compétences visées
    learning_type = Column(String(100), nullable=True)  # approach
    level = Column(String(100), nullable=True)  # niveau
    content_language = Column(String(100), nullable=True, default="English")
    estimated_duration = Column(String(100), nullable=True)  # volume horaire
    keywords = Column(Text, nullable=True)  # comma-separated

    # Teacher-specific class settings (optional; collected by the create wizard).
    capacity = Column(Integer, nullable=True)  # max students, None = unlimited
    term_start = Column(DateTime, nullable=True)  # class start date
    term_end = Column(DateTime, nullable=True)  # class end date
    meeting_days = Column(
        Text, nullable=True
    )  # comma-separated weekdays e.g. "Mon,Wed"

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    enrollments = relationship(
        "Enrollment", back_populates="classroom", cascade="all, delete-orphan"
    )
    invitations = relationship(
        "Invitation", back_populates="classroom", cascade="all, delete-orphan"
    )
    # Deleting a class purges its class-scoped data (submissions cascade via Assignment).
    # SQLite FK enforcement is off, so cascade is handled at the ORM level here.
    assignments = relationship(
        "Assignment", cascade="all, delete-orphan", passive_deletes=False
    )
    resources = relationship(
        "ClassResource", cascade="all, delete-orphan", passive_deletes=False
    )
    monitor_states = relationship(
        "MonitorState", cascade="all, delete-orphan", passive_deletes=False
    )
    away_events = relationship(
        "MonitorAwayEvent", cascade="all, delete-orphan", passive_deletes=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "name": self.name,
            "short_description": self.short_description,
            "subject": self.subject,
            "custom_subject": self.custom_subject,
            "course": self.course,
            "learning_objective": self.learning_objective,
            "competencies": self.competencies,
            "learning_type": self.learning_type,
            "level": self.level,
            "content_language": self.content_language,
            "estimated_duration": self.estimated_duration,
            "keywords": self.keywords.split(",") if self.keywords else None,
            "capacity": self.capacity,
            "term_start": self.term_start.isoformat() if self.term_start else None,
            "term_end": self.term_end.isoformat() if self.term_end else None,
            "meeting_days": self.meeting_days.split(",") if self.meeting_days else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Enrollment(Base):
    """Roster membership: a student enrolled in a classroom."""

    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint(
            "classroom_id", "student_id", name="uq_enrollment_classroom_student"
        ),
    )

    id = Column(String(36), primary_key=True)
    classroom_id = Column(
        String(36),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="active")
    enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    classroom = relationship("Classroom", back_populates="enrollments")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "classroom_id": self.classroom_id,
            "student_id": self.student_id,
            "status": self.status,
            "enrolled_at": self.enrolled_at.isoformat() if self.enrolled_at else None,
        }


class Invitation(Base):
    """An invitation to join a classroom (as student or parent), keyed by a token."""

    __tablename__ = "invitations"

    id = Column(String(36), primary_key=True)
    classroom_id = Column(
        String(36),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email = Column(String(255), nullable=False, index=True)
    invitee_role = Column(String(50), nullable=False, default="student")
    token = Column(String(64), nullable=False, unique=True, index=True)
    status = Column(String(50), nullable=False, default="pending")
    invited_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    accepted_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    classroom = relationship("Classroom", back_populates="invitations")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "classroom_id": self.classroom_id,
            "email": self.email,
            "invitee_role": self.invitee_role,
            "token": self.token,
            "status": self.status,
            "invited_by": self.invited_by,
            "accepted_user_id": self.accepted_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
