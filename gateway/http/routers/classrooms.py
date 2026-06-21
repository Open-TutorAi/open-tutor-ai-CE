"""Classroom router."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from common.exceptions import NotFoundError, AuthorizationError
from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user, get_account_service
from accounts.users.service import AccountService
from learning.classrooms.service import ClassroomsService

router = APIRouter(prefix="/classrooms", tags=["classrooms"])


def _svc(db: Session = Depends(get_db)) -> ClassroomsService:
    return ClassroomsService(db)


def _classroom_out(c) -> dict:
    return {
        "id": c.id,
        "teacher_id": c.teacher_id,
        "name": c.name,
        "description": c.description,
        "subject": c.subject,
        "is_active": c.is_active,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


class CreateClassroomRequest(BaseModel):
    name: str
    description: Optional[str] = None
    subject: Optional[str] = None


class EnrollRequest(BaseModel):
    student_id: str


@router.get("")
def list_classrooms(
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(_svc),
):
    if current_user.role in ("teacher", "admin"):
        return [_classroom_out(c) for c in svc.list_for_teacher(current_user.id)]
    # student: return classrooms they're enrolled in
    enrollments = svc.get_student_classrooms(current_user.id)
    result = []
    for e in enrollments:
        c = svc.get(e.classroom_id)
        result.append(_classroom_out(c))
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
def create_classroom(
    body: CreateClassroomRequest,
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(_svc),
):
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Teachers only")
    c = svc.create(current_user.id, body.name, body.description, body.subject)
    return _classroom_out(c)


@router.get("/{classroom_id}")
def get_classroom(
    classroom_id: str,
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(_svc),
):
    try:
        c = svc.get(classroom_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if current_user.role in ("teacher", "admin") and c.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your classroom")
    return _classroom_out(c)


@router.post("/{classroom_id}/enroll", status_code=status.HTTP_201_CREATED)
def enroll_student(
    classroom_id: str,
    body: EnrollRequest,
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(_svc),
):
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Teachers only")
    try:
        e = svc.enroll_student(classroom_id, body.student_id, current_user.id)
    except (NotFoundError, AuthorizationError) as ex:
        raise HTTPException(status_code=403, detail=str(ex))
    return {"id": e.id, "classroom_id": e.classroom_id, "student_id": e.student_id}


@router.get("/{classroom_id}/students")
def list_students(
    classroom_id: str,
    current_user: User = Depends(get_current_user),
    svc: ClassroomsService = Depends(_svc),
    account_svc: AccountService = Depends(get_account_service),
):
    try:
        svc.get_and_check_owner(classroom_id, current_user.id)
    except (NotFoundError, AuthorizationError) as ex:
        raise HTTPException(status_code=403, detail=str(ex))
    enrollments = svc.get_students(classroom_id)
    result = []
    for e in enrollments:
        user = account_svc.get_user(e.student_id)
        result.append({
            "student_id": e.student_id,
            "name": user.name if user else e.student_id,
            "email": user.email if user else None,
            "enrolled_at": e.enrolled_at.isoformat(),
        })
    return result
