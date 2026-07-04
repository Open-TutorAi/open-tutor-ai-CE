# tests/test_cookie_auth.py
"""HttpOnly cookie sessions — the browser auth channel.

Signin/signup set an HttpOnly, SameSite=Lax session cookie; `get_current_user`
prefers an explicit `Authorization: Bearer` token (tests, tools) and otherwise
authenticates via the cookie. A CSRF origin check guards *cookie-only*
mutations, and the Socket.IO handshake accepts the cookie as well.
"""

from config import settings
from gateway.realtime.socket import _token_from_cookie


def _signup(client, email="cookie@t.com", name="Cookie", password="pass1234!"):
    # Signup happens while logged out — clear any prior session cookie so the
    # request is anonymous (mirrors a browser, and avoids the cookie-only CSRF
    # guard firing on a bodyless-origin test request).
    client.cookies.clear()
    r = client.post(
        "/auths/signup", json={"email": email, "name": name, "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()


# ── cookie issuing ────────────────────────────────────────────────────────────


def test_signup_and_signin_set_httponly_cookie(client):
    r = client.post(
        "/auths/signup",
        json={"email": "a@t.com", "name": "A", "password": "pass1234!"},
    )
    raw = r.headers.get("set-cookie", "")
    assert f"{settings.AUTH_COOKIE_NAME}=" in raw
    assert "HttpOnly" in raw
    assert "SameSite=lax" in raw
    assert "Path=/" in raw

    client.cookies.clear()
    r = client.post(
        "/api/v1/auths/signin", json={"email": "a@t.com", "password": "pass1234!"}
    )
    assert r.status_code == 200, r.text
    raw = r.headers.get("set-cookie", "")
    assert f"{settings.AUTH_COOKIE_NAME}=" in raw and "HttpOnly" in raw


def test_cookie_authenticates_without_bearer_header(client):
    _signup(client)  # TestClient persists the Set-Cookie automatically
    r = client.get("/api/v1/auths/")  # no Authorization header at all
    assert r.status_code == 200, r.text
    assert r.json()["email"] == "cookie@t.com"


def test_signout_clears_cookie_session(client):
    _signup(client)
    assert client.get("/api/v1/auths/").status_code == 200
    r = client.get("/api/v1/auths/signout")
    assert r.status_code == 200
    assert client.get("/api/v1/auths/").status_code == 401


# ── bearer compatibility ─────────────────────────────────────────────────────


def test_bearer_still_works_without_cookie(client):
    data = _signup(client)
    client.cookies.clear()
    r = client.get(
        "/api/v1/auths/", headers={"Authorization": f"Bearer {data['token']}"}
    )
    assert r.status_code == 200
    assert r.json()["email"] == "cookie@t.com"


def test_stale_bearer_falls_through_to_cookie(client):
    """Older UI code may still send `Authorization: Bearer null` — with a valid
    cookie session that garbage header must be ignored, not break the request."""
    _signup(client)
    r = client.get("/api/v1/auths/", headers={"Authorization": "Bearer null"})
    assert r.status_code == 200


def test_explicit_bearer_wins_over_cookie(client):
    """A real Bearer token states exactly who the caller is — it must not be
    silently overridden by whatever session cookie the client happens to hold."""
    first = _signup(client)
    _signup(client, email="second@t.com")  # the client's cookie is now SECOND's
    r = client.get(
        "/api/v1/auths/", headers={"Authorization": f"Bearer {first['token']}"}
    )
    assert r.status_code == 200
    assert r.json()["email"] == "cookie@t.com"  # the bearer's user, not the cookie's
    # And without the header, the cookie (second user) authenticates.
    assert client.get("/api/v1/auths/").json()["email"] == "second@t.com"


def test_missing_credentials_is_401(client):
    client.cookies.clear()
    assert client.get("/api/v1/auths/").status_code == 401


def test_bearer_to_cookie_exchange(client):
    """The /auths/cookie endpoint turns a bearer-authenticated request (e.g. an
    OAuth fragment token) into an HttpOnly cookie session."""
    data = _signup(client)
    client.cookies.clear()
    r = client.post(
        "/api/v1/auths/cookie", headers={"Authorization": f"Bearer {data['token']}"}
    )
    assert r.status_code == 200, r.text
    assert "HttpOnly" in r.headers.get("set-cookie", "")
    # The exchanged cookie now authenticates on its own.
    assert client.get("/api/v1/auths/").status_code == 200


# ── CSRF origin check ────────────────────────────────────────────────────────


def _pw_update(client, **headers):
    return client.post(
        "/api/v1/auths/update/password",
        json={"password": "pass1234!", "new_password": "other5678!"},
        headers=headers,
    )


def test_csrf_blocks_cookie_mutation_from_foreign_origin(client):
    _signup(client)
    r = _pw_update(client, Origin="https://evil.example")
    assert r.status_code == 403
    assert r.json()["detail"] == "Origin check failed"


def test_csrf_blocks_cookie_mutation_with_missing_origin(client):
    """A cookie-only unsafe request with NO Origin/Referer is rejected too —
    closes the "no Origin header" bypass."""
    _signup(client)
    r = _pw_update(client)
    assert r.status_code == 403


def test_csrf_allows_configured_origin(client):
    _signup(client)
    r = _pw_update(client, Origin="http://localhost:5173")  # default CORS origin
    assert r.status_code == 200, r.text


def test_csrf_allows_same_origin_via_forwarded_proto(client):
    """Behind a TLS-terminating proxy the app sees http internally; the check
    must honour X-Forwarded-Proto/Host so the real https origin matches."""
    _signup(client)
    r = _pw_update(
        client,
        Origin="https://tutor.example.com",
        **{"X-Forwarded-Proto": "https", "X-Forwarded-Host": "tutor.example.com"},
    )
    assert r.status_code == 200, r.text


def test_csrf_does_not_affect_bearer_clients(client):
    """A bearer token isn't a CSRF vector — foreign Origin is fine for API clients,
    even when a cookie is also present."""
    data = _signup(client)  # client keeps the cookie too
    r = _pw_update(
        client,
        Authorization=f"Bearer {data['token']}",
        Origin="https://anywhere.example",
    )
    assert r.status_code == 200, r.text


def test_csrf_ignores_safe_methods(client):
    _signup(client)
    r = client.get("/api/v1/auths/", headers={"Origin": "https://evil.example"})
    assert r.status_code == 200


# ── realtime handshake helper ────────────────────────────────────────────────


def test_socket_token_from_cookie_header():
    environ = {"HTTP_COOKIE": f"other=1; {settings.AUTH_COOKIE_NAME}=jwt-here; x=2"}
    assert _token_from_cookie(environ) == "jwt-here"
    assert _token_from_cookie({"HTTP_COOKIE": "other=1"}) is None
    assert _token_from_cookie({}) is None
