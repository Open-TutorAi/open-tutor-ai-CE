"""Classroom invitation model."""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from data.database import Base


class Invite(Base):
    __tablename__ = "invites"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(64), nullable=False, unique=True)
    classroom_id = Column(String(36), ForeignKey("classrooms.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    max_uses = Column(Integer, nullable=True)
    uses = Column(Integer, default=0, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)

    classroom = relationship("Classroom")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "classroom_id": self.classroom_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "max_uses": self.max_uses,
            "uses": self.uses,
            "is_primary": self.is_primary,
        }
