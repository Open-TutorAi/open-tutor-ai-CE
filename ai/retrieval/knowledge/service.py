"""Knowledge base logic for retrieval-augmented generation."""

import uuid
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ai.retrieval.knowledge.repository import KnowledgeRepository
from common.exceptions import NotFoundError


class KnowledgeService:
    def __init__(self, db: Session):
        self.repo = KnowledgeRepository(db)

    def create(self, user_id: str, data: Dict[str, Any]):
        return self.repo.create(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=data["name"],
            description=data.get("description"),
            data=data.get("data"),
            meta=data.get("access_control"),  # UI field access_control → DB column meta
        )

    def list_by_user(self, user_id: str) -> List:
        return self.repo.list_by_user(user_id)

    def get(self, id: str):
        kb = self.repo.get(id)
        if not kb:
            raise NotFoundError("KnowledgeBase", id)
        return kb

    def get_owned(self, id: str, user_id: str):
        """Fetch a knowledge base and verify ownership."""
        kb = self.get(id)
        if kb.user_id != user_id:
            raise NotFoundError("KnowledgeBase", id)
        return kb

    def update(self, id: str, user_id: str, data: Dict[str, Any]):
        self.get_owned(id, user_id)
        update_kwargs = {}
        if "name" in data:
            update_kwargs["name"] = data["name"]
        if "description" in data:
            update_kwargs["description"] = data["description"]
        if "data" in data:
            update_kwargs["data"] = data["data"]
        if "access_control" in data:
            update_kwargs["meta"] = data["access_control"]
        kb = self.repo.update(id, **update_kwargs)
        if not kb:
            raise NotFoundError("KnowledgeBase", id)
        return kb

    def add_file(self, id: str, user_id: str, file_id: str):
        self.get_owned(id, user_id)
        return self.repo.add_file(id, file_id)

    def update_file(self, id: str, user_id: str, file_id: str):
        self.get_owned(id, user_id)
        self.repo.remove_file(id, file_id)
        return self.repo.add_file(id, file_id)

    def remove_file(self, id: str, user_id: str, file_id: str):
        self.get_owned(id, user_id)
        self.repo.remove_file(id, file_id)

    def reset(self, id: str, user_id: str):
        self.get_owned(id, user_id)
        return self.repo.clear_files(id)

    def delete(self, id: str, user_id: str) -> bool:
        self.get_owned(id, user_id)
        return self.repo.delete(id)

    def get_with_files(self, id: str, user_id: str) -> dict:
        kb = self.get_owned(id, user_id)
        files = self.repo.list_files(id)
        d = kb.to_dict()
        d["files"] = [f.to_dict() for f in files]
        return d
