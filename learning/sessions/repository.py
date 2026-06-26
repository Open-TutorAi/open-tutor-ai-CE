"""Chat repository."""

from typing import List, Optional

from data.models import Chat
from data.repositories import BaseRepository


class ChatRepository(BaseRepository[Chat]):
    def get_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Chat]:
        return (
            self.session.query(Chat)
            .filter(Chat.user_id == user_id, Chat.archived.is_(False))
            .order_by(Chat.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_pinned(self, user_id: str) -> List[Chat]:
        return (
            self.session.query(Chat)
            .filter(
                Chat.user_id == user_id,
                Chat.pinned.is_(True),
                Chat.archived.is_(False),
            )
            .order_by(Chat.updated_at.desc())
            .all()
        )

    def get_archived(self, user_id: str) -> List[Chat]:
        return (
            self.session.query(Chat)
            .filter(Chat.user_id == user_id, Chat.archived.is_(True))
            .order_by(Chat.updated_at.desc())
            .all()
        )

    def get_all_for_user(self, user_id: str) -> List[Chat]:
        return (
            self.session.query(Chat)
            .filter(Chat.user_id == user_id)
            .order_by(Chat.updated_at.desc())
            .all()
        )

    def get_by_share_id(self, share_id: str) -> Optional[Chat]:
        return self.session.query(Chat).filter(Chat.share_id == share_id).first()

    def get_by_folder(self, user_id: str, folder_id: str) -> List[Chat]:
        return (
            self.session.query(Chat)
            .filter(Chat.user_id == user_id, Chat.folder_id == folder_id)
            .order_by(Chat.updated_at.desc())
            .all()
        )

    def search(self, user_id: str, query: str) -> List[Chat]:
        q = f"%{query}%"
        return (
            self.session.query(Chat)
            .filter(Chat.user_id == user_id, Chat.title.ilike(q))
            .order_by(Chat.updated_at.desc())
            .all()
        )

    def get_all_tags(self, user_id: str) -> List[str]:
        # NOTE: loads all of a user's chats and aggregates tags in Python.
        # Acceptable at small scale; revisit with a tags table / JSON SQL query
        # if chat volumes grow large.
        chats = self.get_all_for_user(user_id)
        tags = set()
        for chat in chats:
            for t in (chat.meta or {}).get("tags", []):
                tags.add(t.get("name", t) if isinstance(t, dict) else t)
        return sorted(tags)

    def list_by_tag(self, user_id: str, tag_name: str) -> List[Chat]:
        chats = self.get_all_for_user(user_id)
        return [
            c
            for c in chats
            if any(
                (t.get("name") if isinstance(t, dict) else t) == tag_name
                for t in (c.meta or {}).get("tags", [])
            )
        ]

    def add_tag(self, chat: Chat, tag_name: str) -> Chat:
        meta = dict(chat.meta or {})
        tags = meta.get("tags", [])
        if not any(
            (t.get("name") == tag_name if isinstance(t, dict) else t == tag_name)
            for t in tags
        ):
            tags.append({"name": tag_name})
        meta["tags"] = tags
        chat.meta = meta
        self.session.commit()
        self.session.refresh(chat)
        return chat

    def remove_tag(self, chat: Chat, tag_name: str) -> Chat:
        meta = dict(chat.meta or {})
        tags = [
            t
            for t in meta.get("tags", [])
            if (t.get("name") if isinstance(t, dict) else t) != tag_name
        ]
        meta["tags"] = tags
        chat.meta = meta
        self.session.commit()
        self.session.refresh(chat)
        return chat

    def remove_all_tags(self, chat: Chat) -> Chat:
        meta = dict(chat.meta or {})
        meta["tags"] = []
        chat.meta = meta
        self.session.commit()
        self.session.refresh(chat)
        return chat

    def archive_all(self, user_id: str) -> int:
        count = (
            self.session.query(Chat)
            .filter(Chat.user_id == user_id, Chat.archived.is_(False))
            .count()
        )
        (
            self.session.query(Chat)
            .filter(Chat.user_id == user_id)
            .update({Chat.archived: True})
        )
        self.session.commit()
        return count

    def delete_all(self, user_id: str) -> int:
        count = self.session.query(Chat).filter(Chat.user_id == user_id).count()
        self.session.query(Chat).filter(Chat.user_id == user_id).delete()
        self.session.commit()
        return count
