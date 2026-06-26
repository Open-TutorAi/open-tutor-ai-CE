import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from .database import EngagementBase


class EngagementMetric(EngagementBase):
    """A single engagement measurement for a learner during a session.

    Each row captures the per-modality scores (text / audio / video) computed
    at one moment plus the fused overall score and a coarse level label. Rows
    are scoped to the authenticated ``user_id`` and, when available, a
    ``session_id`` (the chat/learning session) so history can be aggregated
    per learner and per session.

    Lives in its own database — kept separate from the main application tables.
    """

    __tablename__ = "engagement_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    modality = Column(String(32), nullable=False)
    message = Column(Text, nullable=True)
    text_score = Column(Float, nullable=True)
    audio_score = Column(Float, nullable=True)
    video_score = Column(Float, nullable=True)
    audio_duration = Column(Integer, nullable=True)
    words = Column(Integer, nullable=True)
    fusion_score = Column(Float, nullable=True)
    engagement_level = Column(String(16), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "modality": self.modality,
            "message": self.message,
            "text_score": self.text_score,
            "audio_score": self.audio_score,
            "video_score": self.video_score,
            "audio_duration": self.audio_duration,
            "words": self.words,
            "fusion_score": self.fusion_score,
            "engagement_level": self.engagement_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
