"""Assignment router."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from common.exceptions import NotFoundError, AuthorizationError
from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user
from learning.assignments.service import AssignmentsService

router = APIRouter(prefix="/assignments", tags=["assignments"])


def _svc(db: Session = Depends(get_db)) -> AssignmentsService:
    return AssignmentsService(db)


def _assignment_out(a) -> dict:
    return {
        "id": a.id,
        "classroom_id": a.classroom_id,
        "teacher_id": a.teacher_id,
        "title": a.title,
        "instructions": a.instructions,
        "attachment_url": a.attachment_url,
        "due_date": a.due_date.isoformat() if a.due_date else None,
        "max_score": a.max_score,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


def _submission_out(s) -> dict:
    return {
        "id": s.id,
        "assignment_id": s.assignment_id,
        "student_id": s.student_id,
        "content": s.content,
        "attachment_url": s.attachment_url,
        "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        "score": s.score,
        "feedback": s.feedback,
        "graded_at": s.graded_at.isoformat() if s.graded_at else None,
        "status": s.status,
    }


class CreateAssignmentRequest(BaseModel):
    classroom_id: str
    title: str
    instructions: Optional[str] = None
    due_date: datetime
    attachment_url: Optional[str] = None
    max_score: int = 20


class SubmitRequest(BaseModel):
    content: Optional[str] = None
    attachment_url: Optional[str] = None


class GradeRequest(BaseModel):
    score: int
    feedback: Optional[str] = None


# ── Teacher endpoints ─────────────────────────────────────────────────────────

@router.get("")
def list_assignments(
    current_user: User = Depends(get_current_user),
    svc: AssignmentsService = Depends(_svc),
):
    if current_user.role in ("teacher", "admin"):
        return [_assignment_out(a) for a in svc.list_for_teacher(current_user.id)]
    return [_assignment_out(a) for a in svc.list_for_student(current_user.id)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_assignment(
    body: CreateAssignmentRequest,
    current_user: User = Depends(get_current_user),
    svc: AssignmentsService = Depends(_svc),
):
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Teachers only")
    try:
        a = svc.create(
            teacher_id=current_user.id,
            classroom_id=body.classroom_id,
            title=body.title,
            instructions=body.instructions,
            due_date=body.due_date,
            attachment_url=body.attachment_url,
            max_score=body.max_score,
        )
    except (NotFoundError, AuthorizationError) as ex:
        raise HTTPException(status_code=403, detail=str(ex))
    return _assignment_out(a)


@router.get("/{assignment_id}")
def get_assignment(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    svc: AssignmentsService = Depends(_svc),
):
    try:
        a = svc.get(assignment_id)
    except NotFoundError as ex:
        raise HTTPException(status_code=404, detail=str(ex))
    return _assignment_out(a)


@router.get("/{assignment_id}/submissions")
def list_submissions(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    svc: AssignmentsService = Depends(_svc),
):
    try:
        subs = svc.get_submissions(assignment_id, current_user.id)
    except (NotFoundError, AuthorizationError) as ex:
        raise HTTPException(status_code=403, detail=str(ex))
    return [_submission_out(s) for s in subs]


@router.post("/{assignment_id}/submissions/{submission_id}/grade")
def grade_submission(
    assignment_id: str,
    submission_id: str,
    body: GradeRequest,
    current_user: User = Depends(get_current_user),
    svc: AssignmentsService = Depends(_svc),
):
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Teachers only")
    try:
        sub = svc.grade(assignment_id, submission_id, current_user.id, body.score, body.feedback)
    except (NotFoundError, AuthorizationError) as ex:
        raise HTTPException(status_code=403, detail=str(ex))
    return _submission_out(sub)


@router.get("/{assignment_id}/status")
def get_status_tracker(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    svc: AssignmentsService = Depends(_svc),
):
    try:
        tracker = svc.get_status_tracker(assignment_id, current_user.id)
    except (NotFoundError, AuthorizationError) as ex:
        raise HTTPException(status_code=403, detail=str(ex))
    return [
        {
            "student_id": row["student_id"],
            "status": row["status"],
            "submission": _submission_out(row["submission"]) if row["submission"] else None,
        }
        for row in tracker
    ]


# ── Student endpoints ─────────────────────────────────────────────────────────

@router.post("/{assignment_id}/submit", status_code=status.HTTP_201_CREATED)
def submit_assignment(
    assignment_id: str,
    body: SubmitRequest,
    current_user: User = Depends(get_current_user),
    svc: AssignmentsService = Depends(_svc),
):
    try:
        sub = svc.submit(assignment_id, current_user.id, body.content, body.attachment_url)
    except (NotFoundError, AuthorizationError) as ex:
        raise HTTPException(status_code=403, detail=str(ex))
    return _submission_out(sub)


@router.get("/{assignment_id}/my-submission")
def get_my_submission(
    assignment_id: str,
    current_user: User = Depends(get_current_user),
    svc: AssignmentsService = Depends(_svc),
):
    sub = svc.get_student_submission(assignment_id, current_user.id)
    if not sub:
        return None
    return _submission_out(sub)
