"""In-memory cache for engagement scores.

Lightweight runtime cache used to store recent per-user signals so we can
compute temporal/textual metrics without hitting the DB for every event.
"""

import time

# Entries idle for longer than this (seconds) are evicted to bound memory.
DEFAULT_TTL = 3600
# Minimum gap between opportunistic eviction passes.
EVICT_INTERVAL = 300
# Smoothing factor for live modality scores (higher = more responsive).
DEFAULT_EMA_ALPHA = 0.4
# How recently the webcam must have produced a score for it to be attached to a
# chat/voice message (seconds). Prevents saving a long-stale video score.
VIDEO_FRESH_WINDOW = 60

# Live per-user modality scores — keyed by ``user_id``.
latest_video_scores = {}
latest_audio_scores = {}

# Text tracking — keyed by scope key ``"<session_id>|<user_id>"``:
# last message timestamp (epoch seconds), message count, recent history.
latest_text_ts = {}
latest_text_count = {}
latest_text_history = {}

# key -> last activity epoch; drives TTL eviction across every store.
_last_seen = {}
_last_evict = [0.0]

_ALL_STORES = (
    latest_video_scores,
    latest_audio_scores,
    latest_text_ts,
    latest_text_count,
    latest_text_history,
)


# Key helpers


def scope_key(user_id: str, session_id=None) -> str:
    """Build the per-(session, user) key used by the text caches."""
    return f"{session_id or 'global'}|{user_id}"


def get_recent_video_score(user_id: str, max_age: int = VIDEO_FRESH_WINDOW, now=None):
    """Return the user's cached webcam score if it is recent enough to attach."""
    score = latest_video_scores.get(user_id)
    if score is None:
        return None
    seen = _last_seen.get(user_id)
    if seen is not None:
        now = now if now is not None else time.time()
        if now - seen > max_age:
            return None
    return score


def session_message_total(session_id=None) -> int:
    """Total messages recorded across all users in a session.

    Used so a user's participation rate is measured within their own session
    rather than against every user on the server.
    """
    prefix = f"{session_id or 'global'}|"
    return sum(c for k, c in latest_text_count.items() if k.startswith(prefix))


def most_recent_text_session(user_id: str):
    """Session id of the user's most recent text activity, or ``None``.

    Text caches are keyed ``"<session>|<user>"``; this finds the session whose
    entry for this user has the latest timestamp, so live consumers (e.g. the
    adaptive prompt) can read the user's current text engagement without knowing
    the session id up front.
    """
    suffix = f"|{user_id}"
    best_session = None
    best_ts = -1
    for key, ts in latest_text_ts.items():
        if key.endswith(suffix) and ts > best_ts:
            best_ts = ts
            best_session = key[: -len(suffix)]
    return best_session


# Eviction


def touch(key: str, now=None) -> None:
    """Mark a cache key as active so it survives the next eviction pass."""
    _last_seen[key] = now if now is not None else time.time()


def evict_stale(ttl: int = DEFAULT_TTL, now=None) -> int:
    """Drop entries idle longer than ``ttl`` seconds from every store."""
    now = now if now is not None else time.time()
    stale = [k for k, seen in _last_seen.items() if now - seen > ttl]
    for k in stale:
        for store in _ALL_STORES:
            store.pop(k, None)
        _last_seen.pop(k, None)
    return len(stale)


def maybe_evict(
    now=None, interval: int = EVICT_INTERVAL, ttl: int = DEFAULT_TTL
) -> None:
    """Run :func:`evict_stale`, but at most once per ``interval`` seconds."""
    now = now if now is not None else time.time()
    if now - _last_evict[0] >= interval:
        _last_evict[0] = now
        evict_stale(ttl=ttl, now=now)


# Smoothing


def decay_score(store: dict, key: str, factor: float = 0.55, floor: float = 0.05):
    """Multiply the cached score toward ``floor`` and return it.

    Used when the webcam sends a frame but no face is found: instead of
    freezing the last (often high) value, the score decays so that sustained
    absence/looking-away drives it down within a few frames.
    """
    prev = store.get(key)
    if prev is None:
        return None
    new = round(max(floor, prev * factor), 3)
    store[key] = new
    touch(key)
    return new


def ema_update(store: dict, key: str, value, alpha: float = DEFAULT_EMA_ALPHA):
    """Exponentially smooth ``value`` into ``store[key]`` and return the result.

    The first observation seeds the average directly; subsequent ones blend
    ``alpha`` of the new value with ``1 - alpha`` of the running estimate.
    A ``None`` value leaves the stored estimate untouched.
    """
    if value is None:
        return store.get(key)
    prev = store.get(key)
    smoothed = value if prev is None else round(alpha * value + (1 - alpha) * prev, 3)
    store[key] = smoothed
    touch(key)
    maybe_evict()
    return smoothed
