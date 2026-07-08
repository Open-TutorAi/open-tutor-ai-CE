"""Shared rate limiter for brute-forceable endpoints (login, signup, invite
redemption, session join). Kept in its own module so routers can import it
without creating a circular import with the app factory.
"""

from starlette.requests import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_user_id_or_ip(request: Request) -> str:
    """Rate-limit key: user ID when a valid JWT is present, IP otherwise.

    Self check-in (POST /api/sessions/{id}/join) must not key off IP because
    an entire classroom on the same school NAT would share one bucket and the
    31st student would get a 429 before the session fills.
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        from gateway.http.dependencies import decode_jwt_token

        payload = decode_jwt_token(auth[7:])
        if payload and "sub" in payload:
            return f"user:{payload['sub']}"
    return get_remote_address(request)


limiter = Limiter(key_func=get_remote_address)
