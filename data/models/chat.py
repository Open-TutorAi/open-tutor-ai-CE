"""Chat conversation model."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, String, Text

from data.database import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    title = Column(Text, nullable=False, default="New Chat")
    chat = Column(JSON, nullable=True)
    share_id = Column(String(36), nullable=True, unique=True, index=True)
    archived = Column(Boolean, default=False, nullable=False)
    pinned = Column(Boolean, default=False, nullable=False)
    folder_id = Column(String(36), nullable=True, index=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "chat": self.chat,
            "share_id": self.share_id,
            "archived": self.archived,
            "pinned": self.pinned,
            "folder_id": self.folder_id,
            "meta": self.meta,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_title_id(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
