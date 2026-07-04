"""Messaging service — business logic + authorization (no ORM directly).

Direct (1:1) conversations between a teacher and a student who **share a class**. Starting a
conversation requires that relationship (reusing the `classrooms` data); once a conversation
exists, either participant may read and send. Per-participant `last_read_at` drives unread
counts. Realtime *delivery* (emit) is the router's concern; this owns truth + authz.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from accounts.users.service import AccountService as IdentityService
from classrooms.repository import ClassroomRepository, EnrollmentRepository
from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from content.files.service import FilesService
from data.models import (
    Classroom,
    Conversation,
    ConversationParticipant,
    Enrollment,
    Message,
)
from messaging.repository import (
    ConversationRepository,
    MessageRepository,
    ParticipantRepository,
)


class MessagingService:
    """Service for conversations + messages."""

    def __init__(self, session: Session):
        self.session = session
        self.conversations = ConversationRepository(session, Conversation)
        self.participants = ParticipantRepository(session, ConversationParticipant)
        self.messages = MessageRepository(session, Message)
        self.classrooms = ClassroomRepository(session, Classroom)
        self.enrollments = EnrollmentRepository(session, Enrollment)
        self.identity = IdentityService(session)
        self.files = FilesService(session)

    # ── relationship + membership helpers ────────────────────────────────────

    def _with_attachment(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Add `attachment_name` next to an `attachment_id` in a serialized message."""
        if d.get("attachment_id"):
            rec = self.files.get(d["attachment_id"])
            d["attachment_name"] = rec.filename if rec else None
        return d

    def _teaches(self, teacher_id: str, student_id: str) -> bool:
        """True if `teacher_id` owns a class in which `student_id` is enrolled."""
        for room in self.classrooms.get_by_teacher(teacher_id):
            if self.enrollments.get(room.id, student_id):
                return True
        return False

    def _related(self, user_a: str, user_b: str) -> bool:
        """Symmetric: the two share a class as teacher/enrolled-student (either way)."""
        return self._teaches(user_a, user_b) or self._teaches(user_b, user_a)

    def _membership(
        self, conversation_id: str, user_id: str
    ) -> ConversationParticipant:
        participant = self.participants.get(conversation_id, user_id)
        if not participant:
            # Hide existence of conversations the caller isn't part of.
            raise NotFoundError("Conversation", conversation_id)
        return participant

    # ── read-model assembly ──────────────────────────────────────────────────

    def _other_participant(
        self, conversation_id: str, viewer_id: str
    ) -> ConversationParticipant:
        for p in self.participants.list_for_conversation(conversation_id):
            if p.user_id != viewer_id:
                return p
        return None

    def _conversation_dict(
        self, conversation: Conversation, viewer_id: str, last_read_at
    ) -> Dict[str, Any]:
        other = self._other_participant(conversation.id, viewer_id)
        other_user = self.identity.get_user(other.user_id) if other else None
        last = self.messages.last_for_conversation(conversation.id)
        # Preview text: the body, or "📎 Attachment" for an attachment-only message.
        last_preview = None
        if last:
            last_preview = last.body or (
                "📎 " + ("Attachment" if last.attachment_id else "")
            )
        return {
            "id": conversation.id,
            "other_user_id": other.user_id if other else None,
            "other_name": other_user.name if other_user else None,
            "other_email": other_user.email if other_user else None,
            "last_message": last_preview,
            "last_message_at": (
                conversation.last_message_at.isoformat()
                if conversation.last_message_at
                else None
            ),
            "unread": self.messages.count_unread(
                conversation.id, viewer_id, last_read_at
            ),
        }

    # ── operations ───────────────────────────────────────────────────────────

    def start(self, initiator_id: str, recipient_id: str) -> Dict[str, Any]:
        """Open (or reuse) a 1:1 conversation with a related user. Idempotent."""
        if initiator_id == recipient_id:
            raise ValidationError("Cannot start a conversation with yourself")
        if not self.identity.get_user(recipient_id):
            raise NotFoundError("User", recipient_id)
        if not self._related(initiator_id, recipient_id):
            raise AuthorizationError("You can only message students in your classes")

        existing = self.conversations.find_direct(initiator_id, recipient_id)
        if existing:
            participant = self.participants.get(existing.id, initiator_id)
            return self._conversation_dict(
                existing,
                initiator_id,
                participant.last_read_at if participant else None,
            )

        # One unit of work: the conversation and both participant rows commit
        # together, so a failure can't leave a half-created conversation.
        conversation = self.conversations.create(
            commit=False,
            id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            last_message_at=None,
        )
        for uid in (initiator_id, recipient_id):
            self.participants.create(
                commit=False,
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                user_id=uid,
                last_read_at=None,
            )
        self.session.commit()
        return self._conversation_dict(conversation, initiator_id, None)

    def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """All of the user's conversations, most-recent first."""
        rows: List[Dict[str, Any]] = []
        for participant in self.participants.list_for_user(user_id):
            conversation = self.conversations.get_by_id(participant.conversation_id)
            if conversation:
                rows.append(
                    self._conversation_dict(
                        conversation, user_id, participant.last_read_at
                    )
                )
        rows.sort(key=lambda r: r["last_message_at"] or "", reverse=True)
        return rows

    def get_messages(self, conversation_id: str, user_id: str) -> Dict[str, Any]:
        """Messages in a conversation the caller belongs to; marks them read."""
        participant = self._membership(conversation_id, user_id)
        conversation = self.conversations.get_by_id(conversation_id)
        items = [
            self._with_attachment(m.to_dict())
            for m in self.messages.list_for_conversation(conversation_id)
        ]
        # Mark read up to now.
        participant.last_read_at = datetime.utcnow()
        self.session.commit()
        return {
            "conversation": self._conversation_dict(
                conversation, user_id, participant.last_read_at
            ),
            "messages": items,
        }

    def send_message(
        self,
        conversation_id: str,
        user_id: str,
        body: str,
        attachment_id: str = None,
    ) -> Dict[str, Any]:
        """Post a message (caller must be a participant). Returns the message + the
        other participant id(s) so the router can deliver it live."""
        self._membership(conversation_id, user_id)
        body = body.strip() if isinstance(body, str) else ""
        attachment_id = attachment_id or None
        if not body and not attachment_id:
            raise ValidationError("Message body or an attachment is required")
        if attachment_id:
            self.files.require_owned(attachment_id, user_id)

        now = datetime.utcnow()
        message = self.messages.create(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            sender_id=user_id,
            body=body or None,
            attachment_id=attachment_id,
            created_at=now,
        )
        conversation = self.conversations.get_by_id(conversation_id)
        conversation.last_message_at = now
        self.session.commit()

        recipients = [
            p.user_id
            for p in self.participants.list_for_conversation(conversation_id)
            if p.user_id != user_id
        ]
        return {
            "message": self._with_attachment(message.to_dict()),
            "recipients": recipients,
        }

    def read_message_attachment(
        self, conversation_id: str, message_id: str, user_id: str
    ) -> tuple:
        """Bytes of a message's attachment, for any participant of the conversation.
        Returns (data, content_type, filename)."""
        self._membership(conversation_id, user_id)  # 404 hides non-membership
        message = self.messages.get_by_id(message_id)
        if (
            not message
            or message.conversation_id != conversation_id
            or not message.attachment_id
        ):
            raise NotFoundError("Attachment", message_id)
        data, content_type = self.files.read_bytes(message.attachment_id)
        rec = self.files.get(message.attachment_id)
        return data, content_type, (rec.filename if rec else "attachment")
