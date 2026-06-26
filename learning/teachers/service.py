"""Teacher availability service."""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from common.exceptions import AuthorizationError, NotFoundError
from data.models import User
from learning.teachers.repository import TeacherRepository

VALID_STATUSES = {"available", "busy", "offline"}


class TeachersService:
    def __init__(self, session: Session):
        self.repo = TeacherRepository(session)

    def get_availability(self, teacher_id: str) -> Dict[str, Any]:
        record = self.repo.get_availability(teacher_id)
        if not record:
            return _default_availability(teacher_id)
        return _avail_dict(record)

    def update_availability(
        self,
        current_user: User,
        status: str,
        office_hours_start: Optional[str],
        office_hours_end: Optional[str],
    ) -> Dict[str, Any]:
        if current_user.role != "teacher":
            raise AuthorizationError("Only teachers can update availability")
        if status not in VALID_STATUSES:
            from common.exceptions import ValidationError
            raise ValidationError(
                f"status must be one of: {', '.join(sorted(VALID_STATUSES))}"
            )
        record = self.repo.upsert_availability(
            current_user.id, status, office_hours_start, office_hours_end
        )
        return _avail_dict(record)


def _avail_dict(record) -> Dict[str, Any]:
    return {
        "teacher_id": record.teacher_id,
        "status": record.status,
        "office_hours_start": record.office_hours_start,
        "office_hours_end": record.office_hours_end,
        "updated_at": record.updated_at.isoformat(),
    }


def _default_availability(teacher_id: str) -> Dict[str, Any]:
    return {
        "teacher_id": teacher_id,
        "status": "available",
        "office_hours_start": None,
        "office_hours_end": None,
        "updated_at": None,
    }
