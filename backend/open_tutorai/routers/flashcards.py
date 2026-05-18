import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker

from open_webui.internal.db import engine
from open_webui.utils.auth import get_verified_user
from open_tutorai.models.database import FlashcardSet, Support

log = logging.getLogger(__name__)
log.setLevel("INFO")

router = APIRouter()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

SYSTEM_PROMPT = """You are an educational assistant. Given a tutoring conversation or lesson text, extract the most important concepts and return ONLY a valid JSON object in this exact format, with no extra text before or after:
{"flashcards": [{"question": "...", "answer": "..."}, ...]}
Rules:
- Extract between 3 and 10 flashcards.
- Cover key questions, definitions, and important notions.
- Keep answers concise (1–3 sentences max).
- Output ONLY the JSON object, nothing else."""


# ---------- Pydantic models ----------

class CardItem(BaseModel):
    question: str
    answer: str


class FlashcardGenerateRequest(BaseModel):
    messages: list[dict]
    model: str
    title: str = "Flashcard Set"
    source_label: Optional[str] = None
    support_id: Optional[str] = None


class ProgressUpdateRequest(BaseModel):
    known_indices: list[int]


class FlashcardSetResponse(BaseModel):
    id: str
    title: str
    source_label: Optional[str]
    support_id: Optional[str]
    model_used: Optional[str]
    cards: list[CardItem]
    known_indices: list[int]
    card_count: int
    known_count: int
    created_at: str
    updated_at: Optional[str]


# ---------- helpers ----------

def _to_response(fs: FlashcardSet) -> FlashcardSetResponse:
    cards = fs.cards or []
    known = fs.known_indices or []
    return FlashcardSetResponse(
        id=fs.id,
        title=fs.title,
        source_label=fs.source_label,
        support_id=fs.support_id,
        model_used=fs.model_used,
        cards=[CardItem(**c) for c in cards],
        known_indices=known,
        card_count=len(cards),
        known_count=len(known),
        created_at=fs.created_at.isoformat() if fs.created_at else "",
        updated_at=fs.updated_at.isoformat() if fs.updated_at else None,
    )


def _get_set_or_404(db, set_id: str, user_id: str) -> FlashcardSet:
    fs = db.query(FlashcardSet).filter(
        FlashcardSet.id == set_id,
        FlashcardSet.user_id == user_id,
    ).first()
    if not fs:
        raise HTTPException(status_code=404, detail="Flashcard set not found")
    return fs


def _validate_support_ownership(db, support_id: str, user_id: str) -> Support:
    support = db.query(Support).filter(
        Support.id == support_id,
        Support.user_id == user_id,
    ).first()
    if not support:
        raise HTTPException(status_code=400, detail="support_id is invalid or does not belong to the current user")
    return support


def _validate_flashcards(raw_cards):
    if not isinstance(raw_cards, list):
        raise ValueError("flashcards must be a list")

    validated_cards = []
    for item in raw_cards:
        if not isinstance(item, dict):
            raise ValueError("each flashcard must be an object")

        question = item.get("question")
        answer = item.get("answer")
        if not isinstance(question, str) or not isinstance(answer, str):
            raise ValueError("flashcard question and answer must be strings")

        question = question.strip()
        answer = answer.strip()
        if not question or not answer:
            raise ValueError("flashcard question and answer must not be empty")

        if len(question) > 500:
            question = question[:500].rstrip()
        if len(answer) > 1500:
            answer = answer[:1500].rstrip()

        validated_cards.append(CardItem(question=question, answer=answer).dict())

    if len(validated_cards) < 3 or len(validated_cards) > 10:
        raise ValueError("flashcards must contain between 3 and 10 cards")

    return validated_cards


def _normalize_known_indices(known_indices: list[int], card_count: int) -> list[int]:
    if card_count <= 0:
        return []

    invalid = [idx for idx in known_indices if idx < 0 or idx >= card_count]
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"known_indices contains invalid card indexes: {invalid}",
        )

    return sorted(set(known_indices))


# ---------- routes ----------

@router.post("/flashcards/generate", response_model=FlashcardSetResponse)
async def generate_flashcards(
    request: Request,
    body: FlashcardGenerateRequest,
    user=Depends(get_verified_user),
):
    if not body.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    # OpenWebUI's /api/chat/completions endpoint runs `Depends(get_verified_user)`,
    # so the caller's bearer token must be re-presented on the inner loopback call.
    # We forward only the Authorization header (no cookies, no body rewrite) and the
    # target is the same process, so the token never leaves this backend.
    auth_header = request.headers.get("authorization", "")
    # OpenWebUI is mounted at "/" of this same FastAPI process (see main.py),
    # so /api/chat/completions is always reached via loopback. PORT is the only
    # part that varies between environments — host stays localhost by design.
    port = int(os.environ.get("PORT", "8080"))

    payload = {
        "model": body.model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + body.messages,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                f"http://localhost:{port}/api/chat/completions",
                json=payload,
                headers={"Authorization": auth_header, "Content-Type": "application/json"},
            )
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        log.error(f"LLM call failed: {e.response.status_code} {e.response.text}")
        raise HTTPException(status_code=502, detail="LLM call failed")
    except Exception as e:
        log.error(f"LLM call error: {e}")
        raise HTTPException(status_code=502, detail="Could not reach LLM")

    try:
        response_json = r.json()
        choices = response_json.get("choices")
        if not isinstance(choices, list) or len(choices) == 0:
            raise ValueError("LLM response contains no completion choices")

        content = choices[0].get("message", {}).get("content")
        if not isinstance(content, str):
            raise ValueError("LLM response missing message content")

        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        data = json.loads(content.strip())
        raw_cards = data.get("flashcards", [])
        if not raw_cards:
            raise ValueError("empty flashcards list")
        raw_cards = _validate_flashcards(raw_cards)
    except Exception as e:
        log.error(f"Failed to parse LLM response: {e}")
        raise HTTPException(status_code=500, detail="Could not parse flashcards from LLM response")

    db = SessionLocal()
    try:
        source_label = body.source_label
        if body.support_id:
            support = _validate_support_ownership(db, body.support_id, user.id)
            source_label = f"Support: {support.subject}"

        fs = FlashcardSet(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title=body.title,
            source_label=source_label,
            support_id=body.support_id,
            model_used=body.model,
            cards=raw_cards,
            known_indices=[],
            created_at=datetime.utcnow(),
        )
        db.add(fs)
        db.commit()
        db.refresh(fs)
        return _to_response(fs)
    finally:
        db.close()


@router.get("/flashcards/sets", response_model=list[FlashcardSetResponse])
async def list_flashcard_sets(user=Depends(get_verified_user)):
    db = SessionLocal()
    try:
        sets = (
            db.query(FlashcardSet)
            .filter(FlashcardSet.user_id == user.id)
            .order_by(FlashcardSet.created_at.desc())
            .all()
        )
        return [_to_response(fs) for fs in sets]
    finally:
        db.close()


@router.get("/flashcards/sets/{set_id}", response_model=FlashcardSetResponse)
async def get_flashcard_set(set_id: str, user=Depends(get_verified_user)):
    db = SessionLocal()
    try:
        return _to_response(_get_set_or_404(db, set_id, user.id))
    finally:
        db.close()


@router.patch("/flashcards/sets/{set_id}/progress", response_model=FlashcardSetResponse)
async def update_progress(
    set_id: str,
    body: ProgressUpdateRequest,
    user=Depends(get_verified_user),
):
    db = SessionLocal()
    try:
        fs = _get_set_or_404(db, set_id, user.id)
        fs.known_indices = _normalize_known_indices(body.known_indices, len(fs.cards or []))
        fs.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(fs)
        return _to_response(fs)
    finally:
        db.close()


@router.delete("/flashcards/sets/{set_id}", status_code=204)
async def delete_flashcard_set(set_id: str, user=Depends(get_verified_user)):
    db = SessionLocal()
    try:
        fs = _get_set_or_404(db, set_id, user.id)
        db.delete(fs)
        db.commit()
    finally:
        db.close()
