"""File service."""

import os
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from config import settings
from content.files.repository import FileRepository
from data.models import FileRecord


class FilesService:
    def __init__(self, session: Session):
        self.repo = FileRepository(session, FileRecord)

    def upload(
        self,
        user_id: str,
        filename: str,
        content_type: Optional[str],
        contents: bytes,
    ) -> FileRecord:
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(contents) > max_bytes:
            raise ValidationError(
                f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit", field="file"
            )

        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(filename or "")[1]
        save_path = os.path.join(upload_dir, f"{file_id}{ext}")
        with open(save_path, "wb") as fh:
            fh.write(contents)

        return self.repo.create(
            id=file_id,
            user_id=user_id,
            filename=filename,
            path=save_path,
            content_type=content_type,
            size=len(contents),
            data=None,
            meta={
                "content_type": content_type,
                "name": filename,
                "size": len(contents),
            },
            created_at=datetime.utcnow(),
        )

    def list_for_user(self, user_id: str) -> List[FileRecord]:
        return self.repo.get_by_user(user_id)

    def get(self, file_id: str) -> Optional[FileRecord]:
        return self.repo.get_by_id(file_id)

    def require_owned(self, file_id: str, user_id: str) -> FileRecord:
        record = self.repo.get_by_id(file_id)
        if not record:
            raise NotFoundError("File", file_id)
        if record.user_id != user_id:
            raise AuthorizationError("You do not own this file")
        return record

    def update_content(self, file_id: str, user_id: str, content: str) -> FileRecord:
        record = self.require_owned(file_id, user_id)
        record.data = {"content": content}
        self.repo.session.commit()
        self.repo.session.refresh(record)
        return record

    def read_bytes(self, file_id: str) -> tuple[bytes, str]:
        """Return (content_bytes, content_type). Raises NotFoundError if absent."""
        record = self.repo.get_by_id(file_id)
        if not record:
            raise NotFoundError("File", file_id)
        if record.path and os.path.exists(record.path):
            with open(record.path, "rb") as fh:
                return fh.read(), record.content_type or "application/octet-stream"
        # Fallback: stored text content
        text = (record.data or {}).get("content", "")
        return text.encode(), "text/plain"

    def delete(self, file_id: str, user_id: str) -> None:
        record = self.require_owned(file_id, user_id)
        self.repo.delete_record(record)

    def delete_all(self, user_id: str) -> int:
        return self.repo.delete_all_for_user(user_id)
