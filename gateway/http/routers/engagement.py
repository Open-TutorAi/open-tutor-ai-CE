"""Engagement router — /engagement/* multimodal engagement tracking.
"""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from data.models import User
from gateway.http.dependencies import get_current_user
from ai.engagement.database import get_engagement_db
from ai.engagement.service import EngagementService

router = APIRouter(prefix="/engagement", tags=["engagement"])


def _svc(db: Session = Depends(get_engagement_db)) -> EngagementService:
    return EngagementService(db)


class VideoPayload(BaseModel):
    frame: str
    session_id: Optional[str] = None


class AudioPayload(BaseModel):
    audio: str
    session_id: Optional[str] = None
    duration_seconds: Optional[int] = None
    message: Optional[str] = None
    video_score: Optional[float] = None


class ChatPayload(BaseModel):
    message: str
    session_id: Optional[str] = None
    is_voice: bool = False
    audio: Optional[str] = None
    duration_seconds: Optional[int] = None
    video_score: Optional[float] = None


@router.post("/video")
def receive_video_frame(
    payload: VideoPayload,
    user: User = Depends(get_current_user),
    svc: EngagementService = Depends(_svc),
):
    """Score a base64 webcam frame for the live indicator (not persisted).

    The score is cached and only saved when the learner sends a chat/voice.
    """
    data = svc.score_video(user.id, payload.session_id, payload.frame)
    return {"status": "ok", "video_score": data.get("video_score")}


@router.post("/audio")
def receive_audio(
    payload: AudioPayload,
    user: User = Depends(get_current_user),
    svc: EngagementService = Depends(_svc),
):
    """Score a base64 voice clip and persist the fused engagement event."""
    data = svc.record_audio(
        user.id,
        payload.session_id,
        payload.audio,
        duration_seconds=payload.duration_seconds,
        message=payload.message or "",
        video_score=payload.video_score,
    )
    return {"status": "ok", "audio_score": data.get("audio_score"), "data": data}


@router.post("/chat")
def receive_chat_message(
    payload: ChatPayload,
    user: User = Depends(get_current_user),
    svc: EngagementService = Depends(_svc),
):
    """Record a text (or transcribed-voice) interaction."""
    if payload.is_voice and payload.audio:
        data = svc.record_audio(
            user.id,
            payload.session_id,
            payload.audio,
            duration_seconds=payload.duration_seconds,
            message=payload.message,
            video_score=payload.video_score,
        )
    else:
        data = svc.record_text(
            user.id,
            payload.session_id,
            payload.message,
            video_score=payload.video_score,
        )
    return {"status": "success", "data": data}


@router.get("/session/{session_id}/summary")
def session_summary(
    session_id: str,
    limit: int = 50,
    user: User = Depends(get_current_user),
    svc: EngagementService = Depends(_svc),
):
    """Recent engagement rows + averages for a session, scoped to the user."""
    return {"status": "ok", **svc.summary(user.id, session_id=session_id, limit=limit)}


@router.get("/session/{session_id}/score")
def session_score(
    session_id: str,
    text_weight: float = 0.4,
    audio_weight: float = 0.3,
    video_weight: float = 0.3,
    user: User = Depends(get_current_user),
    svc: EngagementService = Depends(_svc),
):
    """Weighted overall score from the latest cached/estimated signals."""
    weights = {"text": text_weight, "audio": audio_weight, "video": video_weight}
    return {
        "status": "ok",
        **svc.score(user.id, session_id=session_id, weights=weights),
    }
