import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.requests import Request as StarletteRequest

from open_webui.internal.db import get_session as get_db
from open_webui.utils.auth import get_verified_user
from open_webui.utils.chat import generate_chat_completion
from open_webui.main import app as webui_app
from open_tutorai.models.database import FlashcardSet, Support

log = logging.getLogger(__name__)
log.setLevel("INFO")

router = APIRouter()

MIN_CARDS = 3
MAX_CARDS = 10
DEFAULT_CARD_COUNT = 8

# Accepted difficulty hints. Keep this list small and stable — the prompt
# builder injects the chosen value verbatim, so any new entry should be a
# short phrase the LLM can interpret without further explanation.
ALLOWED_DIFFICULTIES = {"beginner", "intermediate", "advanced"}


def _build_system_prompt(
    card_count: int,
    language: Optional[str],
    difficulty: Optional[str],
) -> str:
    lines = [
        "You are an educational assistant. Given a tutoring conversation or lesson text, extract the most important concepts and return ONLY a valid JSON object in this exact format, with no extra text before or after:",
        '{"flashcards": [{"question": "...", "answer": "..."}, ...]}',
        "Rules:",
        f"- Produce around {card_count} flashcards (minimum {MIN_CARDS}, maximum {MAX_CARDS}).",
        "- Cover key questions, definitions, and important notions.",
        "- Keep answers concise (1–3 sentences max).",
    ]
    if language:
        lines.append(f"- Write every question and answer in {language}.")
    if difficulty:
        lines.append(
            f"- Target a {difficulty} learner: adjust vocabulary, depth and the level of prior knowledge assumed accordingly."
        )
    lines.append("- Output ONLY the JSON object, nothing else.")
    return "\n".join(lines)


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
    card_count: Optional[int] = None
    language: Optional[str] = None
    difficulty: Optional[str] = None


class ProgressUpdateRequest(BaseModel):
    known_indices: list[int]


class FlashcardSetUpdateRequest(BaseModel):
    cards: list[dict]
    # Caller is responsible for re-mapping known_indices to the new card
    # positions — server has no way to track identity across a positional
    # array. Omit to reset progress to empty.
    known_indices: Optional[list[int]] = None
    title: Optional[str] = None


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


def _inner_webui_request(request: Request) -> Request:
    """Returns a Request whose `.app` resolves to the mounted OpenWebUI app.

    `open_webui.utils.chat.generate_chat_completion` reads
    `request.app.state.MODELS` to dispatch to the right backend (Ollama,
    OpenAI, …). Our router runs on the outer TutorAI app, whose `state`
    has no MODELS — so we hand the function a Request bound to the inner
    app instead. State (metadata, direct, etc.) is preserved through the
    shared scope dict."""
    scope = dict(request.scope)
    scope["app"] = webui_app
    return StarletteRequest(scope, receive=request.receive)


def _content_from_completion(response: Any) -> str:
    """Extracts the assistant message content from whatever shape
    `generate_chat_completion` returned. Ollama and OpenAI paths both
    converge on the OpenAI chat-completion dict shape, but the OpenAI path
    can wrap it in a Starlette Response — handle both."""
    if hasattr(response, "body"):
        # Starlette JSONResponse / Response — unwrap to dict.
        response = json.loads(response.body)
    if not isinstance(response, dict):
        raise ValueError(
            f"unexpected completion response type: {type(response).__name__}"
        )
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("completion response contains no choices")
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str):
        raise ValueError("completion response missing message content")
    return content


# Matches an opening triple-backtick fence with an optional language tag, e.g.
# ```json\n  or  ```JSON\n  or just  ```\n
_FENCE_RE = re.compile(r"^```[a-zA-Z]*\s*", flags=re.MULTILINE)

# Reasoning-model wrappers (DeepSeek-R1, Qwen-QwQ, etc.). The actual answer
# follows the closing tag.
_REASONING_RE = re.compile(
    r"<\s*(think|reasoning|thought|reflection)\s*>.*?<\s*/\s*\1\s*>",
    flags=re.IGNORECASE | re.DOTALL,
)

# Trailing comma before } or ] — common LLM mistake, makes json.loads fail.
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")


def _strip_reasoning(content: str) -> str:
    """Removes <think>…</think>-style reasoning blocks emitted by reasoning
    models before the actual answer."""
    return _REASONING_RE.sub("", content)


def _repair_json(s: str) -> str:
    """Conservative repairs for common LLM JSON mistakes. Currently just
    strips trailing commas before closing brackets — anything more
    invasive risks corrupting valid output."""
    return _TRAILING_COMMA_RE.sub(r"\1", s)


def _strip_fences(content: str) -> str:
    """Removes leading/trailing markdown code fences. Tolerates language tags
    and stray text outside the fences."""
    s = content.strip()
    if "```" not in s:
        return s
    # Drop everything up to and including the first opening fence,
    # then drop everything from the next ``` onward.
    parts = s.split("```")
    # parts looks like [prose_before, "json\n{...}\n", prose_after, ...]
    # Pick the largest middle chunk that contains a "{" or "[" — that's the JSON.
    middle = [p for p in parts[1:-1] if "{" in p or "[" in p] or parts[1:2]
    if not middle:
        return s
    chunk = max(middle, key=len)
    # If the chunk starts with a language tag like "json\n", strip it.
    chunk = re.sub(r"^[a-zA-Z]+\s*\n", "", chunk, count=1)
    return chunk.strip()


def _extract_balanced_json(content: str) -> Optional[str]:
    """Scans `content` for the first balanced JSON object or array and returns
    the substring, or None if no balanced delimiter pair is found. Handles
    strings (so braces inside string literals don't count) but not escaped
    quotes inside strings — good enough for LLM output, which rarely
    contains them in flashcard text."""
    start_idx = None
    opener = None
    closer = None
    depth = 0
    in_string = False
    for i, ch in enumerate(content):
        if in_string:
            if ch == "\\":
                continue  # next char is escaped; skip-by-loop is fine since we don't read it
            if ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if start_idx is None:
            if ch in "{[":
                start_idx = i
                opener = ch
                closer = "}" if ch == "{" else "]"
                depth = 1
            continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return content[start_idx : i + 1]
    return None


def _parse_llm_flashcards(content: str) -> list:
    """Best-effort extraction of a flashcards list from raw LLM output.
    Accepts: bare JSON, fenced JSON (with or without language tag), JSON
    embedded in prose, top-level {"flashcards": [...]} object, or a bare
    array of card objects. Tolerates reasoning-model wrappers (<think>…)
    and trailing commas. Raises ValueError on irrecoverable failure."""
    cleaned = _strip_reasoning(content)
    unfenced = _strip_fences(cleaned)

    # Build a list of candidate JSON strings to try, in order of preference.
    candidates: list[str] = [unfenced]
    extracted = _extract_balanced_json(unfenced)
    if extracted and extracted != unfenced:
        candidates.append(extracted)
    # Also try repaired versions for each candidate (trailing-comma fix, etc.).
    candidates += [_repair_json(c) for c in list(candidates)]

    last_err: Optional[Exception] = None
    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError as e:
            last_err = e
            continue

        if isinstance(data, dict):
            cards = data.get("flashcards")
            if isinstance(cards, list):
                return cards
            # Some models return a single dict with question/answer keys.
            if "question" in data and "answer" in data:
                return [data]
            last_err = ValueError(
                "JSON object did not contain a 'flashcards' array"
            )
            continue
        if isinstance(data, list):
            return data
        last_err = ValueError(f"unexpected JSON top-level type: {type(data).__name__}")

    raise ValueError(f"could not extract flashcards JSON: {last_err}")


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
    fs = (
        db.query(FlashcardSet)
        .filter(
            FlashcardSet.id == set_id,
            FlashcardSet.user_id == user_id,
        )
        .first()
    )
    if not fs:
        raise HTTPException(status_code=404, detail="Flashcard set not found")
    return fs


def _validate_support_ownership(db, support_id: str, user_id: str) -> Support:
    support = (
        db.query(Support)
        .filter(
            Support.id == support_id,
            Support.user_id == user_id,
        )
        .first()
    )
    if not support:
        raise HTTPException(
            status_code=400,
            detail="support_id is invalid or does not belong to the current user",
        )
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
    db: Session = Depends(get_db),
    user=Depends(get_verified_user),
):
    if not body.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    card_count = body.card_count if body.card_count is not None else DEFAULT_CARD_COUNT
    if card_count < MIN_CARDS or card_count > MAX_CARDS:
        raise HTTPException(
            status_code=422,
            detail=f"card_count must be between {MIN_CARDS} and {MAX_CARDS}",
        )

    language = body.language.strip() if body.language else None
    if language and len(language) > 50:
        raise HTTPException(status_code=422, detail="language is too long")

    difficulty = body.difficulty.strip().lower() if body.difficulty else None
    if difficulty is not None and difficulty not in ALLOWED_DIFFICULTIES:
        raise HTTPException(
            status_code=422,
            detail=f"difficulty must be one of {sorted(ALLOWED_DIFFICULTIES)}",
        )

    system_prompt = _build_system_prompt(card_count, language, difficulty)

    form_data = {
        "model": body.model,
        "messages": [{"role": "system", "content": system_prompt}] + body.messages,
        "stream": False,
        # Force JSON-only output where the backend supports it. Two keys to
        # cover both routes: `response_format` is the OpenAI standard,
        # `format: "json"` is Ollama's native flag. Models that don't
        # recognize either key just ignore it, so this is safe to always
        # include — the lenient parser below remains the safety net.
        "response_format": {"type": "json_object"},
        "format": "json",
    }

    # OpenWebUI is mounted on this same process, so we call its completion
    # function directly instead of going back out over HTTP. Token forwarding
    # falls out for free (the request still carries the caller's auth state),
    # and exceptions propagate as real Python stack traces.
    try:
        completion = await generate_chat_completion(
            _inner_webui_request(request), form_data, user
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error("LLM call failed: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail="LLM call failed")

    raw_content: Optional[str] = None
    try:
        raw_content = _content_from_completion(completion)
        raw_cards = _parse_llm_flashcards(raw_content)
        if not raw_cards:
            raise ValueError("empty flashcards list")
    except Exception as e:
        # Log a truncated copy of the LLM output so the failure mode is
        # diagnosable (model returned prose, wrong shape, hit token limit, …)
        # without flooding the logs on huge responses.
        snippet = (raw_content or "<no content>")[:2000]
        log.error(
            "Failed to parse LLM response: %s\n"
            "----- LLM content (truncated to 2000 chars) -----\n%s\n-----",
            e,
            snippet,
        )
        raise HTTPException(
            status_code=500, detail="Could not parse flashcards from LLM response"
        )

    try:
        raw_cards = _validate_flashcards(raw_cards)
    except ValueError as e:
        # Model returned a JSON list of the wrong shape/size — that's a 422
        # (validation), not a 500 (parser failure). Caller can retry with a
        # different count / model.
        raise HTTPException(status_code=422, detail=str(e))

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


@router.get("/flashcards/sets", response_model=list[FlashcardSetResponse])
async def list_flashcard_sets(
    db: Session = Depends(get_db),
    user=Depends(get_verified_user),
):
    sets = (
        db.query(FlashcardSet)
        .filter(FlashcardSet.user_id == user.id)
        .order_by(FlashcardSet.created_at.desc())
        .all()
    )
    return [_to_response(fs) for fs in sets]


@router.get("/flashcards/sets/{set_id}", response_model=FlashcardSetResponse)
async def get_flashcard_set(
    set_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_verified_user),
):
    return _to_response(_get_set_or_404(db, set_id, user.id))


@router.patch("/flashcards/sets/{set_id}/progress", response_model=FlashcardSetResponse)
async def update_progress(
    set_id: str,
    body: ProgressUpdateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_verified_user),
):
    fs = _get_set_or_404(db, set_id, user.id)
    fs.known_indices = _normalize_known_indices(
        body.known_indices, len(fs.cards or [])
    )
    fs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(fs)
    return _to_response(fs)


@router.patch("/flashcards/sets/{set_id}", response_model=FlashcardSetResponse)
async def update_flashcard_set(
    set_id: str,
    body: FlashcardSetUpdateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_verified_user),
):
    try:
        validated_cards = _validate_flashcards(body.cards)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    fs = _get_set_or_404(db, set_id, user.id)
    fs.cards = validated_cards
    fs.known_indices = _normalize_known_indices(
        body.known_indices or [], len(validated_cards)
    )
    if body.title is not None:
        title = body.title.strip()
        if not title:
            raise HTTPException(status_code=422, detail="title must not be empty")
        fs.title = title[:200]
    fs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(fs)
    return _to_response(fs)


@router.delete("/flashcards/sets/{set_id}", status_code=204)
async def delete_flashcard_set(
    set_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_verified_user),
):
    fs = _get_set_or_404(db, set_id, user.id)
    db.delete(fs)
    db.commit()
