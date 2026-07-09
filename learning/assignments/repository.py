"""Assignment repositories — data access only (SQLAlchemy, no business logic)."""

from typing import List, Optional

from sqlalchemy import func

from data.models import Assignment, Submission
from data.repositories import BaseRepository


class AssignmentRepository(BaseRepository[Assignment]):
    """Data access for assignments."""

    def list_for_classroom(self, classroom_id: str) -> List[Assignment]:
        return (
            self.session.query(Assignment)
            .filter(Assignment.classroom_id == classroom_id)
            .order_by(Assignment.created_at.desc())
            .all()
        )

    def list_for_classrooms(self, classroom_ids: List[str]) -> List[Assignment]:
        if not classroom_ids:
            return []
        return (
            self.session.query(Assignment)
            .filter(Assignment.classroom_id.in_(classroom_ids))
            .order_by(Assignment.created_at.desc())
            .all()
        )


class SubmissionRepository(BaseRepository[Submission]):
    """Data access for student submissions."""

    def get(self, assignment_id: str, student_id: str) -> Optional[Submission]:
        return (
            self.session.query(Submission)
            .filter(
                Submission.assignment_id == assignment_id,
                Submission.student_id == student_id,
            )
            .first()
        )

    def list_for_assignment(self, assignment_id: str) -> List[Submission]:
        return (
            self.session.query(Submission)
            .filter(Submission.assignment_id == assignment_id)
            .all()
        )

    def count_ungraded_for_classrooms(self, classroom_ids: List[str]) -> int:
        """Number of submissions still awaiting a grade across the given classes,
        in one query (joins assignments; no rows materialised)."""
        if not classroom_ids:
            return 0
        return (
            self.session.query(func.count(Submission.id))
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .filter(
                Assignment.classroom_id.in_(classroom_ids),
                Submission.grade.is_(None),
            )
            .scalar()
        )
