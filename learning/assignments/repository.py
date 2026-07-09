"""Assignment and submission repositories."""

import os
from typing import List, Optional

from data.models import Assignment, Submission
from data.repositories import BaseRepository


class AssignmentRepository(BaseRepository[Assignment]):
    """Repository for assignment operations."""

    def get_by_user(self, user_id: str) -> List[Assignment]:
        return (
            self.session.query(Assignment)
            .filter(Assignment.user_id == user_id)
            .order_by(Assignment.created_at.desc())
            .all()
        )


class SubmissionRepository(BaseRepository[Submission]):
    """Repository for submission operations."""

    def get_by_assignment(self, assignment_id: str) -> List[Submission]:
        return (
            self.session.query(Submission)
            .filter(Submission.assignment_id == assignment_id)
            .order_by(Submission.created_at.desc())
            .all()
        )

    def get_by_assignment_and_user(
        self, assignment_id: str, user_id: str
    ) -> Optional[Submission]:
        return (
            self.session.query(Submission)
            .filter(
                Submission.assignment_id == assignment_id,
                Submission.user_id == user_id,
            )
            .first()
        )

    def delete_by_assignment(self, assignment_id: str) -> None:
        submissions = self.get_by_assignment(assignment_id)
        for submission in submissions:
            try:
                if os.path.exists(submission.file_path):
                    os.remove(submission.file_path)
            except OSError:
                pass
        self.session.query(Submission).filter(
            Submission.assignment_id == assignment_id
        ).delete()
