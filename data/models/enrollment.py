"""Classroom enrollment association model."""

import uuid
from datetime import date
from sqlalchemy import Column, Date, ForeignKey, String
from sqlalchemy.orm import relationship
from data.database import Base


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    classroom_id = Column(String(36), ForeignKey("classrooms.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    enrolled_at = Column(Date, default=date.today, nullable=False)

    classroom = relationship("Classroom", back_populates="enrollments")
    student = relationship("User", back_populates="enrollments")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "classroom_id": self.classroom_id,
            "student_id": self.student_id,
            "enrolled_at": self.enrolled_at.isoformat() if self.enrolled_at else None,
        }
