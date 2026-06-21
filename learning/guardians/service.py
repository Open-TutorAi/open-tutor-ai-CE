"""Guardian service."""

import uuid
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from common.exceptions import NotFoundError
from data.models.guardian import Guardian
from learning.guardians.repository import GuardianRepository


class GuardiansService:

    def __init__(self, session: Session):
        self.repo = GuardianRepository(session, Guardian)

    def list_for_student(self, student_id: str) -> List[Guardian]:
        return self.repo.get_by_student(student_id)

    def invite(self, student_id: str, teacher_id: str, email: str, relationship: str) -> Guardian:
        existing = self.repo.get_by_student_and_email(student_id, email)
        if existing:
            return existing

        name = email.split("@")[0].replace(".", " ").replace("_", " ").title()
        return self.repo.create(
            id=str(uuid.uuid4()),
            student_id=student_id,
            invited_by=teacher_id,
            name=name,
            email=email,
            relationship=relationship,
            status="pending",
            linked_at=None,
            created_at=datetime.utcnow(),
        )

    def resend(self, guardian_id: str) -> Guardian:
        guardian = self.repo.get_by_id(guardian_id)
        if not guardian:
            raise NotFoundError("Guardian", guardian_id)
        return guardian

    def get(self, guardian_id: str) -> Guardian:
        guardian = self.repo.get_by_id(guardian_id)
        if not guardian:
            raise NotFoundError("Guardian", guardian_id)
        return guardian

    def activate(self, guardian_id: str) -> Guardian:
        return self.repo.update(guardian_id, status="active", linked_at=datetime.utcnow())
