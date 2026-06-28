"""Messages service."""

import os
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from config import settings
from data.models import User
from learning.messages.repository import MessageRepository

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "video/mp4", "video/quicktime", "video/webm",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "application/zip",
}


class MessagesService:
    def __init__(self, session: Session):
        self.repo = MessageRepository(session)

    # ── Admin / setup helpers ─────────────────────────────────────────────────

    def link_parent_student(self, parent_id: str, student_id: str) -> Dict[str, Any]:
        link = self.repo.link_parent_student(parent_id, student_id)
        return {"parent_id": link.parent_id, "student_id": link.student_id}

    def link_teacher_student(
        self, teacher_id: str, student_id: str
    ) -> Dict[str, Any]:
        link = self.repo.link_teacher_student(teacher_id, student_id)
        return {"teacher_id": link.teacher_id, "student_id": link.student_id}

    # ── Teacher discovery ─────────────────────────────────────────────────────

    def get_teachers_of_child(
        self, parent: User, student_id: str
    ) -> List[Dict[str, Any]]:
        children = self.repo.get_children_of_parent(parent.id)
        if not any(c.id == student_id for c in children):
            raise AuthorizationError("This student is not linked to your account")
        return [_user_dict(t) for t in self.repo.get_teachers_of_student(student_id)]

    def get_all_children_teachers(self, parent: User) -> List[Dict[str, Any]]:
        children = self.repo.get_children_of_parent(parent.id)
        result = []
        for child in children:
            for teacher in self.repo.get_teachers_of_student(child.id):
                result.append(
                    {"student": _user_dict(child), "teacher": _user_dict(teacher)}
                )
        return result

    # ── Conversations ─────────────────────────────────────────────────────────

    def get_conversations(self, current_user: User) -> List[Dict[str, Any]]:
        if current_user.role == "parent":
            convs = self.repo.get_conversations_for_parent(current_user.id)
        elif current_user.role == "teacher":
            convs = self.repo.get_conversations_for_teacher(current_user.id)
        else:
            raise AuthorizationError("Only parents and teachers can access messages")
        return [self._conv_dict(c, current_user.id) for c in convs]

    def send_message(
        self,
        current_user: User,
        receiver_id: str,
        student_id: str,
        content: str,
        attachment_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if current_user.role not in ("parent", "teacher"):
            raise AuthorizationError("Only parents and teachers can send messages")

        if current_user.role == "parent":
            parent_id, teacher_id = current_user.id, receiver_id
            children = self.repo.get_children_of_parent(parent_id)
            if not any(c.id == student_id for c in children):
                raise AuthorizationError("This student is not linked to your account")
        else:
            teacher_id, parent_id = current_user.id, receiver_id

        conv = self.repo.get_or_create_conversation(parent_id, teacher_id, student_id)
        msg = self.repo.create_message(conv.id, current_user.id, content)

        if attachment_ids:
            self.repo.link_attachments_to_message(attachment_ids, msg.id)
            # Reload with attachments
            msg = self.repo.get_message(msg.id)

        return _msg_dict(msg)

    def get_messages(
        self, current_user: User, conversation_id: str
    ) -> List[Dict[str, Any]]:
        conv = self.repo.get_conversation(conversation_id)
        if not conv:
            raise NotFoundError("Conversation", conversation_id)
        if current_user.id not in (conv.parent_id, conv.teacher_id):
            raise AuthorizationError("Not a participant in this conversation")
        messages = self.repo.get_messages(conversation_id)
        for msg in messages:
            if msg.sender_id != current_user.id and not msg.is_read:
                self.repo.mark_as_read(msg.id)
        return [_msg_dict(m) for m in messages]

    def mark_message_read(
        self, current_user: User, message_id: str
    ) -> Dict[str, Any]:
        msg = self.repo.get_message(message_id)
        if not msg:
            raise NotFoundError("Message", message_id)
        conv = self.repo.get_conversation(msg.conversation_id)
        if not conv or current_user.id not in (conv.parent_id, conv.teacher_id):
            raise AuthorizationError("Not a participant in this conversation")
        updated = self.repo.mark_as_read(message_id)
        return _msg_dict(updated)

    # ── Attachments ───────────────────────────────────────────────────────────

    def upload_attachment(
        self,
        current_user: User,
        conversation_id: str,
        filename: str,
        content_type: str,
        file_bytes: bytes,
    ) -> Dict[str, Any]:
        if current_user.role not in ("parent", "teacher"):
            raise AuthorizationError("Only parents and teachers can upload attachments")

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise ValidationError(
                f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB} MB"
            )

        if content_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(f"File type not allowed: {content_type}")

        # Verify user is a participant in this conversation
        conv = self.repo.get_conversation(conversation_id)
        if not conv:
            raise NotFoundError("Conversation", conversation_id)
        if current_user.id not in (conv.parent_id, conv.teacher_id):
            raise AuthorizationError("Not a participant in this conversation")

        file_id = str(uuid.uuid4())
        ext = os.path.splitext(filename or "")[1]
        stored_filename = f"msg_{file_id}{ext}"
        upload_dir = os.path.join(settings.UPLOAD_DIR, "messages")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, stored_filename)

        with open(file_path, "wb") as fh:
            fh.write(file_bytes)

        att = self.repo.create_attachment(
            uploader_id=current_user.id,
            conversation_id=conversation_id,
            original_filename=filename,
            filename=stored_filename,
            mime_type=content_type,
            file_size=len(file_bytes),
            file_path=file_path,
        )
        return _att_dict(att)

    def get_attachment(
        self, current_user: User, attachment_id: str
    ) -> Dict[str, Any]:
        att = self.repo.get_attachment(attachment_id)
        if not att:
            raise NotFoundError("Attachment", attachment_id)

        # Verify user is a participant in the conversation
        if att.conversation_id:
            conv = self.repo.get_conversation(att.conversation_id)
            if not conv or current_user.id not in (conv.parent_id, conv.teacher_id):
                raise AuthorizationError("Not authorised to download this attachment")

        return _att_dict(att)

    def _conv_dict(self, conv, current_user_id: str) -> Dict[str, Any]:
        unread = self.repo.count_unread(conv.id, current_user_id)
        # Resolve human-readable names
        parent = self.repo.session.query(User).filter(User.id == conv.parent_id).first()
        teacher = self.repo.session.query(User).filter(User.id == conv.teacher_id).first()
        student = self.repo.session.query(User).filter(User.id == conv.student_id).first()
        return {
            "id": conv.id,
            "parent_id": conv.parent_id,
            "teacher_id": conv.teacher_id,
            "student_id": conv.student_id,
            "parent_name": parent.name if parent else conv.parent_id,
            "teacher_name": teacher.name if teacher else conv.teacher_id,
            "student_name": student.name if student else conv.student_id,
            "unread_count": unread,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
        }


def _user_dict(user: User) -> Dict[str, Any]:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "profile_image_url": user.profile_image_url,
        "role": user.role,
    }


def _msg_dict(msg) -> Dict[str, Any]:
    attachments = []
    if hasattr(msg, "attachments") and msg.attachments:
        attachments = [_att_dict(a) for a in msg.attachments]
    return {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "sender_id": msg.sender_id,
        "content": msg.content,
        "is_read": msg.is_read,
        "attachments": attachments,
        "created_at": msg.created_at.isoformat(),
    }


def _att_dict(att) -> Dict[str, Any]:
    return {
        "id": att.id,
        "message_id": att.message_id,
        "conversation_id": att.conversation_id,
        "original_filename": att.original_filename,
        "mime_type": att.mime_type,
        "file_size": att.file_size,
        "uploaded_at": att.uploaded_at.isoformat(),
    }
