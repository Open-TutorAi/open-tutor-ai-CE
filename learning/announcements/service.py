"""Announcements service."""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from common.exceptions import AuthorizationError, NotFoundError
from data.models import User
from learning.announcements.repository import AnnouncementRepository

VALID_PRIORITIES = {"normal", "important", "urgent"}
VALID_TARGET_TYPES = {"all", "class", "selected"}


class AnnouncementsService:
    def __init__(self, session: Session):
        self.repo = AnnouncementRepository(session)

    # ── Teacher operations ────────────────────────────────────────────────────

    def create(
        self,
        current_user: User,
        title: str,
        content: str,
        priority: str = "normal",
        target_type: str = "all",
    ) -> Dict[str, Any]:
        if current_user.role != "teacher":
            raise AuthorizationError("Only teachers can create announcements")
        if priority not in VALID_PRIORITIES:
            from common.exceptions import ValidationError
            raise ValidationError(
                f"priority must be one of: {', '.join(sorted(VALID_PRIORITIES))}"
            )
        ann = self.repo.create(
            teacher_id=current_user.id,
            title=title,
            content=content,
            priority=priority,
            target_type=target_type,
        )
        return _ann_dict(ann, is_read=False)

    def update(
        self,
        current_user: User,
        announcement_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        priority: Optional[str] = None,
        target_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        ann = self._require_owned(current_user, announcement_id)
        if ann.is_published:
            raise AuthorizationError("Cannot edit a published announcement")
        updated = self.repo.update(announcement_id, title, content, priority, target_type)
        return _ann_dict(updated, is_read=False)

    def publish(self, current_user: User, announcement_id: str) -> Dict[str, Any]:
        self._require_owned(current_user, announcement_id)
        ann = self.repo.publish(announcement_id)
        return _ann_dict(ann, is_read=False)

    def unpublish(self, current_user: User, announcement_id: str) -> Dict[str, Any]:
        self._require_owned(current_user, announcement_id)
        ann = self.repo.unpublish(announcement_id)
        return _ann_dict(ann, is_read=False)

    def delete(self, current_user: User, announcement_id: str) -> Dict[str, Any]:
        self._require_owned(current_user, announcement_id)
        self.repo.delete(announcement_id)
        return {"deleted": True}

    def list_for_teacher(self, current_user: User) -> List[Dict[str, Any]]:
        if current_user.role != "teacher":
            raise AuthorizationError("Only teachers can list their announcements")
        anns = self.repo.list_for_teacher(current_user.id)
        return [_ann_dict(a, is_read=False) for a in anns]

    # ── Parent operations ─────────────────────────────────────────────────────

    def list_published(self, current_user: User) -> List[Dict[str, Any]]:
        anns = self.repo.list_published()
        return [
            _ann_dict(a, is_read=self.repo.is_read_by(a.id, current_user.id))
            for a in anns
        ]

    def mark_read(self, current_user: User, announcement_id: str) -> Dict[str, Any]:
        ann = self.repo.get(announcement_id)
        if not ann:
            raise NotFoundError("Announcement", announcement_id)
        self.repo.mark_read(announcement_id, current_user.id)
        return _ann_dict(ann, is_read=True)

    def count_unread(self, current_user: User) -> int:
        return self.repo.count_unread_for_user(current_user.id)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _require_owned(self, current_user: User, announcement_id: str):
        if current_user.role != "teacher":
            raise AuthorizationError("Teachers only")
        ann = self.repo.get(announcement_id)
        if not ann:
            raise NotFoundError("Announcement", announcement_id)
        if ann.teacher_id != current_user.id:
            raise AuthorizationError("You do not own this announcement")
        return ann


def _ann_dict(ann, is_read: bool) -> Dict[str, Any]:
    return {
        "id": ann.id,
        "teacher_id": ann.teacher_id,
        "title": ann.title,
        "content": ann.content,
        "priority": ann.priority,
        "is_published": ann.is_published,
        "target_type": ann.target_type,
        "is_read": is_read,
        "created_at": ann.created_at.isoformat(),
        "updated_at": ann.updated_at.isoformat(),
    }
