"""Announcement (classroom stream post) request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AnnouncementCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class AnnouncementOut(BaseModel):
    id: str
    classroom_id: str
    author_id: str
    author_name: Optional[str] = None
    content: str
    created_at: datetime
