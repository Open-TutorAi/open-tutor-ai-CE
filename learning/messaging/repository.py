"""Messaging repositories — data access only (SQLAlchemy, no business logic)."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func

from data.models import Conversation, ConversationParticipant, Message
from data.repositories import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Data access for conversations."""

    def find_direct(self, user_a: str, user_b: str) -> Optional[Conversation]:
        """The 1:1 conversation containing exactly these two users, if any."""
        rows = (
            self.session.query(ConversationParticipant.conversation_id)
            .filter(ConversationParticipant.user_id.in_([user_a, user_b]))
            .group_by(ConversationParticipant.conversation_id)
            .having(func.count(func.distinct(ConversationParticipant.user_id)) == 2)
            .all()
        )
        for (conversation_id,) in rows:
            participants = (
                self.session.query(ConversationParticipant)
                .filter(ConversationParticipant.conversation_id == conversation_id)
                .count()
            )
            if participants == 2:
                return self.get_by_id(conversation_id)
        return None


class ParticipantRepository(BaseRepository[ConversationParticipant]):
    """Data access for conversation membership + per-user read state."""

    def get(
        self, conversation_id: str, user_id: str
    ) -> Optional[ConversationParticipant]:
        return (
            self.session.query(ConversationParticipant)
            .filter(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
            )
            .first()
        )

    def list_for_conversation(
        self, conversation_id: str
    ) -> List[ConversationParticipant]:
        return (
            self.session.query(ConversationParticipant)
            .filter(ConversationParticipant.conversation_id == conversation_id)
            .all()
        )

    def list_for_user(self, user_id: str) -> List[ConversationParticipant]:
        return (
            self.session.query(ConversationParticipant)
            .filter(ConversationParticipant.user_id == user_id)
            .all()
        )


class MessageRepository(BaseRepository[Message]):
    """Data access for messages."""

    def list_for_conversation(self, conversation_id: str) -> List[Message]:
        return (
            self.session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )

    def last_for_conversation(self, conversation_id: str) -> Optional[Message]:
        return (
            self.session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .first()
        )

    def count_unread(
        self, conversation_id: str, viewer_id: str, since: Optional[datetime]
    ) -> int:
        """Messages from the *other* party newer than the viewer's last read."""
        q = self.session.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.sender_id != viewer_id,
        )
        if since is not None:
            q = q.filter(Message.created_at > since)
        return q.count()
