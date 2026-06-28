"""Diagnostics router — /diagnostics/* routes."""

import threading
import time
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from common.exceptions import AuthorizationError, NotFoundError
from data.models import User
from gateway.http.dependencies import get_current_user, get_diagnostics_service
from learning.diagnostics.service import DiagnosticsService

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

# ── Rate limiting (in-process, per-user) ──────────────────────────────────────

_rate_store: dict[str, list[float]] = {}
_rate_lock = threading.Lock()

_RATE_LIMIT = 10  # max calls per window
_RATE_WINDOW = 60  # window in seconds


async def _check_rate(key: str) -> None:
    now = time.time()
    with _rate_lock:
        calls = [t for t in _rate_store.get(key, []) if t > now - _RATE_WINDOW]
        if len(calls) >= _RATE_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests — maximum {_RATE_LIMIT} per minute",
            )
        _rate_store[key] = calls + [now]


async def _require_generate_rl(current_user: User = Depends(get_current_user)) -> None:
    await _check_rate(f"gen:{current_user.id}")


async def _require_submit_rl(current_user: User = Depends(get_current_user)) -> None:
    await _check_rate(f"sub:{current_user.id}")


# ── Request / response schemas ────────────────────────────────────────────────


class GenerateRequest(BaseModel):
    support_id: str = Field(min_length=1, max_length=36)
    model_id: str = Field(min_length=1, max_length=100)


class AnswerItem(BaseModel):
    question_id: int = Field(ge=1, le=100)
    answer: str = Field(min_length=1, max_length=500)


class SubmitRequest(BaseModel):
    answers: List[AnswerItem] = Field(min_length=1, max_length=50)


class DiagnosticResponse(BaseModel):
    id: str
    support_id: str
    user_id: str
    questions: Optional[List[Any]] = None
    answers: Optional[List[Any]] = None
    score: Optional[int] = None
    determined_level: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Helpers ───────────────────────────────────────────────────────────────────


def _sanitize_questions(questions, diag_status):
    """Strip correct_answer and explanation when diagnostic is still pending."""
    if not questions or diag_status == "completed":
        return questions
    return [
        {k: v for k, v in q.items() if k not in ("correct_answer", "explanation")}
        for q in questions
    ]


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post("/generate", response_model=DiagnosticResponse)
async def generate_diagnostic(
    data: GenerateRequest,
    current_user: User = Depends(get_current_user),
    svc: DiagnosticsService = Depends(get_diagnostics_service),
    _rl: None = Depends(_require_generate_rl),
):
    try:
        result = await svc.generate(data.support_id, current_user.id, data.model_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM provider unavailable",
        )
    result.questions = _sanitize_questions(result.questions, result.status)
    return result


@router.post("/{diagnostic_id}/submit", response_model=DiagnosticResponse)
def submit_diagnostic(
    diagnostic_id: str,
    data: SubmitRequest,
    current_user: User = Depends(get_current_user),
    svc: DiagnosticsService = Depends(get_diagnostics_service),
    _rl: None = Depends(_require_submit_rl),
):
    try:
        result = svc.submit(
            diagnostic_id,
            current_user.id,
            [a.model_dump() for a in data.answers],
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return result


@router.get("/by-support/{support_id}", response_model=Optional[DiagnosticResponse])
def get_by_support(
    support_id: str,
    current_user: User = Depends(get_current_user),
    svc: DiagnosticsService = Depends(get_diagnostics_service),
):
    result = svc.get_by_support(support_id)
    if result and result.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    return result


@router.get("/{diagnostic_id}", response_model=DiagnosticResponse)
def get_diagnostic(
    diagnostic_id: str,
    current_user: User = Depends(get_current_user),
    svc: DiagnosticsService = Depends(get_diagnostics_service),
):
    result = svc.get(diagnostic_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic not found"
        )
    if result.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    return result
