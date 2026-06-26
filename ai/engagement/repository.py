"""Engagement repository."""

from typing import List, Optional
from sqlalchemy import func
from data.repositories import BaseRepository
from .models import EngagementMetric


class EngagementRepository(BaseRepository[EngagementMetric]):
    """Pure data access for engagement metrics."""

    def recent(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[EngagementMetric]:
        """Return the most recent metrics for a user."""
        q = self.session.query(EngagementMetric).filter(
            EngagementMetric.user_id == user_id
        )
        if session_id is not None:
            q = q.filter(EngagementMetric.session_id == session_id)
        return q.order_by(EngagementMetric.created_at.desc()).limit(limit).all()

    def averages(self, user_id: str, session_id: Optional[str] = None) -> dict:
        """Return per-modality average scores and the row count for a scope."""
        q = self.session.query(
            func.avg(EngagementMetric.text_score),
            func.avg(EngagementMetric.audio_score),
            func.avg(EngagementMetric.video_score),
            func.avg(EngagementMetric.fusion_score),
            func.count(EngagementMetric.id),
        ).filter(EngagementMetric.user_id == user_id)
        if session_id is not None:
            q = q.filter(EngagementMetric.session_id == session_id)
        text_avg, audio_avg, video_avg, fusion_avg, count = q.one()
        return {
            "text": round(text_avg, 3) if text_avg is not None else None,
            "audio": round(audio_avg, 3) if audio_avg is not None else None,
            "video": round(video_avg, 3) if video_avg is not None else None,
            "fusion": round(fusion_avg, 3) if fusion_avg is not None else None,
            "count": int(count or 0),
        }
