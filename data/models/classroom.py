"""Classroom domain model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from data.database import Base


class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    course = Column(String(255), nullable=True)
    objectives = Column(Text, nullable=True)
    level = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="classrooms")
    enrollments = relationship(
        "Enrollment", back_populates="classroom", cascade="all, delete-orphan"
    )
    students = relationship(
        "User",
        secondary="enrollments",
        viewonly=True,
        back_populates="enrolled_classrooms",
    )
    sessions = relationship(
        "ClassSession", back_populates="classroom", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject,
            "course": self.course,
            "objectives": self.objectives,
            "level": self.level,
            "description": self.description,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
