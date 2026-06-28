"""Diagnostic test result model."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from data.database import Base


class DiagnosticResult(Base):
    __tablename__ = "diagnostic_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    support_id = Column(
        String(36),
        ForeignKey("supports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    questions = Column(JSON, nullable=True)
    answers = Column(JSON, nullable=True)
    score = Column(Integer, nullable=True)
    determined_level = Column(String(100), nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    support = relationship("Support", backref="diagnostic_results")
    user = relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "support_id": self.support_id,
            "user_id": self.user_id,
            "questions": self.questions,
            "answers": self.answers,
            "score": self.score,
            "determined_level": self.determined_level,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
