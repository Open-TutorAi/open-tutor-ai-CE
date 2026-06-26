"""Chats service."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from common.exceptions import AuthorizationError, NotFoundError
from data.models import Chat
from learning.sessions.repository import ChatRepository


class ChatsService:
    def __init__(self, session: Session):
        self.repo = ChatRepository(session, Chat)

    def _require_owned(self, chat_id: str, user_id: str) -> Chat:
        chat = self.repo.get_by_id(chat_id)
        if not chat:
            raise NotFoundError("Chat", chat_id)
        if chat.user_id != user_id:
            raise AuthorizationError("You do not own this chat")
        return chat

    def create(self, user_id: str, chat_data: Dict[str, Any]) -> Chat:
        title = chat_data.get("title", "New Chat")
        return self.repo.create(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            chat=chat_data,
            archived=False,
            pinned=False,
            meta={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def get(self, chat_id: str, user_id: str) -> Chat:
        chat = self.repo.get_by_id(chat_id)
        if not chat:
            raise NotFoundError("Chat", chat_id)
        if chat.user_id != user_id:
            raise AuthorizationError("Not authorized")
        return chat

    def get_by_share_id(self, share_id: str) -> Optional[Chat]:
        return self.repo.get_by_share_id(share_id)

    def list_for_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Chat]:
        return self.repo.get_by_user(user_id, skip=skip, limit=limit)

    def list_pinned(self, user_id: str) -> List[Chat]:
        return self.repo.get_pinned(user_id)

    def list_archived(self, user_id: str) -> List[Chat]:
        return self.repo.get_archived(user_id)

    def list_all(self, user_id: str) -> List[Chat]:
        return self.repo.get_all_for_user(user_id)

    def list_by_folder(self, user_id: str, folder_id: str) -> List[Chat]:
        return self.repo.get_by_folder(user_id, folder_id)

    def search(self, user_id: str, query: str) -> List[Chat]:
        return self.repo.search(user_id, query)

    def update(self, chat_id: str, user_id: str, chat_data: Dict[str, Any]) -> Chat:
        chat = self._require_owned(chat_id, user_id)
        title = chat_data.get("title", chat.title)
        return self.repo.update(
            chat_id, title=title, chat=chat_data, updated_at=datetime.utcnow()
        )

    def archive(self, chat_id: str, user_id: str) -> Chat:
        chat = self._require_owned(chat_id, user_id)
        return self.repo.update(
            chat_id, archived=not chat.archived, updated_at=datetime.utcnow()
        )

    def archive_all(self, user_id: str) -> int:
        return self.repo.archive_all(user_id)

    def pin(self, chat_id: str, user_id: str) -> Chat:
        chat = self._require_owned(chat_id, user_id)
        return self.repo.update(
            chat_id, pinned=not chat.pinned, updated_at=datetime.utcnow()
        )

    def get_pinned_status(self, chat_id: str, user_id: str) -> bool:
        chat = self._require_owned(chat_id, user_id)
        return chat.pinned

    def share(self, chat_id: str, user_id: str) -> Chat:
        chat = self._require_owned(chat_id, user_id)
        if chat.share_id:
            return chat
        return self.repo.update(
            chat_id, share_id=str(uuid.uuid4()), updated_at=datetime.utcnow()
        )

    def unshare(self, chat_id: str, user_id: str) -> Chat:
        self._require_owned(chat_id, user_id)
        return self.repo.update(chat_id, share_id=None, updated_at=datetime.utcnow())

    def set_folder(self, chat_id: str, user_id: str, folder_id: Optional[str]) -> Chat:
        self._require_owned(chat_id, user_id)
        return self.repo.update(
            chat_id, folder_id=folder_id, updated_at=datetime.utcnow()
        )

    def get_tags(self, chat_id: str, user_id: str) -> List[dict]:
        chat = self._require_owned(chat_id, user_id)
        return (chat.meta or {}).get("tags", [])

    def get_all_tags(self, user_id: str) -> List[str]:
        return self.repo.get_all_tags(user_id)

    def list_by_tag(self, user_id: str, tag_name: str) -> List[Chat]:
        return self.repo.list_by_tag(user_id, tag_name)

    def add_tag(self, chat_id: str, user_id: str, tag_name: str) -> Chat:
        chat = self._require_owned(chat_id, user_id)
        return self.repo.add_tag(chat, tag_name)

    def remove_tag(self, chat_id: str, user_id: str, tag_name: str) -> Chat:
        chat = self._require_owned(chat_id, user_id)
        return self.repo.remove_tag(chat, tag_name)

    def remove_all_tags(self, chat_id: str, user_id: str) -> Chat:
        chat = self._require_owned(chat_id, user_id)
        return self.repo.remove_all_tags(chat)

    def delete(self, chat_id: str, user_id: str) -> bool:
        self._require_owned(chat_id, user_id)
        return self.repo.delete(chat_id)

    def delete_all(self, user_id: str) -> int:
        return self.repo.delete_all(user_id)
