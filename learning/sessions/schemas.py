"""Class session / attendance request/response schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    classroom_id: str
    scheduled_at: datetime
    subject: Optional[str] = None
    objectives: Optional[str] = None
    auto_recorded: bool
    ended_at: Optional[datetime] = None


class SessionSummaryOut(SessionOut):
    present_count: int
    absent_count: int
    late_count: int


class PresenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    student_name: str
    status: str
    recorded_at: datetime


class AttendanceStats(BaseModel):
    avg_rate: float
    sessions_count: int
    total_absences: int
    total_lates: int


class StudentHistory(BaseModel):
    student_id: str
    rate: float
    presences: int
    absences: int
    lates: int
    last_10: List[str]
