"""Contract tests — /api/v1/retrieval/* matches retrieval/index.ts calls."""


def _admin_auth(client):
    """First signup → admin."""
    client.post(
        "/auths/signup",
        json={"email": "admin@ret.com", "name": "Admin", "password": "pass1234!"},
    )
    r = client.post(
        "/api/v1/auths/signin", json={"email": "admin@ret.com", "password": "pass1234!"}
    )
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _user_auth(client):
    """Second signup → regular user."""
    client.post(
        "/auths/signup",
        json={"email": "user@ret.com", "name": "User", "password": "pass1234!"},
    )
    r = client.post(
        "/api/v1/auths/signin", json={"email": "user@ret.com", "password": "pass1234!"}
    )
    return {"Authorization": f"Bearer {r.json()['token']}"}


class TestRetrievalApiV1:
    def test_get_config_admin(self, client):
        h = _admin_auth(client)
        r = client.get("/api/v1/retrieval/config", headers=h)
        assert r.status_code == 200

    def test_get_config_user_forbidden(self, client):
        _admin_auth(client)
        h = _user_auth(client)
        r = client.get("/api/v1/retrieval/config", headers=h)
        assert r.status_code == 403

    def test_update_config_nested(self, client):
        h = _admin_auth(client)
        r = client.post(
            "/api/v1/retrieval/config/update",
            json={
                "chunk": {"chunk_size": 1200, "chunk_overlap": 100},
                "content_extraction": {"engine": "tika", "tika_server_url": None},
                "pdf_extract_images": True,
            },
            headers=h,
        )
        assert r.status_code == 200
        assert r.json()["chunk"]["chunk_size"] == 1200
        assert r.json()["pdf_extract_images"] is True

    def test_update_config_user_forbidden(self, client):
        _admin_auth(client)
        h = _user_auth(client)
        r = client.post("/api/v1/retrieval/config/update", json={}, headers=h)
        assert r.status_code == 403

    def test_get_template(self, client):
        h = _admin_auth(client)
        r = client.get("/api/v1/retrieval/template", headers=h)
        assert r.status_code == 200
        assert "template" in r.json()

    def test_query_settings(self, client):
        h = _admin_auth(client)
        r = client.get("/api/v1/retrieval/query/settings", headers=h)
        assert r.status_code == 200

    def test_update_query_settings(self, client):
        h = _admin_auth(client)
        r = client.post(
            "/api/v1/retrieval/query/settings/update",
            json={"k": 5, "r": 0.5, "template": None},
            headers=h,
        )
        assert r.status_code == 200

    def test_get_embedding_admin(self, client):
        h = _admin_auth(client)
        r = client.get("/api/v1/retrieval/embedding", headers=h)
        assert r.status_code == 200

    def test_get_embedding_user_forbidden(self, client):
        _admin_auth(client)
        h = _user_auth(client)
        r = client.get("/api/v1/retrieval/embedding", headers=h)
        assert r.status_code == 403

    def test_update_embedding(self, client):
        h = _admin_auth(client)
        r = client.post(
            "/api/v1/retrieval/embedding/update",
            json={
                "embedding_engine": "openai",
                "embedding_model": "text-embedding-3-small",
            },
            headers=h,
        )
        assert r.status_code == 200
        assert r.json()["embedding_engine"] == "openai"

    def test_get_reranking_admin(self, client):
        h = _admin_auth(client)
        r = client.get("/api/v1/retrieval/reranking", headers=h)
        assert r.status_code == 200

    def test_update_reranking(self, client):
        h = _admin_auth(client)
        r = client.post(
            "/api/v1/retrieval/reranking/update",
            json={"reranking_model": "cross-encoder/ms-marco-MiniLM-L-6-v2"},
            headers=h,
        )
        assert r.status_code == 200
        assert r.json()["reranking_model"] == "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def test_process_file(self, client):
        _admin_auth(client)
        h = _user_auth(client)
        r = client.post(
            "/api/v1/retrieval/process/file",
            json={"file_id": "f1", "collection_name": "col1"},
            headers=h,
        )
        assert r.status_code == 200

    def test_process_youtube(self, client):
        h = _admin_auth(client)
        r = client.post(
            "/api/v1/retrieval/process/youtube",
            json={"url": "https://youtube.com/watch?v=test"},
            headers=h,
        )
        assert r.status_code == 200

    def test_process_web(self, client):
        h = _admin_auth(client)
        r = client.post(
            "/api/v1/retrieval/process/web",
            json={"url": "https://example.com", "collection_name": "col1"},
            headers=h,
        )
        assert r.status_code == 200

    def test_process_web_search(self, client):
        h = _admin_auth(client)
        r = client.post(
            "/api/v1/retrieval/process/web/search",
            json={"query": "test query", "collection_name": ""},
            headers=h,
        )
        assert r.status_code == 200

    def test_query_doc(self, client):
        h = _admin_auth(client)
        r = client.post(
            "/api/v1/retrieval/query/doc",
            json={"collection_name": "col1", "query": "test", "k": None},
            headers=h,
        )
        assert r.status_code == 200

    def test_query_collection(self, client):
        h = _admin_auth(client)
        r = client.post(
            "/api/v1/retrieval/query/collection",
            json={"collection_names": "col1,col2", "query": "test", "k": None},
            headers=h,
        )
        assert r.status_code == 200

    def test_reset_uploads_admin(self, client):
        h = _admin_auth(client)
        r = client.post("/api/v1/retrieval/reset/uploads", headers=h)
        assert r.status_code == 200

    def test_reset_db_admin(self, client):
        h = _admin_auth(client)
        r = client.post("/api/v1/retrieval/reset/db", headers=h)
        assert r.status_code == 200

    def test_reset_uploads_user_forbidden(self, client):
        _admin_auth(client)
        h = _user_auth(client)
        r = client.post("/api/v1/retrieval/reset/uploads", headers=h)
        assert r.status_code == 403

    def test_reset_db_user_forbidden(self, client):
        _admin_auth(client)
        h = _user_auth(client)
        r = client.post("/api/v1/retrieval/reset/db", headers=h)
        assert r.status_code == 403
