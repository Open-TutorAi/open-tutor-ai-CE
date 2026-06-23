"""Repository for ErrorCard CRUD operations."""
from typing import List, Optional
from sqlalchemy.orm import Session

from data.models.error_card import ErrorCard
from data.repositories.base import BaseRepository


class ErrorCardRepository(BaseRepository[ErrorCard]):
    """Repository for error cards generated from student/tutor exchanges."""

    def __init__(self, session: Session):
        super().__init__(session, ErrorCard)

    def list_by_support(self, support_id: str, user_id: str) -> List[ErrorCard]:
        """List all error cards for a given support, scoped to the owning user."""
        return (
            self.session.query(ErrorCard)
            .filter(
                ErrorCard.support_id == support_id,
                ErrorCard.user_id == user_id,
            )
            .order_by(ErrorCard.created_at.desc())
            .all()
        )

    def get_for_user(self, card_id: str, user_id: str) -> Optional[ErrorCard]:
        """Get a card by id, but only if it belongs to the given user."""
        return (
            self.session.query(ErrorCard)
            .filter(ErrorCard.id == card_id, ErrorCard.user_id == user_id)
            .first()
        )

    def delete_for_user(self, card_id: str, user_id: str) -> bool:
        """Delete a card only if it belongs to the given user. Returns True if deleted."""
        card = self.get_for_user(card_id, user_id)
        if not card:
            return False
        self.session.delete(card)
        self.session.commit()
        return True

    def count_by_support(self, support_id: str, user_id: str) -> int:
        """Count cards for a support (useful for stats)."""
        return (
            self.session.query(ErrorCard)
            .filter(
                ErrorCard.support_id == support_id,
                ErrorCard.user_id == user_id,
            )
            .count()
        )
