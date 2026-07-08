# tests/test_engagement.py
"""Engagement tracking — service math, persistence scoping, HTTP + chat hook."""

from ai.engagement.fusion import compute_overall_score
from ai.engagement.service import EngagementService


def _token(client, email="learner@t.com"):
    r = client.post(
        "/auths/signup",
        json={"email": email, "name": "L", "password": "pass1234!"},
    )
    return r.json()["token"]


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


# ── Fusion math ───────────────────────────────────────────────────────────────


def test_fusion_full_weights():
    assert compute_overall_score({"text": 1.0, "audio": 1.0, "video": 1.0}) == 1.0


def test_fusion_redistributes_missing_modalities():
    # text=0.5 (w .4), video=1.0 (w .3), audio missing → (0.2 + 0.3) / 0.7
    val = compute_overall_score({"text": 0.5, "audio": None, "video": 1.0})
    assert abs(val - 0.714) < 0.01


def test_fusion_none_when_no_signals():
    assert compute_overall_score({"text": None, "audio": None, "video": None}) is None


# ── Service: compute, persist, scope ──────────────────────────────────────────


def test_record_text_persists_and_fuses(engagement_db):
    svc = EngagementService(engagement_db)
    row = svc.record_text("u1", "s1", "this is a reasonably long text answer")
    assert row["text_score"] is not None
    assert row["fusion_score"] is not None
    assert row["engagement_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert row["user_id"] == "u1" and row["session_id"] == "s1"


def test_metrics_scoped_to_user(engagement_db):
    svc = EngagementService(engagement_db)
    svc.record_text("u1", "s1", "hello world from user one")
    assert svc.summary("u1", "s1")["count"] == 1
    # A different user must not see u1's rows.
    assert svc.summary("u2", "s1")["count"] == 0


def test_summary_reports_averages(engagement_db):
    svc = EngagementService(engagement_db)
    svc.record_text("u1", "s1", "first message here")
    svc.record_text("u1", "s1", "second message here too")
    summary = svc.summary("u1", "s1")
    assert summary["count"] == 2
    assert summary["averages"]["text"] is not None


def test_record_text_accepts_explicit_video_score(engagement_db):
    svc = EngagementService(engagement_db)
    # The client passes the live webcam score it is displaying at send time.
    row = svc.record_text("u1", "s1", "a message with the camera on", video_score=0.72)
    assert row["video_score"] == 0.72


def test_voice_message_attaches_cached_video_score(engagement_db):
    from ai.engagement import cache

    svc = EngagementService(engagement_db)
    cache.latest_video_scores.pop("uvoice", None)
    cache._last_seen.pop("uvoice", None)

    # Webcam scored the user's face → cached. A voice send with no explicit
    # video_score must still attach that recent cached score.
    cache.latest_video_scores["uvoice"] = 0.77
    cache.touch("uvoice")
    row = svc.record_audio("uvoice", "s1", audio_base64="", message="spoken turn")
    assert row["video_score"] == 0.77

    # A stale cached score (older than the freshness window) is not attached.
    import time as _t

    cache._last_seen["uvoice"] = _t.time() - 600
    row2 = svc.record_audio("uvoice", "s1", audio_base64="", message="later turn")
    assert row2["video_score"] is None
    cache.latest_video_scores.pop("uvoice", None)
    cache._last_seen.pop("uvoice", None)


def test_video_scored_live_but_saved_only_on_send(engagement_db):
    from ai.engagement import cache

    svc = EngagementService(engagement_db)
    cache.latest_video_scores.pop("uv", None)

    # Scoring a webcam frame caches it for the live display but does NOT persist.
    svc.score_video("uv", "s1", None)
    assert svc.summary("uv", "s1")["count"] == 0

    # On send, the message captures the current cached webcam score.
    cache.latest_video_scores["uv"] = 0.8
    row = svc.record_text("uv", "s1", "sending a message now")
    assert row["video_score"] == 0.8
    assert svc.summary("uv", "s1")["count"] == 1  # only the send is saved
    cache.latest_video_scores.pop("uv", None)


# ── HTTP endpoints ────────────────────────────────────────────────────────────


def test_chat_endpoint_returns_score(client):
    token = _token(client, "chatscore@t.com")
    r = client.post(
        "/api/v1/engagement/chat",
        json={"message": "hello there tutor", "session_id": "s1"},
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json()["data"]["fusion_score"] is not None


def test_summary_and_score_endpoints(client):
    token = _token(client, "summary@t.com")
    client.post(
        "/api/v1/engagement/chat",
        json={"message": "a message to record", "session_id": "sX"},
        headers=_auth(token),
    )
    summary = client.get("/api/v1/engagement/session/sX/summary", headers=_auth(token))
    assert summary.status_code == 200 and summary.json()["count"] >= 1

    score = client.get("/api/v1/engagement/session/sX/score", headers=_auth(token))
    assert score.status_code == 200
    assert score.json()["overall_score"] is not None


def test_video_endpoint_handles_invalid_frame(client):
    token = _token(client, "video@t.com")
    r = client.post(
        "/api/v1/engagement/video",
        json={"frame": "@@not-a-real-frame@@", "session_id": "s1"},
        headers=_auth(token),
    )
    # No face / undecodable frame → score is None but the request still succeeds.
    assert r.status_code == 200
    assert r.json()["video_score"] is None
    # Webcam frames are not persisted — nothing is stored for this session.
    summary = client.get("/api/v1/engagement/session/s1/summary", headers=_auth(token))
    assert summary.json()["count"] == 0


def test_engagement_requires_auth(client):
    assert client.post(
        "/api/v1/engagement/chat", json={"message": "x"}
    ).status_code in (
        401,
        403,
    )
    assert client.get("/api/v1/engagement/session/s1/score").status_code in (401, 403)


def test_chat_endpoint_stores_passed_video_score(client):
    token = _token(client, "vidsend@t.com")
    r = client.post(
        "/api/v1/engagement/chat",
        json={
            "message": "sent with camera on",
            "session_id": "sv",
            "video_score": 0.66,
        },
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json()["data"]["video_score"] == 0.66
    summary = client.get(
        "/api/v1/engagement/session/sv/summary", headers=_auth(token)
    ).json()
    assert summary["rows"][0]["video_score"] == 0.66


# ── Adaptive prompt injection (close the loop with the tutor LLM) ──────────────


def test_directive_none_without_signal():
    from ai.engagement.prompt import build_engagement_directive

    # A fresh user with no cached signals yields no directive (no-op).
    assert build_engagement_directive("nobody-here") is None


def test_directive_reflects_level():
    from ai.engagement import cache
    from ai.engagement.prompt import build_engagement_directive

    cache.latest_video_scores["adapt-low"] = 0.1
    cache.latest_audio_scores["adapt-low"] = 0.1
    try:
        directive = build_engagement_directive("adapt-low")
        assert directive is not None
        assert "LOW" in directive
        assert "Slow down" in directive or "disengaged" in directive
    finally:
        cache.latest_video_scores.pop("adapt-low", None)
        cache.latest_audio_scores.pop("adapt-low", None)


def test_inject_appends_to_existing_system_message():
    from ai.engagement import cache
    from ai.engagement.prompt import inject_engagement_directive

    cache.latest_video_scores["inj"] = 0.9
    cache.latest_audio_scores["inj"] = 0.9
    try:
        messages = [
            {"role": "system", "content": "You are a tutor."},
            {"role": "user", "content": "Explain fractions."},
        ]
        out = inject_engagement_directive(messages, "inj")
        assert out[0]["role"] == "system"
        assert "You are a tutor." in out[0]["content"]
        assert "engagement" in out[0]["content"].lower()
        # User message is untouched.
        assert out[-1]["content"] == "Explain fractions."
    finally:
        cache.latest_video_scores.pop("inj", None)
        cache.latest_audio_scores.pop("inj", None)


def test_inject_prepends_system_when_absent():
    from ai.engagement import cache
    from ai.engagement.prompt import inject_engagement_directive

    cache.latest_video_scores["inj2"] = 0.5
    cache.latest_audio_scores["inj2"] = 0.5
    try:
        messages = [{"role": "user", "content": "Hi"}]
        out = inject_engagement_directive(messages, "inj2")
        assert out[0]["role"] == "system"
        assert len(out) == 2
    finally:
        cache.latest_video_scores.pop("inj2", None)
        cache.latest_audio_scores.pop("inj2", None)


def test_inject_noop_without_signal():
    from ai.engagement.prompt import inject_engagement_directive

    messages = [{"role": "user", "content": "Hi"}]
    out = inject_engagement_directive(messages, "no-signal-user")
    assert out == messages  # unchanged
