"""Exams router — proctored exams (Epic E10).

  • Teacher config + live proctoring live under the /classrooms tree (require_teacher).
  • The student-facing exam lifecycle lives under /assignments (service enforces enrolment).

A web app cannot truly *prevent* a student leaving the page, so this is detection +
accountability: each violation is recorded, counted, and delivered live to the teacher.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.models import User
from exams.service import ExamsService
from gateway.http.dependencies import (
    get_current_user,
    get_exams_service,
    require_teacher,
)

router = APIRouter(prefix="/classrooms", tags=["exams"])
student_router = APIRouter(prefix="/assignments", tags=["exams"])


class ExamConfigRequest(BaseModel):
    time_limit_minutes: Optional[int] = Field(None, ge=1, le=1440)
    # Hard-capped at 3 (the service enforces the same cap as defence-in-depth).
    max_violations: Optional[int] = Field(None, ge=0, le=3)
    on_violation: str = Field("flag", max_length=20)  # warn | flag | auto_submit
    require_fullscreen: bool = True


class ViolationRequest(BaseModel):
    type: str = Field(..., min_length=1, max_length=64)


def _http_from_domain(exc: Exception) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, AuthorizationError):
        return HTTPException(status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, ValidationError):
        return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    raise exc


# ── teacher: configuration + proctoring ─────────────────────────────────────────


@router.post("/{id}/assignments/{assignment_id}/exam")
def configure_exam(
    id: str,
    assignment_id: str,
    data: ExamConfigRequest,
    teacher: User = Depends(require_teacher),
    svc: ExamsService = Depends(get_exams_service),
):
    """Mark an assignment as a proctored exam (or update its settings)."""
    try:
        return svc.configure_exam(assignment_id, teacher.id, data.model_dump())
    except (NotFoundError, AuthorizationError, ValidationError) as exc:
        raise _http_from_domain(exc)


@router.delete("/{id}/assignments/{assignment_id}/exam")
def unset_exam(
    id: str,
    assignment_id: str,
    teacher: User = Depends(require_teacher),
    svc: ExamsService = Depends(get_exams_service),
):
    """Turn the exam back into an ordinary assignment."""
    try:
        svc.unset_exam(assignment_id, teacher.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
    return {"status": "ok"}


@router.get("/{id}/assignments/{assignment_id}/proctoring")
def proctoring(
    id: str,
    assignment_id: str,
    teacher: User = Depends(require_teacher),
    svc: ExamsService = Depends(get_exams_service),
):
    """Live proctoring view: per-student session status + violations."""
    try:
        return svc.get_proctoring(assignment_id, teacher.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


# ── student / shared: exam lifecycle ────────────────────────────────────────────


@student_router.get("/{assignment_id}/exam")
def get_exam(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    svc: ExamsService = Depends(get_exams_service),
):
    """Is this assignment an exam? Returns config (+ the caller's session if a student)."""
    try:
        return svc.get_exam(assignment_id, current_user.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@student_router.post("/{assignment_id}/exam/start")
def start_exam(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    svc: ExamsService = Depends(get_exams_service),
):
    """Begin (or resume) the calling student's exam attempt."""
    try:
        return svc.start_session(assignment_id, current_user.id)
    except (NotFoundError, AuthorizationError, ValidationError) as exc:
        raise _http_from_domain(exc)


@student_router.post("/{assignment_id}/exam/submit")
def submit_exam(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    svc: ExamsService = Depends(get_exams_service),
):
    """Mark the calling student's exam session submitted (called with the work submit)."""
    try:
        return svc.submit_session(assignment_id, current_user.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@student_router.post("/{assignment_id}/exam/violation")
async def report_violation(
    assignment_id: str,
    data: ViolationRequest,
    current_user: User = Depends(get_current_user),
    svc: ExamsService = Depends(get_exams_service),
):
    """Record a proctoring event; notify the proctoring teacher live."""
    from gateway.realtime.socket import emit_exam_violation, is_user_online

    try:
        result = svc.report_violation(assignment_id, current_user.id, data.type)
    except (NotFoundError, AuthorizationError, ValidationError) as exc:
        raise _http_from_domain(exc)
    target = result["target"]
    if target.get("teacher_id") and is_user_online(target["teacher_id"]):
        await emit_exam_violation(target["teacher_id"], target)
    return {
        "action": result["action"],
        "grace_seconds": result["grace_seconds"],
        "session": result["session"],
    }


class TerminateRequest(BaseModel):
    reason: str = Field("timeout", max_length=255)


@student_router.post("/{assignment_id}/exam/terminate")
async def terminate_exam(
    assignment_id: str,
    data: TerminateRequest,
    current_user: User = Depends(get_current_user),
    svc: ExamsService = Depends(get_exams_service),
):
    """End the calling student's exam now (grace/time expired); notify the teacher live."""
    from gateway.realtime.socket import emit_exam_violation, is_user_online

    try:
        result = svc.terminate_session(assignment_id, current_user.id, data.reason)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
    target = result["target"]
    if target.get("teacher_id") and is_user_online(target["teacher_id"]):
        await emit_exam_violation(target["teacher_id"], target)
    return {"session": result["session"]}
