"""Dashboard service — business logic for performance & productivity stats."""

import uuid
from calendar import monthrange
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from data.models.focus_settings import FocusSettings
from data.models.study_session import StudySession
from .repository import DashboardRepository

_DEFAULT_SUBJECTS = [
    {"subject": "Mathématiques", "percentage": 0, "total_count": 0},
    {"subject": "Physique", "percentage": 0, "total_count": 0},
    {"subject": "Algorithmique", "percentage": 0, "total_count": 0},
    {"subject": "Chimie", "percentage": 0, "total_count": 0},
]


def _date_range(
    year: Optional[int],
    month: Optional[int],
    start_date: Optional[str],
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Compute (start, end) datetimes from month params or a weekly start_date."""
    if start_date:
        start = datetime.fromisoformat(start_date)
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        return start, end
    if year and month:
        _, last = monthrange(year, month)
        return datetime(year, month, 1), datetime(year, month, last, 23, 59, 59)
    return None, None


class DashboardService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = DashboardRepository(session)

    # ── Performance ───────────────────────────────────────────────────────────

    def get_statistics(
        self,
        user_id: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        start_date: Optional[str] = None,
    ) -> List[Dict]:
        start, end = _date_range(year, month, start_date)
        stats = self.repo.get_subject_stats(user_id, start, end)
        return stats if stats else _DEFAULT_SUBJECTS

    def get_performance(
        self,
        user_id: str,
        period: str = "monthly",
        year: Optional[int] = None,
        month: Optional[int] = None,
        start_date: Optional[str] = None,
    ) -> Dict:
        start, end = _date_range(year, month, start_date)
        return self.repo.get_performance(user_id, start, end)

    def get_calendar(
        self,
        user_id: str,
        year: int,
        month: int,
        start_date: Optional[str] = None,
    ) -> Dict:
        if start_date:
            start = datetime.fromisoformat(start_date)
            end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
            active_offsets = self.repo.get_active_days_range(user_id, start, end)
            return {
                "year": year,
                "month": month,
                "week_start": start_date,
                "active_days": active_offsets,
            }
        active_days = self.repo.get_active_days(user_id, year, month)
        return {"year": year, "month": month, "active_days": active_days}

    # ── Productivity ──────────────────────────────────────────────────────────

    def get_productivity(self, user_id: str) -> Dict:
        week_sessions = self.repo.get_sessions_this_week(user_id)
        weekly_hours = sum(s.duration_minutes for s in week_sessions) / 60
        return {
            "streak": self.repo.get_streak(user_id),
            "total_sessions": self.repo.get_total_sessions(user_id),
            "weekly_hours": round(weekly_hours, 1),
            "daily_hours": self.repo.get_sessions_by_day(user_id),
        }

    # ── Focus sessions ────────────────────────────────────────────────────────

    def record_session(
        self, user_id: str, duration_minutes: int, session_type: str = "work"
    ) -> StudySession:
        session = StudySession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            duration_minutes=duration_minutes,
            session_type=session_type,
            completed=True,
        )
        self.session.add(session)
        self.session.commit()
        self.session.refresh(session)
        return session

    def get_focus_settings(self, user_id: str) -> FocusSettings:
        settings = (
            self.session.query(FocusSettings)
            .filter(FocusSettings.user_id == user_id)
            .first()
        )
        if not settings:
            settings = FocusSettings(user_id=user_id)
            self.session.add(settings)
            self.session.commit()
            self.session.refresh(settings)
        return settings

    def update_focus_settings(self, user_id: str, data: Dict) -> FocusSettings:
        settings = (
            self.session.query(FocusSettings)
            .filter(FocusSettings.user_id == user_id)
            .first()
        )
        if not settings:
            settings = FocusSettings(user_id=user_id, **data)
            self.session.add(settings)
        else:
            for key, val in data.items():
                setattr(settings, key, val)
        self.session.commit()
        self.session.refresh(settings)
        return settings
