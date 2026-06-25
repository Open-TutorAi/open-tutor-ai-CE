"""Lightweight, dependency-free request rate limiting.

A small in-memory sliding-window limiter plus an ASGI middleware that applies it to
sensitive mutating endpoints (login, submit, grade, …). Kept deliberately simple — no
Redis/slowapi dependency — and **disabled in DEBUG** (dev + tests) so it never throttles
local work or the suite; it engages only in a real deployment (DEBUG=false).

For a multi-process / multi-host deployment this in-memory store is per-process; a shared
store (Redis) would be the next step, but this already bounds abuse on a single node.
"""

import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request
from fastapi.responses import JSONResponse


class SlidingWindowLimiter:
    """Allow at most `max_requests` per `window_seconds` for a given key."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        cutoff = now - self.window_seconds
        dq = self._hits[key]
        while dq and dq[0] <= cutoff:
            dq.popleft()
        if len(dq) >= self.max_requests:
            return False
        dq.append(now)
        return True


# Paths (by suffix) that perform sensitive mutations and deserve a tight budget.
_SENSITIVE_SUFFIXES = (
    "/signin",
    "/signup",
    "/submit",
    "/grade",
)


def _client_key(request: Request) -> str:
    # Prefer the authenticated bearer token (per-user); fall back to client IP.
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return "tok:" + auth[7:][:32]
    client = request.client
    return "ip:" + (client.host if client else "unknown")


def add_rate_limiting(app, max_requests: int = 10, window_seconds: int = 60) -> None:
    """Register the limiter middleware. Mutating requests to sensitive paths are capped
    per caller; everything else passes through untouched."""
    limiter = SlidingWindowLimiter(max_requests, window_seconds)

    @app.middleware("http")
    async def rate_limit(request: Request, call_next):
        path = request.url.path
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and path.endswith(
            _SENSITIVE_SUFFIXES
        ):
            key = f"{_client_key(request)}|{path}"
            if not limiter.allow(key):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests — please slow down."},
                    headers={"Retry-After": str(window_seconds)},
                )
        return await call_next(request)
