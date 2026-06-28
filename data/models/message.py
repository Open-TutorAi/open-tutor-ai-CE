"""Parent-Teacher messaging models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from data.database import Base


class ParentStudent(Base):
    """Links a parent user to their child (student) user."""

    __tablename__ = "parent_students"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TeacherStudent(Base):
    """Links a teacher user to a student they teach."""

    __tablename__ = "teacher_students"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ParentTeacherConversation(Base):
    """A thread between a parent and a teacher about a specific student."""

    __tablename__ = "parent_teacher_conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    teacher_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    messages = relationship(
        "ParentTeacherMessage",
        back_populates="conversation",
        order_by="ParentTeacherMessage.created_at",
    )


class ParentTeacherMessage(Base):
    """A single message within a parent-teacher conversation."""

    __tablename__ = "parent_teacher_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String(36),
        ForeignKey("parent_teacher_conversations.id"),
        nullable=False,
        index=True,
    )
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    conversation = relationship("ParentTeacherConversation", back_populates="messages")
    attachments = relationship(
        "MessageAttachment",
        primaryjoin="ParentTeacherMessage.id == foreign(MessageAttachment.message_id)",
        lazy="select",
        order_by="MessageAttachment.uploaded_at",
    )
