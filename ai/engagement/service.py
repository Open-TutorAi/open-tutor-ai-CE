"""Engagement service logic for multimodal engagement scoring.
"""

import logging
from typing import Optional, Dict
from sqlalchemy.orm import Session

from .repository import EngagementRepository
from .cache import (
    latest_video_scores,
    latest_audio_scores,
    ema_update,
    decay_score,
    get_recent_video_score,
)
from .text_core import compute_text_metrics, compute_text_score_estimate
from .audio_core import compute_audio_score
from .video_core import compute_video_score
from .fusion import compute_overall_score
from .models import EngagementMetric

logger = logging.getLogger("engagement")

# Default fusion weights — Overall = 40% text + 30% audio + 30% video.
DEFAULT_WEIGHTS: Dict[str, float] = {"text": 0.4, "audio": 0.3, "video": 0.3}


def _strip_data_url(b64: Optional[str]) -> Optional[str]:

    if b64 and b64.startswith("data:"):
        try:
            return b64.split(",", 1)[1]
        except Exception:
            return b64
    return b64


# Engagement-level thresholds recalibrated from the real score distribution
# (tertiles) rather than the original heuristic 0.40/0.70: collected sessions
# cluster around 0.42 (disengaged) and 0.70 (engaged), so the heuristic cut
# points collapsed almost everything to MEDIUM. See manual_check/calibrate.py
# and RESULTATS_ANALYSE.md (§7).
LEVEL_LOW_MAX = 0.53
LEVEL_HIGH_MIN = 0.69


def _level(score: Optional[float]) -> Optional[str]:
    if score is None:
        return None
    if score >= LEVEL_HIGH_MIN:
        return "HIGH"
    if score >= LEVEL_LOW_MAX:
        return "MEDIUM"
    return "LOW"


class EngagementService:
    """Compute, fuse, persist and aggregate engagement metrics for a learner."""

    def __init__(self, session: Session):
        self.repo = EngagementRepository(session, EngagementMetric)

    def _persist(
        self,
        user_id: str,
        session_id: Optional[str],
        modality: str,
        *,
        message: Optional[str] = None,
        text_score: Optional[float] = None,
        audio_score: Optional[float] = None,
        video_score: Optional[float] = None,
        audio_duration: Optional[int] = None,
        words: Optional[int] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> dict:
        scores = {"text": text_score, "audio": audio_score, "video": video_score}
        fusion_score = compute_overall_score(scores, weights=weights or DEFAULT_WEIGHTS)
        record = self.repo.create(
            user_id=user_id,
            session_id=session_id,
            modality=modality,
            message=message,
            text_score=text_score,
            audio_score=audio_score,
            video_score=video_score,
            audio_duration=audio_duration,
            words=words,
            fusion_score=fusion_score,
            engagement_level=_level(fusion_score),
        )
        return record.to_dict()

    def record_text(
        self,
        user_id: str,
        session_id: Optional[str],
        message: str,
        video_score: Optional[float] = None,
    ) -> dict:
        """Record a text interaction, capturing the current webcam score."""
        metrics = compute_text_metrics(user_id, message, session_id=session_id)
        if video_score is None:
            video_score = get_recent_video_score(user_id)
        return self._persist(
            user_id,
            session_id,
            modality="text",
            message=message,
            text_score=metrics.get("chat_score"),
            video_score=video_score,
            words=metrics.get("words"),
        )

    def record_audio(
        self,
        user_id: str,
        session_id: Optional[str],
        audio_base64: str,
        duration_seconds: Optional[int] = None,
        message: str = "",
        video_score: Optional[float] = None,
    ) -> dict:
        """Record a voice interaction; score the audio and fuse with video/text."""
        audio_base64 = _strip_data_url(audio_base64)
        audio_score = compute_audio_score(audio_base64) if audio_base64 else None
        if video_score is None:
            video_score = get_recent_video_score(user_id)

        text_score = None
        words = None
        if message:
            metrics = compute_text_metrics(user_id, message, session_id=session_id)
            text_score = metrics.get("chat_score")
            words = metrics.get("words")

        if audio_score is not None:
            audio_score = ema_update(latest_audio_scores, user_id, audio_score)

        return self._persist(
            user_id,
            session_id,
            modality="audio",
            message=message or None,
            text_score=text_score,
            audio_score=audio_score,
            video_score=video_score,
            audio_duration=duration_seconds,
            words=words,
        )

    def score_video(
        self, user_id: str, session_id: Optional[str], frame_base64: str
    ) -> dict:
        """Score a webcam frame for the live indicator and cache it."""
        frame_base64 = _strip_data_url(frame_base64)
        if not frame_base64:
            return {"video_score": latest_video_scores.get(user_id)}

        video_score = compute_video_score(frame_base64)
        if video_score is not None:
            # Smooth across frames so the live webcam score is stable.
            video_score = ema_update(latest_video_scores, user_id, video_score)
        else:
            # A frame arrived but no face was found (learner looked away or left
            # the frame). Decay the cached score instead of freezing it at the
            # last high value, so visual disengagement is reflected.
            video_score = decay_score(latest_video_scores, user_id)
        return {"video_score": video_score}

    # Analytics
    def summary(
        self, user_id: str, session_id: Optional[str] = None, limit: int = 50
    ) -> dict:
        rows = self.repo.recent(user_id, session_id=session_id, limit=limit)
        return {
            "user_id": user_id,
            "session_id": session_id,
            "count": len(rows),
            "averages": self.repo.averages(user_id, session_id=session_id),
            "rows": [r.to_dict() for r in rows],
        }

    def score(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> dict:
        weights = weights or DEFAULT_WEIGHTS
        text_metrics = compute_text_score_estimate(user_id, session_id=session_id)
        scores = {
            "text": text_metrics.get("text_score"),
            "audio": latest_audio_scores.get(user_id),
            "video": latest_video_scores.get(user_id),
        }
        overall = compute_overall_score(scores, weights=weights)
        return {
            "user_id": user_id,
            "session_id": session_id,
            "scores": scores,
            "text_metrics": text_metrics,
            "weights": weights,
            "overall_score": overall,
            "engagement_level": _level(overall),
        }
