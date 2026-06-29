"""Audio router — /audio/* matching audio/index.ts UI client.

Admin-only: config read/write with API key stored in config.
Verified user: transcriptions, speech, models, voices.
"""

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai.media.audio import AudioService
from data.database import get_db
from data.models import User
from gateway.http.dependencies import get_current_user

router = APIRouter(prefix="/audio", tags=["audio"])


def _svc(db: Session = Depends(get_db)) -> AudioService:
    return AudioService(db)


def _require_admin(user: User) -> None:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


class AudioConfigUpdate(BaseModel):
    # Flat schema matching UI's OpenAIConfigForm: {url, key, model, speaker}
    url: Optional[str] = None
    key: Optional[str] = None
    model: Optional[str] = None
    speaker: Optional[str] = None


# ── Admin-only: config ────────────────────────────────────────────────────────


@router.get("/config")
def get_config(
    user: User = Depends(get_current_user), svc: AudioService = Depends(_svc)
):
    _require_admin(user)
    return svc.get_config()


@router.post("/config/update")
def update_config(
    body: AudioConfigUpdate,
    user: User = Depends(get_current_user),
    svc: AudioService = Depends(_svc),
):
    _require_admin(user)
    return svc.update_config(body.model_dump(exclude_none=True))


# ── Verified user: transcriptions, speech, models, voices ────────────────────


@router.post("/transcriptions")
async def transcribe(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    svc: AudioService = Depends(_svc),
):
    cfg = svc.get_config()
    url = (cfg.get("url") or "").rstrip("/")
    key = cfg.get("key") or ""
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio STT URL not configured",
        )
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{url}/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {key}"},
            files={
                "file": (
                    file.filename,
                    await file.read(),
                    file.content_type or "audio/mpeg",
                )
            },
            data={"model": cfg.get("model") or "whisper-1"},
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@router.post("/speech")
async def synthesize_speech(
    body: dict,
    user: User = Depends(get_current_user),
    svc: AudioService = Depends(_svc),
):
    cfg = svc.get_config()
    url = (cfg.get("url") or "").rstrip("/")
    key = cfg.get("key") or ""
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio TTS URL not configured",
        )
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{url}/v1/audio/speech",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": body.get("model") or cfg.get("model") or "tts-1",
                "input": body.get("input", ""),
                "voice": body.get("voice") or cfg.get("speaker") or "alloy",
            },
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return Response(
        content=r.content, media_type=r.headers.get("content-type", "audio/mpeg")
    )


@router.get("/models")
def get_models(
    user: User = Depends(get_current_user), svc: AudioService = Depends(_svc)
):
    return svc.get_models()


@router.get("/voices")
def get_voices(
    user: User = Depends(get_current_user), svc: AudioService = Depends(_svc)
):
    return svc.get_voices()
