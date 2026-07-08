"""Announcements business logic."""

from typing import List

from sqlalchemy.orm import Session

from common.exceptions import AuthorizationError, NotFoundError
from data.models import Announcement, Classroom
from learning.announcements.repository import AnnouncementRepository
from learning.announcements.schemas import AnnouncementOut
from learning.classrooms.repository import ClassroomRepository


def _to_announcement_out(announcement: Announcement) -> AnnouncementOut:
    return AnnouncementOut(
        id=announcement.id,
        classroom_id=announcement.classroom_id,
        author_id=announcement.author_id,
        author_name=announcement.author.name if announcement.author else None,
        content=announcement.content,
        created_at=announcement.created_at,
    )


class AnnouncementsService:

    def __init__(self, session: Session):
        self.repo = AnnouncementRepository(session, Announcement)
        self.classroom_repo = ClassroomRepository(session, Classroom)

    def _require_classroom_access(self, classroom_id: str, caller_id: str) -> Classroom:
        classroom = self.classroom_repo.get_by_id(classroom_id)
        if classroom is None:
            raise NotFoundError("Classroom", classroom_id)
        is_owner = classroom.owner_id == caller_id
        is_enrolled = self.classroom_repo.is_enrolled(classroom_id, caller_id)
        if not is_owner and not is_enrolled:
            raise AuthorizationError("not_authorized")
        return classroom

    def create_announcement(
        self, classroom_id: str, caller_id: str, content: str
    ) -> AnnouncementOut:
        classroom = self.classroom_repo.get_by_id(classroom_id)
        if classroom is None:
            raise NotFoundError("Classroom", classroom_id)
        if classroom.owner_id != caller_id:
            raise AuthorizationError("not_owner")
        announcement = self.repo.create(classroom_id, caller_id, content)
        return _to_announcement_out(announcement)

    def list_announcements(
        self, classroom_id: str, caller_id: str
    ) -> List[AnnouncementOut]:
        self._require_classroom_access(classroom_id, caller_id)
        announcements = self.repo.get_by_classroom(classroom_id)
        return [_to_announcement_out(a) for a in announcements]

    def delete_announcement(self, announcement_id: str, caller_id: str) -> None:
        announcement = self.repo.get_by_id(announcement_id)
        if announcement is None:
            raise NotFoundError("Announcement", announcement_id)
        classroom = self.classroom_repo.get_by_id(announcement.classroom_id)
        if classroom is None or classroom.owner_id != caller_id:
            raise AuthorizationError("not_owner")
        self.repo.delete(announcement_id)
