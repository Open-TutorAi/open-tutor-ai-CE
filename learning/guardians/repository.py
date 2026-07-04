"""Guardian repository — data access only."""

from typing import List, Optional

from data.models import GuardianLink
from data.repositories import BaseRepository


class GuardianRepository(BaseRepository[GuardianLink]):
    """Data access for guardian links."""

    def get_for_student(self, student_user_id: str) -> List[GuardianLink]:
        return (
            self.session.query(GuardianLink)
            .filter(GuardianLink.student_user_id == student_user_id)
            .order_by(GuardianLink.created_at.desc())
            .all()
        )

    def get_active(
        self, student_user_id: str, parent_user_id: str
    ) -> Optional[GuardianLink]:
        return (
            self.session.query(GuardianLink)
            .filter(
                GuardianLink.student_user_id == student_user_id,
                GuardianLink.parent_user_id == parent_user_id,
            )
            .first()
        )

    def get_pending_by_email(
        self, student_user_id: str, invited_email: str
    ) -> Optional[GuardianLink]:
        return (
            self.session.query(GuardianLink)
            .filter(
                GuardianLink.student_user_id == student_user_id,
                GuardianLink.invited_email == invited_email,
                GuardianLink.status == "pending",
            )
            .first()
        )

    def list_pending_by_email(self, invited_email: str) -> List[GuardianLink]:
        return (
            self.session.query(GuardianLink)
            .filter(
                GuardianLink.invited_email == invited_email,
                GuardianLink.status == "pending",
            )
            .all()
        )
