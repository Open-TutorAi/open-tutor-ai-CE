"""Monitor-state model — the persisted *desired* state of a student's screen lock.

Part of E6 (classroom control). This is **device/session** state, not learning data, so
it sits outside the E3 read-only guarantee. The realtime `monitor:set` event is the
*delivery*; this row is the *truth* the client re-reads on (re)connect. `enabled=True`
means the screen is normal; `enabled=False` means blanked/locked.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)

from data.database import Base


class MonitorState(Base):
    __tablename__ = "monitor_states"
    __table_args__ = (
        UniqueConstraint(
            "classroom_id", "student_id", name="uq_monitor_classroom_student"
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
    enabled = Column(Boolean, nullable=False, default=True)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "classroom_id": self.classroom_id,
            "student_id": self.student_id,
            "enabled": self.enabled,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MonitorAwayEvent(Base):
    """An append-only record of a locked student leaving (`away=True`) or returning
    (`away=False`) to their screen — the durable history behind the live
    `monitor:student-away` event, so a teacher sees what happened while not watching.
    """

    __tablename__ = "monitor_away_events"

    id = Column(String(36), primary_key=True)
    classroom_id = Column(
        String(36),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    away = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "classroom_id": self.classroom_id,
            "student_id": self.student_id,
            "away": self.away,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
