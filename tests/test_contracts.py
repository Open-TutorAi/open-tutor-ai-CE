# tests/test_contracts.py
"""
Contract tests — every path here is derived directly from constants.ts and
the api/ index files in the UI. A 404 on any of these means the UI is broken.

Convention:
  TUTOR_API_BASE_URL = /api/v1       (most calls)
  TUTOR_BASE_URL     = ""  (root)    (signup, user-count)
"""


# ── helpers ───────────────────────────────────────────────────────────────────


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _signup(client, email="u@test.com", name="U", pwd="pass1234!"):
    r = client.post(
        "/auths/signup", json={"email": email, "name": name, "password": pwd}
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


# ── Auth ─────────────────────────────────────────────────────────────────────
# TUTOR_BASE_URL  paths (no /api/v1)


class TestAuthRoot:
    """Paths the UI calls via TUTOR_BASE_URL (no /api/v1)."""

    def test_signup_root(self, client):
        """POST /auths/signup  ← userSignUp() in auths/index.ts:325"""
        r = client.post(
            "/auths/signup",
            json={
                "email": "signup@test.com",
                "name": "Alice",
                "password": "secret123!",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert "token" in data
        assert data["email"] == "signup@test.com"

    def test_user_count_root(self, client):
        """GET /auths/user-count  ← getNumUsers() in auths/index.ts:117"""
        r = client.get("/auths/user-count")
        assert r.status_code == 200
        assert "count" in r.json()


# TUTOR_API_BASE_URL  paths (/api/v1/*)


class TestAuthApiV1:
    """Paths the UI calls via TUTOR_API_BASE_URL (/api/v1)."""

    def test_signin(self, client):
        """POST /api/v1/auths/signin  ← userSignIn() in auths/index.ts:287"""
        _signup(client)
        r = client.post(
            "/api/v1/auths/signin",
            json={
                "email": "u@test.com",
                "password": "pass1234!",
            },
        )
        assert r.status_code == 200
        assert "token" in r.json()

    def test_signin_wrong_password(self, client):
        """POST /api/v1/auths/signin with bad credentials → 401"""
        _signup(client)
        r = client.post(
            "/api/v1/auths/signin",
            json={
                "email": "u@test.com",
                "password": "wrong",
            },
        )
        assert r.status_code == 401

    def test_session_user(self, client):
        """GET /api/v1/auths/  ← getSessionUser() in auths/index.ts:88"""
        token = _signup(client)
        r = client.get("/api/v1/auths/", headers=_auth_header(token))
        assert r.status_code == 200
        data = r.json()
        assert "id" in data and "email" in data

    def test_signout(self, client):
        """GET /api/v1/auths/signout  ← userSignOut() in auths/index.ts:359"""
        token = _signup(client)
        r = client.get("/api/v1/auths/signout", headers=_auth_header(token))
        assert r.status_code == 200


# ── Supports ──────────────────────────────────────────────────────────────────
# All via TUTOR_API_BASE_URL → /api/v1/supports/*


class TestSupportsApiV1:
    def test_create(self, client):
        """POST /api/v1/supports/create  ← createSupport() in supports/index.ts:66"""
        token = _signup(client)
        r = client.post(
            "/api/v1/supports/create",
            json={"title": "Test support", "subject": "Math"},
            headers=_auth_header(token),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["title"] == "Test support"
        assert "id" in data

    def test_list(self, client):
        """GET /api/v1/supports/list  ← getSupportRequests() in supports/index.ts:141"""
        token = _signup(client)
        r = client.get("/api/v1/supports/list", headers=_auth_header(token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_with_status_filter(self, client):
        """GET /api/v1/supports/list?status=pending  ← getSupportRequests(token, 'pending')"""
        token = _signup(client)
        r = client.get(
            "/api/v1/supports/list?status=pending", headers=_auth_header(token)
        )
        assert r.status_code == 200

    def test_get_by_id(self, client):
        """GET /api/v1/supports/{id}  ← getSupportById() in supports/index.ts:180"""
        token = _signup(client)
        created = client.post(
            "/api/v1/supports/create",
            json={"title": "For get", "subject": "Science"},
            headers=_auth_header(token),
        ).json()
        r = client.get(f"/api/v1/supports/{created['id']}", headers=_auth_header(token))
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_update_chat_id(self, client):
        """PATCH /api/v1/supports/{id}/update-chat  ← updateSupportChatId() in supports/index.ts:223"""
        token = _signup(client)
        support = client.post(
            "/api/v1/supports/create",
            json={"title": "Chat update", "subject": "Art"},
            headers=_auth_header(token),
        ).json()
        r = client.patch(
            f"/api/v1/supports/{support['id']}/update-chat?chat_id=chat-abc",
            headers=_auth_header(token),
        )
        assert r.status_code == 200
        assert r.json()["chat_id"] == "chat-abc"

    def test_update(self, client):
        """PATCH /api/v1/supports/{id}  ← updateSupport() in supports/index.ts:279"""
        token = _signup(client)
        support = client.post(
            "/api/v1/supports/create",
            json={"title": "Original", "subject": "History"},
            headers=_auth_header(token),
        ).json()
        r = client.patch(
            f"/api/v1/supports/{support['id']}",
            json={"title": "Updated", "subject": "History"},
            headers=_auth_header(token),
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Updated"

    def test_delete(self, client):
        """DELETE /api/v1/supports/{id}  ← deleteSupport() in supports/index.ts:316"""
        token = _signup(client)
        support = client.post(
            "/api/v1/supports/create",
            json={"title": "To delete", "subject": "PE"},
            headers=_auth_header(token),
        ).json()
        r = client.delete(
            f"/api/v1/supports/{support['id']}", headers=_auth_header(token)
        )
        assert r.status_code == 200


# ── Self Regulation ────────────────────────────────────────────────────────────
# All via TUTOR_API_BASE_URL → /api/v1/self_regulation/*


class TestSelfRegulationApiV1:
    def test_get_config(self, client):
        """GET /api/v1/self_regulation/config  ← getConfig() in evaluations/index.ts:6"""
        token = _signup(client)
        r = client.get("/api/v1/self_regulation/config", headers=_auth_header(token))
        assert r.status_code == 200

    def test_update_config(self, client):
        """POST /api/v1/self_regulation/config  ← updateConfig() in evaluations/index.ts:37"""
        token = _signup(client)
        r = client.post(
            "/api/v1/self_regulation/config",
            json={"enabled": True},
            headers=_auth_header(token),
        )
        assert r.status_code == 200

    def test_get_all_feedbacks(self, client):
        """GET /api/v1/self_regulation/feedbacks/all  ← getAllFeedbacks() in evaluations/index.ts:68"""
        token = _signup(client)
        r = client.get(
            "/api/v1/self_regulation/feedbacks/all", headers=_auth_header(token)
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_export_feedbacks(self, client):
        """GET /api/v1/self_regulation/feedbacks/all/export  ← exportAllFeedbacks() in evaluations/index.ts:99"""
        token = _signup(client)
        r = client.get(
            "/api/v1/self_regulation/feedbacks/all/export", headers=_auth_header(token)
        )
        assert r.status_code == 200

    def test_create_feedback(self, client):
        """POST /api/v1/self_regulation/feedback  ← createNewFeedback() in evaluations/index.ts:130"""
        token = _signup(client)
        r = client.post(
            "/api/v1/self_regulation/feedback",
            json={"data": {"rating": "positive", "comment": "Great!"}},
            headers=_auth_header(token),
        )
        assert r.status_code == 200
        assert "id" in r.json()

    def test_get_feedback_by_id(self, client):
        """GET /api/v1/self_regulation/feedback/{id}  ← getFeedbackById() in evaluations/index.ts:161"""
        token = _signup(client)
        fb = client.post(
            "/api/v1/self_regulation/feedback",
            json={"data": {"rating": "neutral"}},
            headers=_auth_header(token),
        ).json()
        r = client.get(
            f"/api/v1/self_regulation/feedback/{fb['id']}", headers=_auth_header(token)
        )
        assert r.status_code == 200
        assert r.json()["id"] == fb["id"]

    def test_update_feedback(self, client):
        """POST /api/v1/self_regulation/feedback/{id}  ← updateFeedbackById() in evaluations/index.ts:192"""
        token = _signup(client)
        fb = client.post(
            "/api/v1/self_regulation/feedback",
            json={"data": {"rating": "neutral"}},
            headers=_auth_header(token),
        ).json()
        r = client.post(
            f"/api/v1/self_regulation/feedback/{fb['id']}",
            json={"data": {"rating": "positive"}},
            headers=_auth_header(token),
        )
        assert r.status_code == 200

    def test_delete_feedback(self, client):
        """DELETE /api/v1/self_regulation/feedback/{id}  ← deleteFeedbackById() in evaluations/index.ts:223"""
        token = _signup(client)
        fb = client.post(
            "/api/v1/self_regulation/feedback",
            json={"data": {"rating": "negative"}},
            headers=_auth_header(token),
        ).json()
        r = client.delete(
            f"/api/v1/self_regulation/feedback/{fb['id']}", headers=_auth_header(token)
        )
        assert r.status_code == 200
