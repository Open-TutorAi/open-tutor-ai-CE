"""Feedback/self-regulation repository."""

from typing import List

from data.models import Feedback
from data.repositories import BaseRepository


class FeedbackRepository(BaseRepository[Feedback]):
    """Repository for feedback operations."""

    def get_by_response(self, response_id: str) -> List[Feedback]:
        return (
            self.session.query(Feedback)
            .filter(Feedback.response_id == response_id)
            .all()
        )

    def get_by_user(self, user_id: str) -> List[Feedback]:
        return self.session.query(Feedback).filter(Feedback.user_id == user_id).all()

    def get_by_type(self, feedback_type: str) -> List[Feedback]:
        return (
            self.session.query(Feedback)
            .filter(Feedback.feedback_type == feedback_type)
            .all()
        )
