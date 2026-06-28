"""Teachers router — /teachers/* for teacher availability."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from common.exceptions import AuthorizationError, ValidationError
from data.models import User
from gateway.http.dependencies import get_current_user, get_teachers_service
from learning.teachers.service import TeachersService

router = APIRouter(prefix="/teachers", tags=["teachers"])


class UpdateAvailabilityRequest(BaseModel):
    status: str
    office_hours_start: Optional[str] = None
    office_hours_end: Optional[str] = None


@router.get("/availability/{teacher_id}")
async def get_teacher_availability(
    teacher_id: str,
    current_user: User = Depends(get_current_user),
    svc: TeachersService = Depends(get_teachers_service),
) -> Dict[str, Any]:
    return svc.get_availability(teacher_id)


@router.put("/availability")
async def update_availability(
    body: UpdateAvailabilityRequest,
    current_user: User = Depends(get_current_user),
    svc: TeachersService = Depends(get_teachers_service),
) -> Dict[str, Any]:
    try:
        return svc.update_availability(
            current_user,
            body.status,
            body.office_hours_start,
            body.office_hours_end,
        )
    except (AuthorizationError, ValidationError) as exc:
        code = (
            status.HTTP_403_FORBIDDEN
            if isinstance(exc, AuthorizationError)
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=exc.message)
