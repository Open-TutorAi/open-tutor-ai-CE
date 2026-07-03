"""Pomodoro focus settings — one row per user."""

from sqlalchemy import Column, String, Integer
from data.database import Base


class FocusSettings(Base):
    __tablename__ = "focus_settings"

    user_id = Column(String(36), primary_key=True)
    work_minutes = Column(Integer, nullable=False, default=25)
    break_minutes = Column(Integer, nullable=False, default=5)
    long_break_minutes = Column(Integer, nullable=False, default=15)
    long_break_interval = Column(Integer, nullable=False, default=4)
