"""File repository."""

import os
from typing import List

from data.models import FileRecord
from data.repositories import BaseRepository


class FileRepository(BaseRepository[FileRecord]):
    def get_by_user(self, user_id: str) -> List[FileRecord]:
        return (
            self.session.query(FileRecord)
            .filter(FileRecord.user_id == user_id)
            .order_by(FileRecord.created_at.desc())
            .all()
        )

    def delete_all_for_user(self, user_id: str) -> int:
        records = self.get_by_user(user_id)
        for record in records:
            self._remove_disk_file(record)
        count = len(records)
        self.session.query(FileRecord).filter(FileRecord.user_id == user_id).delete()
        self.session.commit()
        return count

    def delete_record(self, record: FileRecord) -> None:
        self._remove_disk_file(record)
        self.session.delete(record)
        self.session.commit()

    @staticmethod
    def _remove_disk_file(record: FileRecord) -> None:
        if record.path and os.path.exists(record.path):
            try:
                os.remove(record.path)
            except OSError:
                pass
