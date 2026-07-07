"""Assignments router — teacher authoring/grading + student submission.

Two trees:
  • `/classrooms/{id}/assignments*` — teacher-only (require_teacher); service enforces ownership.
  • `/assignments*` — the calling student's own feed/submissions (service enforces enrolment).

Thin HTTP layer only; domain exceptions are mapped to HTTP status here.
"""

from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.models import User
from gateway.http.attachments import attachment_response
from gateway.http.dependencies import (
    Pagination,
    get_assignments_service,
    get_current_user,
    pagination,
    require_teacher,
)
from gateway.http.errors import http_from_domain as _http_from_domain
from learning.assignments.service import AssignmentsService

# Teacher-facing authoring/grading lives under the /classrooms tree.
router = APIRouter(prefix="/classrooms", tags=["assignments"])
# Student-facing feed/submission lives under its own /assignments tree.
student_router = APIRouter(prefix="/assignments", tags=["assignments"])


class AssignmentCreateRequest(BaseModel):
    # Bounds are defence-in-depth; the service still enforces non-blank semantics.
    title: str = Field(..., min_length=1, max_length=255)
    instructions: Optional[str] = Field(None, max_length=10000)
    attachment_id: Optional[str] = Field(None, max_length=64)
    due_date: Optional[str] = Field(None, max_length=40)


class GradeRequest(BaseModel):
    student_id: str = Field(..., min_length=1, max_length=64)
    grade: Optional[float] = Field(None, ge=0, le=1000)
    feedback: Optional[str] = Field(None, max_length=2000)


class SubmitRequest(BaseModel):
    content: Optional[str] = Field(None, max_length=20000)
    attachment_id: Optional[str] = Field(None, max_length=64)


def _attachment_response(result: tuple) -> Response:
    """(bytes, content_type, filename) → a forced-download Response.

    Serves `attachment` with a header-sanitised filename (see
    gateway.http.attachments) so a crafted name can't break the response header.
    """
    data, content_type, filename = result
    return attachment_response(data, content_type, filename)


# ── teacher: authoring ─────────────────────────────────────────────────────────


@router.get("/{id}/assignments")
def list_assignments(
    id: str,
    teacher: User = Depends(require_teacher),
    svc: AssignmentsService = Depends(get_assignments_service),
    page: Pagination = Depends(pagination),
):
    try:
        return page.apply(svc.list_for_class(id, teacher.id))
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@router.post("/{id}/assignments", status_code=status.HTTP_201_CREATED)
def create_assignment(
    id: str,
    data: AssignmentCreateRequest,
    teacher: User = Depends(require_teacher),
    svc: AssignmentsService = Depends(get_assignments_service),
):
    try:
        return svc.create(id, teacher.id, data.model_dump())
    except (NotFoundError, AuthorizationError, ValidationError) as exc:
        raise _http_from_domain(exc)


@router.get("/{id}/assignments/{assignment_id}")
def get_assignment(
    id: str,
    assignment_id: str,
    teacher: User = Depends(require_teacher),
    svc: AssignmentsService = Depends(get_assignments_service),
):
    try:
        return svc.get_assignment(assignment_id, teacher.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@router.delete("/{id}/assignments/{assignment_id}")
def delete_assignment(
    id: str,
    assignment_id: str,
    teacher: User = Depends(require_teacher),
    svc: AssignmentsService = Depends(get_assignments_service),
):
    try:
        svc.delete(assignment_id, teacher.id)
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
    return {"status": "deleted", "id": assignment_id}


# ── teacher: grading ───────────────────────────────────────────────────────────


@router.post("/{id}/assignments/{assignment_id}/grade")
def grade_submission(
    id: str,
    assignment_id: str,
    data: GradeRequest,
    teacher: User = Depends(require_teacher),
    svc: AssignmentsService = Depends(get_assignments_service),
):
    try:
        return svc.grade(
            assignment_id, teacher.id, data.student_id, data.grade, data.feedback
        )
    except (NotFoundError, AuthorizationError, ValidationError) as exc:
        raise _http_from_domain(exc)


@router.get(
    "/{id}/assignments/{assignment_id}/students/{student_id}/submission/attachment"
)
def download_submission_attachment(
    id: str,
    assignment_id: str,
    student_id: str,
    teacher: User = Depends(require_teacher),
    svc: AssignmentsService = Depends(get_assignments_service),
):
    """Teacher downloads a student's submission attachment (must own the class)."""
    try:
        return _attachment_response(
            svc.read_submission_attachment(assignment_id, student_id, teacher.id)
        )
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


# ── student: feed + submission ─────────────────────────────────────────────────


@student_router.get("")
def my_assignments(
    current_user: User = Depends(get_current_user),
    svc: AssignmentsService = Depends(get_assignments_service),
    page: Pagination = Depends(pagination),
):
    """Assignments across the calling student's enrolled classes, with their status."""
    return page.apply(svc.list_for_student(current_user.id))


@student_router.get("/{assignment_id}/submission")
def my_submission(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    svc: AssignmentsService = Depends(get_assignments_service),
):
    return svc.get_my_submission(assignment_id, current_user.id)


@student_router.post("/{assignment_id}/submit", status_code=status.HTTP_201_CREATED)
def submit_assignment(
    assignment_id: str,
    data: SubmitRequest,
    current_user: User = Depends(get_current_user),
    svc: AssignmentsService = Depends(get_assignments_service),
):
    try:
        return svc.submit(assignment_id, current_user.id, data.model_dump())
    except (NotFoundError, AuthorizationError, ValidationError) as exc:
        raise _http_from_domain(exc)


@student_router.get("/{assignment_id}/attachment")
def download_assignment_attachment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    svc: AssignmentsService = Depends(get_assignments_service),
):
    """The assignment's attachment, for the owning teacher or an enrolled student."""
    try:
        return _attachment_response(
            svc.read_assignment_attachment(assignment_id, current_user.id)
        )
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)


@student_router.get("/{assignment_id}/submission/attachment")
def download_my_submission_attachment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    svc: AssignmentsService = Depends(get_assignments_service),
):
    """The calling student's own submission attachment."""
    try:
        return _attachment_response(
            svc.read_submission_attachment(
                assignment_id, current_user.id, current_user.id
            )
        )
    except (NotFoundError, AuthorizationError) as exc:
        raise _http_from_domain(exc)
