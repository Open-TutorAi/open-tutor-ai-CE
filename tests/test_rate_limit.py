"""Unit tests for the sliding-window rate limiter (pure logic).

The middleware itself is disabled under DEBUG (and the suite runs with DEBUG=true), so we
test the counting logic directly with an injected clock — no app/server needed.
"""

from gateway.http.rate_limit import SlidingWindowLimiter


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
