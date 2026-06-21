"""Guardian domain model."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from data.database import Base


class Guardian(Base):
    __tablename__ = "guardians"

    id = Column(String(36), primary_key=True)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    invited_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    relationship = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    linked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
