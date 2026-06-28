"""Message attachment model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from data.database import Base


class MessageAttachment(Base):
    """A file attached to a parent-teacher message."""

    __tablename__ = "message_attachments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(
        String(36),
        ForeignKey("parent_teacher_messages.id"),
        nullable=True,
        index=True,
    )
    conversation_id = Column(
        String(36),
        ForeignKey("parent_teacher_conversations.id"),
        nullable=True,
        index=True,
    )
    uploader_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    original_filename = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)  # UUID-based stored filename
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    file_path = Column(Text, nullable=False)  # absolute disk path
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
