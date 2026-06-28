"""Guardian repository."""

from typing import List, Optional
from sqlalchemy.orm import Session

from data.models.guardian import Guardian
from data.repositories.base import BaseRepository


class GuardianRepository(BaseRepository[Guardian]):

    def get_by_student(self, student_id: str) -> List[Guardian]:
        return (
            self.session.query(Guardian)
            .filter(Guardian.student_id == student_id)
            .order_by(Guardian.created_at.asc())
            .all()
        )

    def get_by_student_and_email(self, student_id: str, email: str) -> Optional[Guardian]:
        return (
            self.session.query(Guardian)
            .filter(Guardian.student_id == student_id, Guardian.email == email)
            .first()
        )
