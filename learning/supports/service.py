"""Support request service."""

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.models import Support, SupportFile
from learning.supports.repository import SupportRepository


class SupportsService:
    """Service for support request operations."""

    def __init__(self, session: Session):
        self.repo = SupportRepository(session, Support)

    def create(self, user_id: str, data: Dict[str, Any]) -> Support:
        keywords = data.get("keywords")
        return self.repo.create(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=data["title"],
            short_description=data.get("short_description"),
            subject=data.get("subject"),
            custom_subject=data.get("custom_subject"),
            course_id=data.get("course_id"),
            learning_objective=data.get("learning_objective"),
            learning_type=data.get("learning_type"),
            level=data.get("level"),
            content_language=data.get("content_language", "English"),
            estimated_duration=data.get("estimated_duration"),
            access_type=data.get("access_type", "Private"),
            keywords=",".join(keywords) if keywords else None,
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            avatar_id=data.get("avatar_id"),
            chat_id=data.get("chat_id"),
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def get(self, support_id: str) -> Optional[Support]:
        return self.repo.get_by_id(support_id)

    def list_for_user(
        self, user_id: str, status: Optional[str] = None
    ) -> List[Support]:
        return self.repo.get_by_user(user_id, status)

    def update(self, support_id: str, data: Dict[str, Any]) -> Support:
        update_fields: Dict[str, Any] = {}
        for key, value in data.items():
            if key == "keywords":
                update_fields["keywords"] = ",".join(value) if value else None
            else:
                update_fields[key] = value
        update_fields["updated_at"] = datetime.utcnow()
        return self.repo.update(support_id, **update_fields)

    def update_chat_id(self, support_id: str, chat_id: str) -> Support:
        return self.repo.update(
            support_id, chat_id=chat_id, updated_at=datetime.utcnow()
        )

    def delete(self, support_id: str) -> None:
        self.repo.delete_files(support_id)
        self.repo.delete(support_id)

    def verify_ownership(self, user_id: str, support_id: str) -> None:
        """Raise early if the user does not own the support request."""
        support = self.repo.get_by_id(support_id)
        if not support:
            raise NotFoundError("Support", support_id)
        if support.user_id != user_id:
            raise AuthorizationError("You do not own this support request")

    def upload_file(
        self,
        user_id: str,
        support_id: str,
        filename: str,
        content_type: Optional[str],
        contents: bytes,
        upload_dir: str,
        max_size_mb: int,
    ) -> SupportFile:
        """Validate ownership + size, write to disk, persist record."""
        support = self.repo.get_by_id(support_id)
        if not support:
            raise NotFoundError("Support", support_id)
        if support.user_id != user_id:
            raise AuthorizationError("You do not own this support request")

        max_bytes = max_size_mb * 1024 * 1024
        if len(contents) > max_bytes:
            raise ValidationError(
                f"File exceeds the {max_size_mb} MB limit", field="file"
            )

        os.makedirs(upload_dir, exist_ok=True)
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(filename or "")[1]
        save_path = os.path.join(upload_dir, f"{file_id}{ext}")
        with open(save_path, "wb") as fh:
            fh.write(contents)

        record = SupportFile(
            id=file_id,
            support_id=support_id,
            filename=filename,
            file_path=save_path,
            file_type=content_type,
            file_size=len(contents),
            created_at=datetime.utcnow(),
        )
        return self.repo.add_file(record)
