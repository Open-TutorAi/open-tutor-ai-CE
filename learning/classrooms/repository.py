"""Classroom repository."""

from typing import List, Optional
from sqlalchemy.orm import Session

from data.models.classroom import Classroom, Enrollment
from data.repositories.base import BaseRepository


class ClassroomRepository(BaseRepository[Classroom]):

    def get_by_teacher(self, teacher_id: str) -> List[Classroom]:
        return (
            self.session.query(Classroom)
            .filter(Classroom.teacher_id == teacher_id, Classroom.is_active == True)
            .order_by(Classroom.created_at.desc())
            .all()
        )

    def get_enrollment(self, classroom_id: str, student_id: str) -> Optional[Enrollment]:
        return (
            self.session.query(Enrollment)
            .filter(Enrollment.classroom_id == classroom_id, Enrollment.student_id == student_id)
            .first()
        )

    def get_students(self, classroom_id: str) -> List[Enrollment]:
        return (
            self.session.query(Enrollment)
            .filter(Enrollment.classroom_id == classroom_id)
            .all()
        )

    def get_student_classrooms(self, student_id: str) -> List[Enrollment]:
        return (
            self.session.query(Enrollment)
            .filter(Enrollment.student_id == student_id)
            .all()
        )

    def enroll(self, enrollment: Enrollment) -> Enrollment:
        self.session.add(enrollment)
        self.session.commit()
        self.session.refresh(enrollment)
        return enrollment
