"""Adaptive-tutoring prompt injection from live engagement signals.

it turns the latest cached/estimated per-modality signals into a
short natural-language directive that is injected into the chat message, so the tutor adapts its teaching to how engaged the learner is.
it reads only the in-RAM plus the text estimate, so it is cheap enough to run on every chat completion.
"""

from typing import Any, Dict, List, Optional

from .cache import (
    latest_video_scores,
    latest_audio_scores,
    most_recent_text_session,
)
from .text_core import compute_text_score_estimate
from .fusion import compute_overall_score

# Guidance the tutor should follow at each engagement level.
_LEVEL_GUIDANCE = {
    "LOW": (
        "The learner appears disengaged. Slow down and simplify. Use a concrete "
        "example or analogy, break the idea into smaller steps, and ask one short, "
        "easy check-in question to draw them back in. Keep an encouraging, warm tone."
    ),
    "MEDIUM": (
        "The learner is moderately engaged. Keep momentum: check understanding with "
        "a quick question before moving on, and offer a concrete example if the "
        "concept is abstract."
    ),
    "HIGH": (
        "The learner is highly engaged. You can go a little deeper or faster, "
        "introduce a challenge or follow-up question, and build on their momentum."
    ),
}


# Thresholds recalibrated from the real score distribution (tertiles); kept in
# sync with service._level. See manual_check/RESULTATS_ANALYSE.md (§7).
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


def _fmt(score: Optional[float]) -> str:
    return "—" if score is None else f"{score:.2f}"


def build_engagement_directive(user_id: str) -> Optional[str]:
    """Build the adaptive-tutoring directive for a learner, or ``None``.

    Returns ``None`` when there is no usable engagement signal yet (no webcam,
    no audio and no message history) — in that case nothing is injected and the
    tutor behaves exactly as before.
    """
    # Read text from the user's most recent session so the text signal feeds the
    # live directive (text caches are session-scoped). Video/audio are per-user.
    session_id = most_recent_text_session(user_id)
    text_metrics = compute_text_score_estimate(user_id, session_id=session_id)
    scores = {
        "text": text_metrics.get("text_score"),
        "audio": latest_audio_scores.get(user_id),
        "video": latest_video_scores.get(user_id),
    }
    overall = compute_overall_score(scores)
    level = _level(overall)
    if level is None:
        return None

    return (
        "[Learner engagement — live signal, do not mention this to the learner]\n"
        f"Current engagement: {level} "
        f"(overall {_fmt(overall)}; "
        f"text {_fmt(scores['text'])}, "
        f"audio {_fmt(scores['audio'])}, "
        f"video {_fmt(scores['video'])}).\n"
        f"{_LEVEL_GUIDANCE[level]}"
    )


def inject_engagement_directive(
    messages: List[Dict[str, Any]], user_id: str
) -> List[Dict[str, Any]]:
    """Return ``messages`` with the engagement directive merged into ``system``.
    If a system message exists, the
    directive is appended to it; otherwise a new system message is prepended.
    """
    if not isinstance(messages, list):
        return messages

    directive = build_engagement_directive(user_id)
    if not directive:
        return messages

    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "system":
            existing = msg.get("content") or ""
            msg["content"] = f"{existing}\n\n{directive}" if existing else directive
            return messages

    # No system message present — prepend one.
    return [{"role": "system", "content": directive}, *messages]
