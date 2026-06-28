"""Guardian router — /guardians/* routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from common.exceptions import NotFoundError
from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user
from learning.guardians.service import GuardiansService

router = APIRouter(prefix="/guardians", tags=["guardians"])


def _get_svc(db: Session = Depends(get_db)) -> GuardiansService:
    return GuardiansService(db)


def _guardian_out(g) -> dict:
    return {
        "id": g.id,
        "student_id": g.student_id,
        "name": g.name,
        "email": g.email,
        "relationship": g.relationship,
        "status": g.status,
        "linked_at": g.linked_at.isoformat() if g.linked_at else None,
    }


class InviteRequest(BaseModel):
    email: EmailStr
    relationship: str


@router.get("/student/{student_id}")
def list_guardians(
    student_id: str,
    current_user: User = Depends(get_current_user),
    svc: GuardiansService = Depends(_get_svc),
):
    return [_guardian_out(g) for g in svc.list_for_student(student_id)]


@router.post("/student/{student_id}/invite", status_code=status.HTTP_201_CREATED)
def invite_guardian(
    student_id: str,
    body: InviteRequest,
    current_user: User = Depends(get_current_user),
    svc: GuardiansService = Depends(_get_svc),
):
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teachers only")
    g = svc.invite(student_id, current_user.id, body.email, body.relationship)
    return _guardian_out(g)


@router.post("/{guardian_id}/resend")
def resend_invitation(
    guardian_id: str,
    current_user: User = Depends(get_current_user),
    svc: GuardiansService = Depends(_get_svc),
):
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teachers only")
    try:
        g = svc.resend(guardian_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"message": f"Invitation resent to {g.email}"}


@router.get("/{guardian_id}/contact")
def get_guardian_contact(
    guardian_id: str,
    current_user: User = Depends(get_current_user),
    svc: GuardiansService = Depends(_get_svc),
):
    try:
        g = svc.get(guardian_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {
        "id": g.id,
        "name": g.name,
        "email": g.email,
        "relationship": g.relationship,
    }
