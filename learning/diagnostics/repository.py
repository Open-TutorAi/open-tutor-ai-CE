"""Diagnostic repository."""

from typing import List, Optional

from data.models import DiagnosticResult
from data.repositories import BaseRepository


class DiagnosticRepository(BaseRepository[DiagnosticResult]):
    def get_by_support(self, support_id: str) -> Optional[DiagnosticResult]:
        return (
            self.session.query(DiagnosticResult)
            .filter(DiagnosticResult.support_id == support_id)
            .order_by(DiagnosticResult.created_at.desc())
            .first()
        )

    def get_by_user(self, user_id: str) -> List[DiagnosticResult]:
        return (
            self.session.query(DiagnosticResult)
            .filter(DiagnosticResult.user_id == user_id)
            .order_by(DiagnosticResult.created_at.desc())
            .all()
        )
