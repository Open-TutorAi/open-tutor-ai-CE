"""Classroom service."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from common.exceptions import NotFoundError, AuthorizationError
from data.models.classroom import Classroom, Enrollment
from learning.classrooms.repository import ClassroomRepository


class ClassroomsService:

    def __init__(self, session: Session):
        self.repo = ClassroomRepository(session, Classroom)

    def create(self, teacher_id: str, name: str, description: str = None, subject: str = None) -> Classroom:
        return self.repo.create(
            id=str(uuid.uuid4()),
            teacher_id=teacher_id,
            name=name,
            description=description,
            subject=subject,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def list_for_teacher(self, teacher_id: str) -> List[Classroom]:
        return self.repo.get_by_teacher(teacher_id)

    def get(self, classroom_id: str) -> Classroom:
        c = self.repo.get_by_id(classroom_id)
        if not c:
            raise NotFoundError("Classroom", classroom_id)
        return c

    def get_and_check_owner(self, classroom_id: str, teacher_id: str) -> Classroom:
        c = self.get(classroom_id)
        if c.teacher_id != teacher_id:
            raise AuthorizationError("Not your classroom")
        return c

    def enroll_student(self, classroom_id: str, student_id: str, teacher_id: str) -> Enrollment:
        self.get_and_check_owner(classroom_id, teacher_id)
        existing = self.repo.get_enrollment(classroom_id, student_id)
        if existing:
            return existing
        return self.repo.enroll(Enrollment(
            id=str(uuid.uuid4()),
            classroom_id=classroom_id,
            student_id=student_id,
            enrolled_at=datetime.utcnow(),
        ))

    def get_students(self, classroom_id: str) -> List[Enrollment]:
        return self.repo.get_students(classroom_id)

    def get_student_classrooms(self, student_id: str) -> List[Enrollment]:
        return self.repo.get_student_classrooms(student_id)
