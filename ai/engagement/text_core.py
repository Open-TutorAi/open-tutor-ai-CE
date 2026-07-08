import time
from typing import Dict, Any, Optional
from .cache import (
    latest_text_ts,
    latest_text_count,
    latest_text_history,
    scope_key,
    session_message_total,
    touch,
    maybe_evict,
)


def compute_text_metrics(
    user_id: str, message: str, session_id: Optional[str] = None
) -> Dict[str, Any]:
    """Compute richer text engagement metrics and update runtime cache.

    Returns a dict with multiple diagnostics useful for UI and fusion:
    - chat_score: float (0.0-1.0)
    - words: int
    - message_freq_score: float
    - participation_count: int
    - participation_rate: float (user messages / total messages)
    - continuity_score: float (based on interval to last user message)
    - activity_score: float (messages in last 5 minutes)
    - lexical_diversity: float (unique words / total words)
    - question_score: float (presence of questions in the message)
    """
    now = int(time.time())
    key = scope_key(user_id, session_id)
    tokens = message.split() if message else []
    words = len(tokens)

    if words > 0:
        unique_words = len({t.lower().strip(".,!?;:\"'") for t in tokens})
        ttr = unique_words / words

        lexical_diversity = round(ttr * min(1.0, words / 15.0), 3)
    else:
        lexical_diversity = 0.0

    # Question presence:
    question_words = (
        "what",
        "why",
        "how",
        "when",
        "where",
        "who",
        "which",
        "whose",
        "can",
        "could",
        "would",
        "should",
        "is",
        "are",
        "do",
        "does",
    )
    lowered = message.lower() if message else ""
    has_question_mark = "?" in lowered
    starts_with_qword = any(
        lowered.lstrip().startswith(qw + " ") for qw in question_words
    )
    if has_question_mark and starts_with_qword:
        question_score = 1.0
    elif has_question_mark or starts_with_qword:
        question_score = 0.7
    else:
        question_score = 0.2

    # Response length score:
    if words >= 120:
        length_score = 0.95
    elif words >= 60:
        length_score = 0.9
    elif words >= 25:
        length_score = 0.8
    elif words >= 12:
        length_score = 0.65
    elif words >= 5:
        length_score = 0.4
    else:
        length_score = 0.1

    # Message frequency & continuity:
    prev_ts = latest_text_ts.get(key)
    message_count = latest_text_count.get(key, 0)

    if prev_ts is None:
        freq_score = 0.6
        continuity_score = 0.5
    else:
        interval = max(1, now - prev_ts)
        if interval <= 30:
            freq_score = 0.95
            continuity_score = 1.0
        elif interval <= 120:
            freq_score = 0.75
            continuity_score = 0.85
        elif interval <= 300:
            freq_score = 0.5
            continuity_score = 0.6
        else:
            freq_score = 0.2
            continuity_score = 0.25

    # Update history for activity computation
    hist = latest_text_history.setdefault(key, [])
    hist.append(now)
    if len(hist) > 50:
        del hist[:-50]

    # Activity score:
    recent_count = sum(1 for t in hist if now - t <= 300)
    activity_score = min(1.0, recent_count / 5.0)

    # Participation rate:
    total_msgs = session_message_total(session_id) + 1  # +1 for this message
    participation_rate = (message_count + 1) / max(1, total_msgs)

    # Update caches
    latest_text_ts[key] = now
    latest_text_count[key] = message_count + 1
    touch(key, now)
    maybe_evict(now)

    # Combine signals into chat_score. Content (length, lexical diversity,
    # questions) weighs 0.60 and rhythm (freq, activity, continuity,
    # participation) 0.40, so deep engagement reaches HIGH without depending on
    # rapid-fire pacing.
    chat_score = (
        0.25 * length_score
        + 0.20 * lexical_diversity
        + 0.15 * question_score
        + 0.10 * freq_score
        + 0.10 * activity_score
        + 0.10 * continuity_score
        + 0.10 * participation_rate
    )
    chat_score = round(max(0.0, min(1.0, chat_score)), 3)

    return {
        "chat_score": chat_score,
        "words": words,
        "message_freq_score": freq_score,
        "participation_count": latest_text_count[key],
        "participation_rate": round(participation_rate, 3),
        "continuity_score": round(continuity_score, 3),
        "activity_score": round(activity_score, 3),
        "lexical_diversity": lexical_diversity,
        "question_score": question_score,
    }


def compute_text_score_estimate(
    user_id: str, session_id: Optional[str] = None
) -> Dict[str, Any]:
    """Estimate a text engagement score for a user using cached state only."""
    now = int(time.time())
    key = scope_key(user_id, session_id)
    message_count = latest_text_count.get(key, 0)
    prev_ts = latest_text_ts.get(key)
    hist = latest_text_history.get(key, [])

    # Heuristics similar to compute_text_metrics but without a new message
    if message_count == 0:
        return {"text_score": None, "message_count": 0}

    # participation rate (scoped to this session)
    total_msgs = session_message_total(session_id)
    participation_rate = message_count / max(1, total_msgs)

    # activity (last 5 minutes)
    recent_count = sum(1 for t in hist if now - t <= 300)
    activity_score = min(1.0, recent_count / 5.0)

    # continuity
    if prev_ts is None:
        continuity_score = 0.5
    else:
        interval = max(1, now - prev_ts)
        if interval <= 30:
            continuity_score = 1.0
        elif interval <= 120:
            continuity_score = 0.85
        elif interval <= 300:
            continuity_score = 0.6
        else:
            continuity_score = 0.25

    # crude length and freq proxies
    length_score = 0.6
    freq_score = 0.6

    text_score = (
        0.25 * length_score
        + 0.20 * freq_score
        + 0.20 * activity_score
        + 0.20 * continuity_score
        + 0.15 * participation_rate
    )
    return {
        "text_score": round(max(0.0, min(1.0, text_score)), 3),
        "message_count": message_count,
        "participation_rate": round(participation_rate, 3),
        "activity_score": round(activity_score, 3),
        "continuity_score": round(continuity_score, 3),
    }
