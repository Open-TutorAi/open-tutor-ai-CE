"""Classrooms router — /classrooms/* (teacher section). Thin HTTP layer only.

Every route is guarded by `require_teacher`; the service enforces ownership + validation.
Domain exceptions are mapped to HTTP status here (the repo/service never raise HTTPException).
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from classrooms.service import ClassroomsService
from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.models import User
from gateway.http.dependencies import (
    Pagination,
    get_classrooms_service,
    get_current_user,
    pagination,
    require_teacher,
)

router = APIRouter(prefix="/classrooms", tags=["classrooms"])
# Invitee-facing acceptance lives outside the /classrooms (teacher) tree.
invitations_router = APIRouter(prefix="/invitations", tags=["classrooms"])
# Cross-class teacher views (the Students directory) live at the top level.
directory_router = APIRouter(prefix="/students", tags=["classrooms"])
# Student-facing: the teachers a student may message (counterpart of the directory).
contacts_router = APIRouter(prefix="/my-teachers", tags=["classrooms"])
# Student-facing self routes (the calling user's own state, e.g. screen-lock).
me_router = APIRouter(prefix="/me", tags=["classrooms"])


class EnrolRequest(BaseModel):
    email: EmailStr = Field(..., max_length=320)


class InviteRequest(BaseModel):
    email: EmailStr = Field(..., max_length=320)
    invitee_role: str = Field("student", max_length=20)


class AcceptRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=512)


class GuardianInviteRequest(BaseModel):
    email: EmailStr = Field(..., max_length=320)


class MonitorRequest(BaseModel):
    enabled: bool


class PresenceRequest(BaseModel):
    away: bool


class ClassroomCreateRequest(BaseModel):
    # Pedagogical profile captured by the guided wizard (all required; service also
    # validates non-blank). Length bounds are defence-in-depth against oversized input.
    name: str = Field(..., min_length=1, max_length=255)
    short_description: str = Field(..., min_length=1, max_length=2000)
    subject: str = Field(..., min_length=1, max_length=255)
    custom_subject: Optional[str] = Field(None, max_length=255)
    course: str = Field(..., min_length=1, max_length=255)
    learning_objective: str = Field(..., min_length=1, max_length=2000)
    competencies: str = Field(..., min_length=1, max_length=2000)
    learning_type: str = Field(..., min_length=1, max_length=64)
    level: str = Field(..., min_length=1, max_length=64)
    content_language: str = Field(..., min_length=1, max_length=64)
    estimated_duration: str = Field(..., min_length=1, max_length=64)
    keywords: List[str] = Field(default=[], max_length=50)
    # Optional teacher settings (schedule + capacity).
    capacity: Optional[int] = Field(None, ge=1, le=100000)
    term_start: Optional[str] = Field(None, max_length=40)
    term_end: Optional[str] = Field(None, max_length=40)
    meeting_days: Optional[List[str]] = Field(None, max_length=14)


def _http_from_domain(exc: Exception) -> HTTPException:
    """Map a domain exception to the matching HTTP error."""
    if isinstance(exc, NotFoundError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, AuthorizationError):
        return HTTPException(status.HTTP_403_FORBIDDEN, detail=exc.message)
    if isinstance(exc, ValidationError):
        return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    raise exc


@router.get("")
def list_classrooms(
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
    page: Pagination = Depends(pagination),
):
    """List the calling teacher's classes (each with an active student count)."""
    return page.apply(svc.list_for_teacher(teacher.id))


@router.post("", status_code=status.HTTP_201_CREATED)
def create_classroom(
    data: ClassroomCreateRequest,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.create(teacher.id, data.model_dump())
    except ValidationError as exc:
        raise _http_from_domain(exc)


@router.get("/{id}")
def get_classroom(
    id: str,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.get(id, teacher.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@router.delete("/{id}")
def delete_classroom(
    id: str,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        svc.delete(id, teacher.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
    return {"status": "deleted", "id": id}


# ── roster: enrolment ────────────────────────────────────────────────────────


@router.get("/{id}/students")
def list_roster(
    id: str,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
    page: Pagination = Depends(pagination),
):
    try:
        return page.apply(svc.list_roster(id, teacher.id))
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@router.post("/{id}/students", status_code=status.HTTP_201_CREATED)
def enrol_student(
    id: str,
    data: EnrolRequest,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.enrol(id, teacher.id, data.email)
    except AuthorizationError as exc:
        raise _http_from_domain(exc)
    except NotFoundError as exc:
        # No account for this email → caller (UI) offers the invitation flow.
        raise _http_from_domain(exc)
    except ValidationError as exc:
        # Only validation case here is a duplicate enrolment.
        raise HTTPException(status.HTTP_409_CONFLICT, detail=exc.message)


@router.delete("/{id}/students/{student_id}")
def remove_student(
    id: str,
    student_id: str,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        svc.remove_student(id, teacher.id, student_id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
    return {"status": "removed", "student_id": student_id}


# ── roster: invitations ──────────────────────────────────────────────────────


@router.get("/{id}/invitations")
def list_invitations(
    id: str,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.list_invitations(id, teacher.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@router.post("/{id}/invitations", status_code=status.HTTP_201_CREATED)
def create_invitation(
    id: str,
    data: InviteRequest,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.invite(id, teacher.id, data.email, data.invitee_role)
    except (NotFoundError, AuthorizationError, ValidationError) as exc:
        raise _http_from_domain(exc)


# ── guardians (parent link & contact) ────────────────────────────────────────


@router.get("/{id}/students/{student_id}/guardians")
def list_guardians(
    id: str,
    student_id: str,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.list_guardians(id, teacher.id, student_id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@router.post(
    "/{id}/students/{student_id}/guardians", status_code=status.HTTP_201_CREATED
)
def invite_guardian(
    id: str,
    student_id: str,
    data: GuardianInviteRequest,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.invite_guardian(id, teacher.id, student_id, data.email)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
    except ValidationError as exc:
        # Only validation case here is a duplicate link/invite.
        raise HTTPException(status.HTTP_409_CONFLICT, detail=exc.message)


# ── classroom control: student monitors (E6, realtime) ───────────────────────


@router.get("/{id}/students/{student_id}/monitor")
def get_monitor(
    id: str,
    student_id: str,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.get_monitor_state(id, teacher.id, student_id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@router.get("/{id}/monitor/away-log")
def monitor_away_log(
    id: str,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
    page: Pagination = Depends(pagination),
):
    """Recent tab-away history for the class (newest first) — durable telemetry the
    teacher can review even if they weren't watching the Control tab live."""
    try:
        return page.apply(svc.list_away_log(id, teacher.id))
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@router.delete("/{id}/monitor/away-log")
def clear_monitor_away_log(
    id: str,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    """Clear the class's tab-away history."""
    try:
        removed = svc.clear_away_log(id, teacher.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
    return {"status": "cleared", "removed": removed}


@router.post("/{id}/students/{student_id}/monitor")
async def set_monitor(
    id: str,
    student_id: str,
    data: MonitorRequest,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    """Toggle one student's monitor. Persists the desired state, then delivers it live
    if the student is online (offline → persisted only; client reads it on reconnect).
    """
    from gateway.realtime.socket import emit_monitor_set, is_user_online

    try:
        result = svc.set_monitor(id, teacher.id, student_id, data.enabled)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
    online = is_user_online(student_id)
    if online:
        await emit_monitor_set(student_id, data.enabled)
    return {**result, "state": "on" if data.enabled else "off", "delivered": online}


@router.post("/{id}/monitor")
async def set_class_monitor(
    id: str,
    data: MonitorRequest,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    """Class-level toggle: switch every enrolled student together; report how many were
    reached live."""
    from gateway.realtime.socket import emit_monitor_set, is_user_online

    try:
        targets = svc.set_class_monitor(id, teacher.id, data.enabled)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
    reached = 0
    for t in targets:
        if is_user_online(t["student_id"]):
            await emit_monitor_set(t["student_id"], data.enabled)
            reached += 1
    return {
        "state": "on" if data.enabled else "off",
        "enabled": data.enabled,
        "reached": reached,
        "total": len(targets),
    }


@router.get("/{id}/presence")
def class_presence(
    id: str,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    """Per-student online/offline presence for the class roster (E6 control).

    Powers the "X/Y online now" indicator and its student dropdown; online status is
    read live from the socket session pool, so it reflects the current moment. Returns
    ids only (no per-student DB lookup) — the client already holds names from the loaded
    roster, which keeps this endpoint cheap enough to poll on a short interval.
    """
    from gateway.realtime.socket import is_user_online

    try:
        student_ids = svc.list_roster_ids(id, teacher.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
    students = [
        {"student_id": sid, "online": is_user_online(sid)} for sid in student_ids
    ]
    online = sum(1 for s in students if s["online"])
    return {"students": students, "online": online, "total": len(students)}


# ── progress monitoring (read-only) ──────────────────────────────────────────


@router.get("/{id}/progress")
def class_progress(
    id: str,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.get_class_progress(id, teacher.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@router.get("/{id}/students/{student_id}/progress")
def student_progress(
    id: str,
    student_id: str,
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    try:
        return svc.get_student_progress(id, teacher.id, student_id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@directory_router.get("")
def students_directory(
    teacher: User = Depends(require_teacher),
    svc: ClassroomsService = Depends(get_classrooms_service),
    page: Pagination = Depends(pagination),
):
    """Deduplicated roster across all the teacher's classes (read-only)."""
    return page.apply(svc.list_all_students(teacher.id))


@contacts_router.get("")
def my_teachers(
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    """The teachers the calling student may message (across their enrolled classes)."""
    return svc.list_my_teachers(current_user.id)


@me_router.get("/monitor")
def my_monitor(
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    """The calling user's own screen-lock state (E6), aggregated across their classes.

    The client reads this on (re)connect to re-apply a lock that was set while it was
    offline — the durable counterpart of the live `monitor:set` event.
    """
    return svc.get_my_monitor_state(current_user.id)


@me_router.post("/monitor/presence")
async def my_monitor_presence(
    data: PresenceRequest,
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    """Tab-away telemetry: the calling student reports leaving/returning to the screen
    while locked. We notify only the teacher(s) currently locking them, live.
    """
    from gateway.realtime.socket import emit_monitor_student_away

    targets = svc.report_presence(current_user.id, data.away)
    for t in targets:
        await emit_monitor_student_away(t["teacher_id"], t)
    return {"away": data.away, "notified": len(targets)}


@invitations_router.post("/accept")
def accept_invitation(
    data: AcceptRequest,
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(get_classrooms_service),
):
    """Invitee-facing: accept an invitation by token (any authenticated user)."""
    try:
        return svc.accept_invitation(data.token, current_user.id, current_user.email)
    except NotFoundError as exc:
        raise _http_from_domain(exc)
    except ValidationError as exc:
        # expired / already used → Gone
        raise HTTPException(status.HTTP_410_GONE, detail=exc.message)
