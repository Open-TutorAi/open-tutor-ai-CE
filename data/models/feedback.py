"""Feedback domain model - replaces response_feedbacks."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from data.database import Base


class Feedback(Base):
    """Feedback/self-regulation model - replaces open_webui.models.feedbacks."""

    __tablename__ = "feedbacks"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    response_id = Column(String(255), nullable=True, index=True)
    feedback_type = Column(String(50), nullable=False)  # positive, negative, neutral
    content = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)  # Optional numeric rating
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="feedbacks")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "response_id": self.response_id,
            "feedback_type": self.feedback_type,
            "content": self.content,
            "rating": self.rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
