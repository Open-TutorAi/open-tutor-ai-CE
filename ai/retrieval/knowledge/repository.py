"""Knowledge base data access."""

from typing import List, Optional

from sqlalchemy.orm import Session

from data.models.knowledge import KnowledgeBase, KnowledgeFile


class KnowledgeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> KnowledgeBase:
        kb = KnowledgeBase(**kwargs)
        self.db.add(kb)
        self.db.commit()
        self.db.refresh(kb)
        return kb

    def get(self, id: str) -> Optional[KnowledgeBase]:
        return self.db.query(KnowledgeBase).filter(KnowledgeBase.id == id).first()

    def list_by_user(self, user_id: str) -> List[KnowledgeBase]:
        return (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.user_id == user_id)
            .order_by(KnowledgeBase.created_at.desc())
            .all()
        )

    def update(self, id: str, **kwargs) -> Optional[KnowledgeBase]:
        kb = self.get(id)
        if not kb:
            return None
        for k, v in kwargs.items():
            setattr(kb, k, v)
        self.db.commit()
        self.db.refresh(kb)
        return kb

    def delete(self, id: str) -> bool:
        kb = self.get(id)
        if not kb:
            return False
        self.db.delete(kb)
        self.db.commit()
        return True

    def add_file(self, knowledge_id: str, file_id: str) -> KnowledgeFile:
        kf = KnowledgeFile(knowledge_id=knowledge_id, file_id=file_id)
        self.db.add(kf)
        self.db.commit()
        self.db.refresh(kf)
        return kf

    def remove_file(self, knowledge_id: str, file_id: str) -> bool:
        kf = (
            self.db.query(KnowledgeFile)
            .filter(
                KnowledgeFile.knowledge_id == knowledge_id,
                KnowledgeFile.file_id == file_id,
            )
            .first()
        )
        if not kf:
            return False
        self.db.delete(kf)
        self.db.commit()
        return True

    def list_files(self, knowledge_id: str) -> List[KnowledgeFile]:
        return (
            self.db.query(KnowledgeFile)
            .filter(KnowledgeFile.knowledge_id == knowledge_id)
            .all()
        )

    def clear_files(self, knowledge_id: str) -> int:
        n = (
            self.db.query(KnowledgeFile)
            .filter(KnowledgeFile.knowledge_id == knowledge_id)
            .delete()
        )
        self.db.commit()
        return n
