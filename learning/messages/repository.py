"""Messages repository."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from data.models import User
from data.models.attachment import MessageAttachment
from data.models.message import (
    ParentStudent,
    ParentTeacherConversation,
    ParentTeacherMessage,
    TeacherStudent,
)


class MessageRepository:
    def __init__(self, session: Session):
        self.session = session

    # ── Linking tables ────────────────────────────────────────────────────────

    def link_parent_student(self, parent_id: str, student_id: str) -> ParentStudent:
        existing = (
            self.session.query(ParentStudent)
            .filter(
                ParentStudent.parent_id == parent_id,
                ParentStudent.student_id == student_id,
            )
            .first()
        )
        if existing:
            return existing
        link = ParentStudent(
            id=str(uuid.uuid4()), parent_id=parent_id, student_id=student_id
        )
        self.session.add(link)
        self.session.commit()
        return link

    def link_teacher_student(self, teacher_id: str, student_id: str) -> TeacherStudent:
        existing = (
            self.session.query(TeacherStudent)
            .filter(
                TeacherStudent.teacher_id == teacher_id,
                TeacherStudent.student_id == student_id,
            )
            .first()
        )
        if existing:
            return existing
        link = TeacherStudent(
            id=str(uuid.uuid4()), teacher_id=teacher_id, student_id=student_id
        )
        self.session.add(link)
        self.session.commit()
        return link

    def get_children_of_parent(self, parent_id: str) -> List[User]:
        links = (
            self.session.query(ParentStudent)
            .filter(ParentStudent.parent_id == parent_id)
            .all()
        )
        if not links:
            return []
        student_ids = [lnk.student_id for lnk in links]
        return self.session.query(User).filter(User.id.in_(student_ids)).all()

    def get_teachers_of_student(self, student_id: str) -> List[User]:
        links = (
            self.session.query(TeacherStudent)
            .filter(TeacherStudent.student_id == student_id)
            .all()
        )
        if not links:
            return []
        teacher_ids = [lnk.teacher_id for lnk in links]
        return self.session.query(User).filter(User.id.in_(teacher_ids)).all()

    def get_students_of_teacher(self, teacher_id: str) -> List[User]:
        links = (
            self.session.query(TeacherStudent)
            .filter(TeacherStudent.teacher_id == teacher_id)
            .all()
        )
        if not links:
            return []
        student_ids = [lnk.student_id for lnk in links]
        return self.session.query(User).filter(User.id.in_(student_ids)).all()

    # ── Conversations ─────────────────────────────────────────────────────────

    def get_or_create_conversation(
        self, parent_id: str, teacher_id: str, student_id: str
    ) -> ParentTeacherConversation:
        conv = (
            self.session.query(ParentTeacherConversation)
            .filter(
                ParentTeacherConversation.parent_id == parent_id,
                ParentTeacherConversation.teacher_id == teacher_id,
                ParentTeacherConversation.student_id == student_id,
            )
            .first()
        )
        if conv:
            return conv
        conv = ParentTeacherConversation(
            id=str(uuid.uuid4()),
            parent_id=parent_id,
            teacher_id=teacher_id,
            student_id=student_id,
        )
        self.session.add(conv)
        self.session.commit()
        self.session.refresh(conv)
        return conv

    def get_conversation(
        self, conversation_id: str
    ) -> Optional[ParentTeacherConversation]:
        return (
            self.session.query(ParentTeacherConversation)
            .filter(ParentTeacherConversation.id == conversation_id)
            .first()
        )

    def get_conversations_for_parent(
        self, parent_id: str
    ) -> List[ParentTeacherConversation]:
        return (
            self.session.query(ParentTeacherConversation)
            .filter(ParentTeacherConversation.parent_id == parent_id)
            .order_by(ParentTeacherConversation.updated_at.desc())
            .all()
        )

    def get_conversations_for_teacher(
        self, teacher_id: str
    ) -> List[ParentTeacherConversation]:
        return (
            self.session.query(ParentTeacherConversation)
            .filter(ParentTeacherConversation.teacher_id == teacher_id)
            .order_by(ParentTeacherConversation.updated_at.desc())
            .all()
        )

    # ── Messages ──────────────────────────────────────────────────────────────

    def create_message(
        self, conversation_id: str, sender_id: str, content: str
    ) -> ParentTeacherMessage:
        msg = ParentTeacherMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
        )
        self.session.add(msg)
        conv = self.get_conversation(conversation_id)
        if conv:
            conv.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(msg)
        return msg

    def get_messages(self, conversation_id: str) -> List[ParentTeacherMessage]:
        return (
            self.session.query(ParentTeacherMessage)
            .filter(ParentTeacherMessage.conversation_id == conversation_id)
            .order_by(ParentTeacherMessage.created_at)
            .all()
        )

    def get_message(self, message_id: str) -> Optional[ParentTeacherMessage]:
        return (
            self.session.query(ParentTeacherMessage)
            .filter(ParentTeacherMessage.id == message_id)
            .first()
        )

    def mark_as_read(self, message_id: str) -> Optional[ParentTeacherMessage]:
        msg = self.get_message(message_id)
        if not msg:
            return None
        msg.is_read = True
        self.session.commit()
        self.session.refresh(msg)
        return msg

    def count_unread(self, conversation_id: str, user_id: str) -> int:
        return (
            self.session.query(ParentTeacherMessage)
            .filter(
                ParentTeacherMessage.conversation_id == conversation_id,
                ParentTeacherMessage.sender_id != user_id,
                ParentTeacherMessage.is_read == False,  # noqa: E712
            )
            .count()
        )

    # ── Attachments ───────────────────────────────────────────────────────────

    def create_attachment(
        self,
        uploader_id: str,
        conversation_id: Optional[str],
        original_filename: str,
        filename: str,
        mime_type: str,
        file_size: int,
        file_path: str,
    ) -> MessageAttachment:
        att = MessageAttachment(
            id=str(uuid.uuid4()),
            message_id=None,
            conversation_id=conversation_id,
            uploader_id=uploader_id,
            original_filename=original_filename,
            filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            file_path=file_path,
        )
        self.session.add(att)
        self.session.commit()
        self.session.refresh(att)
        return att

    def link_attachments_to_message(
        self, attachment_ids: List[str], message_id: str
    ) -> None:
        if not attachment_ids:
            return
        self.session.query(MessageAttachment).filter(
            MessageAttachment.id.in_(attachment_ids),
            MessageAttachment.message_id.is_(None),
        ).update({"message_id": message_id}, synchronize_session="fetch")
        self.session.commit()

    def get_attachment(self, attachment_id: str) -> Optional[MessageAttachment]:
        return (
            self.session.query(MessageAttachment)
            .filter(MessageAttachment.id == attachment_id)
            .first()
        )

    def get_attachments_for_message(
        self, message_id: str
    ) -> List[MessageAttachment]:
        return (
            self.session.query(MessageAttachment)
            .filter(MessageAttachment.message_id == message_id)
            .order_by(MessageAttachment.uploaded_at)
            .all()
        )
