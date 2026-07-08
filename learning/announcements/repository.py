"""Announcement repository."""

from typing import List, Optional

from data.models import Announcement
from data.repositories import BaseRepository


class AnnouncementRepository(BaseRepository[Announcement]):
    """Repository for classroom announcement (stream post) operations."""

    def create(self, classroom_id: str, author_id: str, content: str) -> Announcement:
        announcement = Announcement(
            classroom_id=classroom_id, author_id=author_id, content=content
        )
        self.session.add(announcement)
        self.session.commit()
        return announcement

    def get_by_classroom(self, classroom_id: str) -> List[Announcement]:
        return (
            self.session.query(Announcement)
            .filter(Announcement.classroom_id == classroom_id)
            .order_by(Announcement.created_at.desc())
            .all()
        )

    def get_by_id(self, announcement_id: str) -> Optional[Announcement]:
        return (
            self.session.query(Announcement)
            .filter(Announcement.id == announcement_id)
            .first()
        )

    def delete(self, announcement_id: str) -> None:
        announcement = self.get_by_id(announcement_id)
        if announcement is None:
            return
        self.session.delete(announcement)
        self.session.commit()
