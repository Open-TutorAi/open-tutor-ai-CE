"""Dashboard repository — aggregated queries for stats and calendar."""

from calendar import monthrange
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from data.models.study_session import StudySession
from data.models.support import Support


class DashboardRepository:
    def __init__(self, session: Session):
        self.session = session

    # ── Study sessions ────────────────────────────────────────────────────────

    def get_sessions_this_week(self, user_id: str) -> List[StudySession]:
        week_ago = datetime.utcnow() - timedelta(days=7)
        return (
            self.session.query(StudySession)
            .filter(
                StudySession.user_id == user_id,
                StudySession.session_type == "work",
                StudySession.completed.is_(True),
                StudySession.created_at >= week_ago,
            )
            .all()
        )

    def get_sessions_by_day(self, user_id: str) -> List[Dict]:
        """Hours studied per day for the last 7 days (Mon–Sun labels)."""
        labels = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        now = datetime.utcnow()
        result = []
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            sessions = (
                self.session.query(StudySession)
                .filter(
                    StudySession.user_id == user_id,
                    StudySession.session_type == "work",
                    StudySession.completed.is_(True),
                    StudySession.created_at >= start,
                    StudySession.created_at <= end,
                )
                .all()
            )
            total_minutes = sum(s.duration_minutes for s in sessions)
            result.append(
                {"day": labels[day.weekday()], "hours": round(total_minutes / 60, 1)}
            )
        return result

    def get_streak(self, user_id: str) -> int:
        """Count consecutive days with at least one completed work session."""
        streak = 0
        now = datetime.utcnow()
        for i in range(365):
            day = now - timedelta(days=i)
            start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            count = (
                self.session.query(StudySession)
                .filter(
                    StudySession.user_id == user_id,
                    StudySession.session_type == "work",
                    StudySession.completed.is_(True),
                    StudySession.created_at >= start,
                    StudySession.created_at <= end,
                )
                .count()
            )
            if count > 0:
                streak += 1
            elif i > 0:
                break
        return streak

    def get_total_sessions(self, user_id: str) -> int:
        return (
            self.session.query(StudySession)
            .filter(
                StudySession.user_id == user_id,
                StudySession.session_type == "work",
                StudySession.completed.is_(True),
            )
            .count()
        )

    # ── Supports → subject stats ──────────────────────────────────────────────

    def get_subject_stats(
        self,
        user_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict]:
        q = self.session.query(Support).filter(Support.user_id == user_id)
        if start:
            q = q.filter(Support.created_at >= start)
        if end:
            q = q.filter(Support.created_at <= end)
        supports = q.all()

        subject_map: Dict[str, Dict] = {}
        for s in supports:
            name = s.subject or s.custom_subject or "Autre"
            if name not in subject_map:
                subject_map[name] = {"count": 0, "completed": 0}
            subject_map[name]["count"] += 1
            if s.status == "completed":
                subject_map[name]["completed"] += 1

        return [
            {
                "subject": subj,
                "total_count": data["count"],
                "percentage": (
                    int((data["completed"] / data["count"]) * 100)
                    if data["count"]
                    else 0
                ),
            }
            for subj, data in subject_map.items()
        ]

    def get_performance(
        self,
        user_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Dict:
        q = self.session.query(Support).filter(Support.user_id == user_id)
        if start:
            q = q.filter(Support.created_at >= start)
        if end:
            q = q.filter(Support.created_at <= end)
        supports = q.all()

        total = len(supports)
        completed = sum(1 for s in supports if s.status == "completed")
        total_points = total * 5 + completed * 100
        return {
            "completion_rate": int((completed / total) * 100) if total else 0,
            "tutorials_completed": completed,
            "total_tutorials": total,
            "total_points": total_points,
        }

    # ── Calendar activities ───────────────────────────────────────────────────

    def get_active_days_range(
        self, user_id: str, start: datetime, end: datetime
    ) -> List[int]:
        """Returns list of offsets (0–6) from start date that have activity."""
        rows = (
            self.session.query(StudySession.created_at)
            .filter(
                StudySession.user_id == user_id,
                StudySession.created_at >= start,
                StudySession.created_at <= end,
            )
            .all()
        )
        base = start.date()
        return sorted({(r.created_at.date() - base).days for r in rows})

    def get_active_days(self, user_id: str, year: int, month: int) -> List[int]:
        _, last_day = monthrange(year, month)
        start = datetime(year, month, 1)
        end = datetime(year, month, last_day, 23, 59, 59)
        rows = (
            self.session.query(StudySession.created_at)
            .filter(
                StudySession.user_id == user_id,
                StudySession.created_at >= start,
                StudySession.created_at <= end,
            )
            .all()
        )
        return sorted({r.created_at.day for r in rows})
