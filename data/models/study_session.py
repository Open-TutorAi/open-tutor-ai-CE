"""Study session model — tracks Pomodoro focus sessions."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Boolean
from data.database import Base


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=False, default=25)
    session_type = Column(String(20), nullable=False, default="work")  # work | break
    completed = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
