"""Unit tests for the sliding-window rate limiter (pure logic).

The middleware itself is disabled under DEBUG (and the suite runs with DEBUG=true), so we
test the counting logic directly with an injected clock — no app/server needed.
"""

import jwt as _jwt

from config import settings
from gateway.http.rate_limit import SlidingWindowLimiter, _client_key


def test_allows_up_to_the_limit_then_blocks():
    limiter = SlidingWindowLimiter(max_requests=3, window_seconds=60)
    # First three within the window are allowed.
    assert limiter.allow("k", now=0.0) is True
    assert limiter.allow("k", now=1.0) is True
    assert limiter.allow("k", now=2.0) is True
    # Fourth in the same window is blocked.
    assert limiter.allow("k", now=3.0) is False


def test_window_slides_and_frees_capacity():
    limiter = SlidingWindowLimiter(max_requests=2, window_seconds=60)
    assert limiter.allow("k", now=0.0) is True
    assert limiter.allow("k", now=10.0) is True
    assert limiter.allow("k", now=20.0) is False  # still within 60s of the first two
    # Once the first hit (t=0) ages out of the 60s window, capacity frees up.
    assert limiter.allow("k", now=61.0) is True


def test_keys_are_independent():
    limiter = SlidingWindowLimiter(max_requests=1, window_seconds=60)
    assert limiter.allow("user-a", now=0.0) is True
    assert limiter.allow("user-a", now=1.0) is False
    # A different caller has its own budget.
    assert limiter.allow("user-b", now=1.0) is True


# ── per-caller key derivation (regression: shared-bucket bug) ────────────────


class _FakeRequest:
    """Minimal stand-in for starlette Request: headers, cookies, client.host."""

    class _Client:
        host = "10.0.0.9"

    def __init__(self, *, bearer=None, cookie=None):
        self.headers = {"authorization": f"Bearer {bearer}"} if bearer else {}
        # The limiter reads the session cookie by AUTH_COOKIE_NAME (default "token")
        # so it keeps working once cookie auth lands; bearer-only on this branch.
        cookie_name = getattr(settings, "AUTH_COOKIE_NAME", "token")
        self.cookies = {cookie_name: cookie} if cookie else {}
        self.client = self._Client()


def _token(sub):
    return _jwt.encode({"sub": sub}, settings.JWT_SECRET_KEY, algorithm="HS256")


def test_client_key_is_distinct_per_user():
    """Regression: keying on a JWT prefix aliased everyone into one bucket because
    the header is identical across tokens. The key must track the `sub` claim."""
    a = _client_key(_FakeRequest(bearer=_token("user-a")))
    b = _client_key(_FakeRequest(bearer=_token("user-b")))
    assert a != b
    assert a == "user:user-a"
    # Same user via the cookie channel keys identically to the bearer channel.
    assert _client_key(_FakeRequest(cookie=_token("user-a"))) == a


def test_client_key_falls_back_to_ip_without_token():
    assert _client_key(_FakeRequest()) == "ip:10.0.0.9"


def test_client_key_hashes_undecodable_token_distinctly():
    a = _client_key(_FakeRequest(bearer="garbage-token-A"))
    b = _client_key(_FakeRequest(bearer="garbage-token-B"))
    assert a != b and a.startswith("tok:")
