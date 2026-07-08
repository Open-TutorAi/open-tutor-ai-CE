"""Class sessions / attendance router.

Routes span three resource families (/api/classrooms/*, /api/sessions/*,
/api/presences/*) so the router declares no shared prefix; each route spells
out its full path.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.database import get_db
from data.models import PresenceStatus, User
from gateway.http.dependencies import get_current_user
from gateway.http.rate_limit import limiter, get_user_id_or_ip
from learning.attendance.service import AttendanceService
from learning.sessions.schemas import (
    AttendanceStats,
    PresenceOut,
    SessionOut,
    SessionSummaryOut,
    StudentHistory,
)

router = APIRouter(tags=["sessions"])


def get_attendance_service(db: Session = Depends(get_db)) -> AttendanceService:
    return AttendanceService(db)


class StartSessionRequest(BaseModel):
    scheduled_at: datetime
    subject: Optional[str] = Field(default=None, max_length=200)
    objectives: Optional[str] = Field(default=None, max_length=2000)


class UpdatePresenceRequest(BaseModel):
    status: PresenceStatus


@router.post(
    "/api/classrooms/{classroom_id}/sessions",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
)
async def start_session(
    classroom_id: str,
    body: StartSessionRequest,
    current_user: User = Depends(get_current_user),
    svc: AttendanceService = Depends(get_attendance_service),
):
    try:
        return svc.start_session(
            classroom_id,
            current_user.id,
            body.scheduled_at,
            body.subject,
            body.objectives,
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get(
    "/api/classrooms/{classroom_id}/sessions", response_model=List[SessionSummaryOut]
)
async def list_sessions(
    classroom_id: str,
    current_user: User = Depends(get_current_user),
    svc: AttendanceService = Depends(get_attendance_service),
):
    try:
        return svc.get_session_summaries(classroom_id, current_user.id)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post("/api/sessions/{session_id}/end", response_model=SessionOut)
async def end_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    svc: AttendanceService = Depends(get_attendance_service),
):
    try:
        return svc.end_session(session_id, current_user.id)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete("/api/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    svc: AttendanceService = Depends(get_attendance_service),
):
    try:
        svc.delete_session(session_id, current_user.id)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    return {"status": "deleted"}


@router.post("/api/sessions/{session_id}/join", response_model=PresenceOut)
@limiter.limit("20/minute", key_func=get_user_id_or_ip)
async def join_session(
    request: Request,
    session_id: str,
    current_user: User = Depends(get_current_user),
    svc: AttendanceService = Depends(get_attendance_service),
):
    try:
        return svc.join_session(session_id, current_user.id)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.get("/api/sessions/{session_id}/presences", response_model=List[PresenceOut])
async def get_session_presences(
    session_id: str,
    current_user: User = Depends(get_current_user),
    svc: AttendanceService = Depends(get_attendance_service),
):
    try:
        return svc.get_session_presences(session_id, current_user.id)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.patch("/api/presences/{presence_id}", response_model=PresenceOut)
async def update_presence(
    presence_id: str,
    body: UpdatePresenceRequest,
    current_user: User = Depends(get_current_user),
    svc: AttendanceService = Depends(get_attendance_service),
):
    try:
        return svc.update_presence(presence_id, current_user.id, body.status)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get(
    "/api/classrooms/{classroom_id}/attendance-stats", response_model=AttendanceStats
)
async def get_attendance_stats(
    classroom_id: str,
    current_user: User = Depends(get_current_user),
    svc: AttendanceService = Depends(get_attendance_service),
):
    try:
        return svc.get_attendance_stats(classroom_id, current_user.id)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get(
    "/api/classrooms/{classroom_id}/students/{student_id}/history",
    response_model=StudentHistory,
)
async def get_student_history(
    classroom_id: str,
    student_id: str,
    current_user: User = Depends(get_current_user),
    svc: AttendanceService = Depends(get_attendance_service),
):
    try:
        return svc.get_student_history(classroom_id, student_id, current_user.id)
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
