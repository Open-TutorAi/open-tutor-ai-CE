"""Exam repositories — data access only (SQLAlchemy, no business logic)."""

from typing import List, Optional

from data.models import ExamConfig, ExamSession, ExamViolation
from data.repositories import BaseRepository


class ExamConfigRepository(BaseRepository[ExamConfig]):
    """Data access for exam configuration (1:1 with an assignment)."""

    def get_for_assignment(self, assignment_id: str) -> Optional[ExamConfig]:
        return (
            self.session.query(ExamConfig)
            .filter(ExamConfig.assignment_id == assignment_id)
            .first()
        )


class ExamSessionRepository(BaseRepository[ExamSession]):
    """Data access for per-student exam attempts."""

    def get(self, assignment_id: str, student_id: str) -> Optional[ExamSession]:
        return (
            self.session.query(ExamSession)
            .filter(
                ExamSession.assignment_id == assignment_id,
                ExamSession.student_id == student_id,
            )
            .first()
        )

    def list_for_assignment(self, assignment_id: str) -> List[ExamSession]:
        return (
            self.session.query(ExamSession)
            .filter(ExamSession.assignment_id == assignment_id)
            .all()
        )


class ExamViolationRepository(BaseRepository[ExamViolation]):
    """Data access for the append-only proctoring log."""

    def list_for_session(self, session_id: str) -> List[ExamViolation]:
        return (
            self.session.query(ExamViolation)
            .filter(ExamViolation.session_id == session_id)
            .order_by(ExamViolation.created_at.desc())
            .all()
        )
