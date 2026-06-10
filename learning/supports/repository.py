"""Support repository."""

import os
from typing import List, Optional

from data.models import Support, SupportFile
from data.repositories import BaseRepository


class SupportRepository(BaseRepository[Support]):
    """Repository for support operations."""

    def get_by_user(self, user_id: str, status: Optional[str] = None) -> List[Support]:
        query = self.session.query(Support).filter(Support.user_id == user_id)
        if status:
            query = query.filter(Support.status == status)
        return query.order_by(Support.created_at.desc()).all()

    def get_files(self, support_id: str) -> List[SupportFile]:
        return (
            self.session.query(SupportFile)
            .filter(SupportFile.support_id == support_id)
            .all()
        )

    def add_file(self, file: SupportFile) -> SupportFile:
        self.session.add(file)
        self.session.commit()
        return file

    def delete_files(self, support_id: str) -> None:
        files = self.get_files(support_id)
        for f in files:
            try:
                if os.path.exists(f.file_path):
                    os.remove(f.file_path)
            except OSError:
                pass
        self.session.query(SupportFile).filter(
            SupportFile.support_id == support_id
        ).delete()
