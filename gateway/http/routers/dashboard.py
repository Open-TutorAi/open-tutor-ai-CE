"""Dashboard & Focus router."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user
from learning.dashboard.service import DashboardService

router = APIRouter(tags=["dashboard"])


def _svc(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


# ── Performance ────────────────────────────────────────────────────────────────


@router.get("/dashboard/statistics")
def get_statistics(
    year: int = Query(None),
    month: int = Query(None),
    start_date: str = Query(None),
    current_user: User = Depends(get_current_user),
    svc: DashboardService = Depends(_svc),
):
    return svc.get_statistics(current_user.id, year, month, start_date)


@router.get("/dashboard/performance")
def get_performance(
    period: str = Query("monthly"),
    year: int = Query(None),
    month: int = Query(None),
    start_date: str = Query(None),
    current_user: User = Depends(get_current_user),
    svc: DashboardService = Depends(_svc),
):
    return svc.get_performance(current_user.id, period, year, month, start_date)


@router.get("/dashboard/calendar")
def get_calendar(
    year: int = Query(None),
    month: int = Query(None),
    start_date: str = Query(None),
    current_user: User = Depends(get_current_user),
    svc: DashboardService = Depends(_svc),
):
    now = datetime.utcnow()
    return svc.get_calendar(
        current_user.id,
        year or now.year,
        month or now.month,
        start_date,
    )


@router.get("/dashboard/productivity")
def get_productivity(
    current_user: User = Depends(get_current_user),
    svc: DashboardService = Depends(_svc),
):
    return svc.get_productivity(current_user.id)


# ── Focus (Pomodoro) ───────────────────────────────────────────────────────────


class FocusSessionRequest(BaseModel):
    duration_minutes: int
    session_type: str = "work"


class FocusSettingsRequest(BaseModel):
    work_minutes: int
    break_minutes: int
    long_break_minutes: int = 15
    long_break_interval: int = 4


@router.post("/focus/session")
def record_focus_session(
    data: FocusSessionRequest,
    current_user: User = Depends(get_current_user),
    svc: DashboardService = Depends(_svc),
):
    sess = svc.record_session(current_user.id, data.duration_minutes, data.session_type)
    return {"id": sess.id, "status": "recorded"}


@router.get("/focus/settings")
def get_focus_settings(
    current_user: User = Depends(get_current_user),
    svc: DashboardService = Depends(_svc),
):
    s = svc.get_focus_settings(current_user.id)
    return {
        "work_minutes": s.work_minutes,
        "break_minutes": s.break_minutes,
        "long_break_minutes": s.long_break_minutes,
        "long_break_interval": s.long_break_interval,
    }


@router.put("/focus/settings")
def update_focus_settings(
    data: FocusSettingsRequest,
    current_user: User = Depends(get_current_user),
    svc: DashboardService = Depends(_svc),
):
    s = svc.update_focus_settings(current_user.id, data.model_dump())
    return {
        "work_minutes": s.work_minutes,
        "break_minutes": s.break_minutes,
        "long_break_minutes": s.long_break_minutes,
        "long_break_interval": s.long_break_interval,
    }
