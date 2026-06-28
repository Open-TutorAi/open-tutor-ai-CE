"""Teacher availability repository."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from data.models.availability import TeacherAvailability


class TeacherRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_availability(self, teacher_id: str) -> Optional[TeacherAvailability]:
        return (
            self.session.query(TeacherAvailability)
            .filter(TeacherAvailability.teacher_id == teacher_id)
            .first()
        )

    def upsert_availability(
        self,
        teacher_id: str,
        status: str,
        office_hours_start: Optional[str],
        office_hours_end: Optional[str],
    ) -> TeacherAvailability:
        record = self.get_availability(teacher_id)
        if record:
            record.status = status
            record.office_hours_start = office_hours_start
            record.office_hours_end = office_hours_end
            record.updated_at = datetime.utcnow()
        else:
            record = TeacherAvailability(
                id=str(uuid.uuid4()),
                teacher_id=teacher_id,
                status=status,
                office_hours_start=office_hours_start,
                office_hours_end=office_hours_end,
            )
            self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record
