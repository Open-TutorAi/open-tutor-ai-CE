"""Pydantic models for feedback API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SubmitFeedbackRequest(BaseModel):
    """Submit feedback request."""

    response_id: str
    feedback_type: str  # positive, negative, neutral
    content: Optional[str] = None
    rating: Optional[float] = None


class FeedbackResponse(BaseModel):
    """Feedback response."""

    id: str
    user_id: str
    response_id: str
    feedback_type: str
    content: Optional[str]
    rating: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
