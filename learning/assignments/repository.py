"""Assignment repository."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from data.models.assignment import Assignment, Submission
from data.repositories.base import BaseRepository


class AssignmentRepository(BaseRepository[Assignment]):

    def get_by_classroom(self, classroom_id: str) -> List[Assignment]:
        return (
            self.session.query(Assignment)
            .filter(Assignment.classroom_id == classroom_id)
            .order_by(Assignment.due_date.asc())
            .all()
        )

    def get_by_teacher(self, teacher_id: str) -> List[Assignment]:
        return (
            self.session.query(Assignment)
            .filter(Assignment.teacher_id == teacher_id)
            .order_by(Assignment.due_date.asc())
            .all()
        )

    def get_by_classrooms(self, classroom_ids: List[str]) -> List[Assignment]:
        if not classroom_ids:
            return []
        return (
            self.session.query(Assignment)
            .filter(Assignment.classroom_id.in_(classroom_ids))
            .order_by(Assignment.due_date.asc())
            .all()
        )


class SubmissionRepository(BaseRepository[Submission]):

    def get_by_assignment(self, assignment_id: str) -> List[Submission]:
        return (
            self.session.query(Submission)
            .filter(Submission.assignment_id == assignment_id)
            .all()
        )

    def get_by_student_and_assignment(self, student_id: str, assignment_id: str) -> Optional[Submission]:
        return (
            self.session.query(Submission)
            .filter(Submission.student_id == student_id, Submission.assignment_id == assignment_id)
            .first()
        )

    def get_by_student(self, student_id: str) -> List[Submission]:
        return (
            self.session.query(Submission)
            .filter(Submission.student_id == student_id)
            .all()
        )
