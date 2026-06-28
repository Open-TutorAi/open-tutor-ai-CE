"""Classroom announcement models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from data.database import Base


class Announcement(Base):
    """A one-way announcement from a teacher to parents."""

    __tablename__ = "announcements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    # normal | important | urgent
    priority = Column(String(20), nullable=False, default="normal")
    is_published = Column(Boolean, default=False, nullable=False)
    # all | class | selected — extensible for future targeting
    target_type = Column(String(20), nullable=False, default="all")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class AnnouncementRead(Base):
    """Records when a user (parent) has read an announcement."""

    __tablename__ = "announcement_reads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    announcement_id = Column(
        String(36),
        ForeignKey("announcements.id"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    read_at = Column(DateTime, default=datetime.utcnow, nullable=False)
