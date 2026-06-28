"""Teacher availability model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String

from data.database import Base


class TeacherAvailability(Base):
    """Availability status and office hours for a teacher."""

    __tablename__ = "teacher_availability"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    # available | busy | offline
    status = Column(String(20), nullable=False, default="available")
    office_hours_start = Column(String(5), nullable=True)  # "08:30"
    office_hours_end = Column(String(5), nullable=True)  # "16:30"
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
