"""Announcements repository."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from data.models.announcement import Announcement, AnnouncementRead


class AnnouncementRepository:
    def __init__(self, session: Session):
        self.session = session

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def create(
        self,
        teacher_id: str,
        title: str,
        content: str,
        priority: str = "normal",
        target_type: str = "all",
    ) -> Announcement:
        ann = Announcement(
            id=str(uuid.uuid4()),
            teacher_id=teacher_id,
            title=title,
            content=content,
            priority=priority,
            target_type=target_type,
            is_published=False,
        )
        self.session.add(ann)
        self.session.commit()
        self.session.refresh(ann)
        return ann

    def get(self, announcement_id: str) -> Optional[Announcement]:
        return (
            self.session.query(Announcement)
            .filter(Announcement.id == announcement_id)
            .first()
        )

    def update(
        self,
        announcement_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        priority: Optional[str] = None,
        target_type: Optional[str] = None,
    ) -> Optional[Announcement]:
        ann = self.get(announcement_id)
        if not ann:
            return None
        if title is not None:
            ann.title = title
        if content is not None:
            ann.content = content
        if priority is not None:
            ann.priority = priority
        if target_type is not None:
            ann.target_type = target_type
        ann.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(ann)
        return ann

    def publish(self, announcement_id: str) -> Optional[Announcement]:
        ann = self.get(announcement_id)
        if not ann:
            return None
        ann.is_published = True
        ann.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(ann)
        return ann

    def unpublish(self, announcement_id: str) -> Optional[Announcement]:
        ann = self.get(announcement_id)
        if not ann:
            return None
        ann.is_published = False
        ann.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(ann)
        return ann

    def delete(self, announcement_id: str) -> bool:
        ann = self.get(announcement_id)
        if not ann:
            return False
        # Remove reads first
        self.session.query(AnnouncementRead).filter(
            AnnouncementRead.announcement_id == announcement_id
        ).delete()
        self.session.delete(ann)
        self.session.commit()
        return True

    def list_for_teacher(self, teacher_id: str) -> List[Announcement]:
        return (
            self.session.query(Announcement)
            .filter(Announcement.teacher_id == teacher_id)
            .order_by(Announcement.created_at.desc())
            .all()
        )

    def list_published(self) -> List[Announcement]:
        return (
            self.session.query(Announcement)
            .filter(Announcement.is_published == True)  # noqa: E712
            .order_by(Announcement.created_at.desc())
            .all()
        )

    # ── Read tracking ─────────────────────────────────────────────────────────

    def mark_read(self, announcement_id: str, user_id: str) -> AnnouncementRead:
        existing = (
            self.session.query(AnnouncementRead)
            .filter(
                AnnouncementRead.announcement_id == announcement_id,
                AnnouncementRead.user_id == user_id,
            )
            .first()
        )
        if existing:
            return existing
        record = AnnouncementRead(
            id=str(uuid.uuid4()),
            announcement_id=announcement_id,
            user_id=user_id,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def is_read_by(self, announcement_id: str, user_id: str) -> bool:
        return (
            self.session.query(AnnouncementRead)
            .filter(
                AnnouncementRead.announcement_id == announcement_id,
                AnnouncementRead.user_id == user_id,
            )
            .first()
            is not None
        )

    def count_unread_for_user(self, user_id: str) -> int:
        read_ids = (
            self.session.query(AnnouncementRead.announcement_id)
            .filter(AnnouncementRead.user_id == user_id)
            .subquery()
        )
        return (
            self.session.query(Announcement)
            .filter(
                Announcement.is_published == True,  # noqa: E712
                ~Announcement.id.in_(read_ids),
            )
            .count()
        )
