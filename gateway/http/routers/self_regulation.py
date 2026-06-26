"""Self-regulation router — /self_regulation/* routes matching OpenTutorAI vocabulary."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from data.models import User
from gateway.http.dependencies import get_current_user, get_self_regulation_service
from governance.self_regulation.service import SelfRegulationService

router = APIRouter(prefix="/self_regulation", tags=["self_regulation"])

# In-memory config stub — replace with DB-backed config when needed
_config: Dict[str, Any] = {}


class FeedbackForm(BaseModel):
    """Flexible feedback payload for HITL self-regulation."""

    data: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    snapshot: Optional[Dict[str, Any]] = None


def _parse_form(form: FeedbackForm, feedback_type: str = "neutral") -> dict:
    data = form.data or {}
    return {
        "feedback_type": data.get("rating", feedback_type),
        "response_id": data.get("sibling_model_id") or data.get("response_id"),
        "content": data.get("comment"),
        "rating": None,
    }


# ── Config ────────────────────────────────────────────────────────────────────


@router.get("/config")
async def get_config(current_user: User = Depends(get_current_user)):
    return _config


@router.post("/config")
async def update_config(
    config: Dict[str, Any], current_user: User = Depends(get_current_user)
):
    _config.update(config)
    return _config


# ── Feedback CRUD ─────────────────────────────────────────────────────────────


@router.get("/feedbacks/all")
async def get_all_feedbacks(
    current_user: User = Depends(get_current_user),
    svc: SelfRegulationService = Depends(get_self_regulation_service),
):
    return [f.to_dict() for f in svc.get_all()]


@router.get("/feedbacks/all/export")
async def export_feedbacks(
    current_user: User = Depends(get_current_user),
    svc: SelfRegulationService = Depends(get_self_regulation_service),
):
    return [f.to_dict() for f in svc.get_all()]


@router.post("/feedback")
async def create_feedback(
    form: FeedbackForm,
    current_user: User = Depends(get_current_user),
    svc: SelfRegulationService = Depends(get_self_regulation_service),
):
    parsed = _parse_form(form)
    feedback = svc.submit(user_id=current_user.id, **parsed)
    return feedback.to_dict()


@router.get("/feedback/{feedback_id}")
async def get_feedback(
    feedback_id: str,
    current_user: User = Depends(get_current_user),
    svc: SelfRegulationService = Depends(get_self_regulation_service),
):
    feedback = svc.get(feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found"
        )
    if feedback.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    return feedback.to_dict()


@router.post("/feedback/{feedback_id}")
async def update_feedback(
    feedback_id: str,
    form: FeedbackForm,
    current_user: User = Depends(get_current_user),
    svc: SelfRegulationService = Depends(get_self_regulation_service),
):
    feedback = svc.get(feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found"
        )
    if feedback.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    data = form.data or {}
    update_fields = {}
    if "rating" in data:
        update_fields["feedback_type"] = data["rating"]
    if "comment" in data:
        update_fields["content"] = data["comment"]
    updated = svc.update(feedback_id, update_fields)
    return updated.to_dict()


@router.delete("/feedback/{feedback_id}")
async def delete_feedback(
    feedback_id: str,
    current_user: User = Depends(get_current_user),
    svc: SelfRegulationService = Depends(get_self_regulation_service),
):
    feedback = svc.get(feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found"
        )
    if feedback.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    svc.delete(feedback_id)
    return {"status": "success"}


# ── Response-feedback (CC compat) ─────────────────────────────────────────────


@router.get("/response-feedbacks/all")
async def get_response_feedbacks(
    current_user: User = Depends(get_current_user),
    svc: SelfRegulationService = Depends(get_self_regulation_service),
):
    return [f.to_dict() for f in svc.get_by_type("response_comparison")]


@router.post("/response-feedback")
async def create_response_feedback(
    form: FeedbackForm,
    current_user: User = Depends(get_current_user),
    svc: SelfRegulationService = Depends(get_self_regulation_service),
):
    parsed = _parse_form(form, feedback_type="response_comparison")
    parsed["feedback_type"] = "response_comparison"
    feedback = svc.submit(user_id=current_user.id, **parsed)
    return feedback.to_dict()


@router.get("/response-feedback/{feedback_id}")
async def get_response_feedback(
    feedback_id: str,
    current_user: User = Depends(get_current_user),
    svc: SelfRegulationService = Depends(get_self_regulation_service),
):
    feedback = svc.get(feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found"
        )
    return feedback.to_dict()
