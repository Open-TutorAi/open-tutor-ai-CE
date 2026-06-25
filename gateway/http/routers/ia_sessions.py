"""Router Sessions IA — /api/v1/ia-sessions/* (US-P04)."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from common.exceptions import AuthorizationError, NotFoundError
from data.models import User
from gateway.http.dependencies import get_current_user, get_ia_sessions_service
from learning.sessions.ia_service import IASessionsService

router = APIRouter(prefix="/ia-sessions", tags=["ia-sessions"])


# ── Schémas de réponse ────────────────────────────────────────────────────────


class MetriquesResponse(BaseModel):
    engagement: float
    comprehension: float
    autonomie: float


class SessionSummaryResponse(BaseModel):
    id: str
    matiere: str
    duree_minutes: int
    quality_score: float
    alerte_difficulte: bool
    themes: List[str] = []
    questions: List[str] = []
    resume: Optional[str] = None
    metriques: Optional[MetriquesResponse] = None
    statut: str


class StatsResponse(BaseModel):
    total: int
    avec_alerte: int
    score_moyen: float


class SessionListResponse(BaseModel):
    sessions: List[SessionSummaryResponse]
    stats: StatsResponse


class SessionDetailResponse(SessionSummaryResponse):
    pass


class TranscriptResponse(BaseModel):
    session_id: str
    transcript_text: str


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/", response_model=SessionListResponse)
async def list_ia_sessions(
    child_id: str = Query(..., description="UUID de l'enfant — SÉCURITÉ: anti-IDOR"),
    subject: Optional[str] = Query(None, max_length=100),
    period: Optional[str] = Query(None, max_length=20),
    current_user: User = Depends(get_current_user),
    svc: IASessionsService = Depends(get_ia_sessions_service),
):
    """
    GET /api/v1/ia-sessions/?child_id=X
    Steps 5→11 du diagramme de séquence.
    SÉCURITÉ : child_id validé côté service (anti-IDOR).
    """
    try:
        result = svc.get_session_summaries(
            child_id=child_id,
            parent_id=current_user.id,
            subject=subject,
            period=period,
        )
    except AuthorizationError:
        # SÉCURITÉ : 403 sans détail interne exposé au client.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé",
        )
    return result


@router.get("/{session_id}/detail", response_model=SessionDetailResponse)
async def get_ia_session_detail(
    session_id: str,
    child_id: str = Query(..., description="UUID de l'enfant"),
    current_user: User = Depends(get_current_user),
    svc: IASessionsService = Depends(get_ia_sessions_service),
):
    """
    GET /api/v1/ia-sessions/{session_id}/detail
    Steps 16→21 : clic session → generateSummary() déclenché.
    """
    try:
        return svc.get_session_detail(
            session_id=session_id,
            parent_id=current_user.id,
            child_id=child_id,
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session introuvable",
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé",
        )


@router.get("/{session_id}/transcript", response_model=TranscriptResponse)
async def get_ia_session_transcript(
    session_id: str,
    child_id: str = Query(..., description="UUID de l'enfant"),
    current_user: User = Depends(get_current_user),
    svc: IASessionsService = Depends(get_ia_sessions_service),
):
    """
    GET /api/v1/ia-sessions/{session_id}/transcript
    Steps 23→25 : accès transcription complète.
    """
    try:
        return svc.get_session_transcript(
            session_id=session_id,
            parent_id=current_user.id,
            child_id=child_id,
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription introuvable",
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé",
        )
