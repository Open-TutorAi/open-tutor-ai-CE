"""Class session domain model."""

import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from data.database import Base


class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    classroom_id = Column(String(36), ForeignKey("classrooms.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    subject = Column(String(255), nullable=True)
    objectives = Column(Text, nullable=True)
    auto_recorded = Column(Boolean, default=False, nullable=False)
    ended_at = Column(DateTime, nullable=True)

    classroom = relationship("Classroom", back_populates="sessions")
    presences = relationship(
        "Presence", back_populates="session", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "classroom_id": self.classroom_id,
            "scheduled_at": (
                self.scheduled_at.isoformat() if self.scheduled_at else None
            ),
            "subject": self.subject,
            "objectives": self.objectives,
            "auto_recorded": self.auto_recorded,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }
