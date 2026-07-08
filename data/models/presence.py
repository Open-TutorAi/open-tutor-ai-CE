"""Student session presence/attendance domain model."""

import enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship
from data.database import Base


class PresenceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"


class Presence(Base):
    __tablename__ = "presences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("class_sessions.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(Enum(PresenceStatus), nullable=False, default=PresenceStatus.ABSENT)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ClassSession", back_populates="presences")
    student = relationship("User", back_populates="presences")

    @property
    def delay_minutes(self) -> Optional[int]:
        """Minutes late, derived from the session's scheduled time. None unless LATE."""
        if self.status != PresenceStatus.LATE:
            return None
        if not self.recorded_at or not self.session or not self.session.scheduled_at:
            return None
        delta = self.recorded_at - self.session.scheduled_at
        return max(0, int(delta.total_seconds() // 60))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "student_id": self.student_id,
            "status": self.status.value if self.status else None,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "delay_minutes": self.delay_minutes,
        }
