# tests/test_files.py
"""Contract tests for /api/v1/files/* — paths from ui/src/lib/apis/files/index.ts."""

import io


def _signup(client, email="files@test.com"):
    r = client.post(
        "/auths/signup", json={"email": email, "name": "U", "password": "pass1234!"}
    )
    assert r.status_code == 200
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _upload(client, token, content=b"hello world", filename="test.txt"):
    return client.post(
        "/api/v1/files/",
        files={"file": (filename, io.BytesIO(content), "text/plain")},
        headers=_auth(token),
    )


class TestFilesApiV1:
    def test_upload_file(self, client):
        """POST /api/v1/files/  ← uploadFile() in files/index.ts:8"""
        token = _signup(client)
        r = _upload(client, token)
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["filename"] == "test.txt"
        assert data["user_id"] is not None

    def test_upload_dir_stub(self, client):
        """POST /api/v1/files/upload/dir  ← uploadDir() in files/index.ts:36"""
        token = _signup(client, "dir@test.com")
        r = client.post("/api/v1/files/upload/dir", headers=_auth(token))
        assert r.status_code == 200
        assert r.json() == []

    def test_get_files(self, client):
        """GET /api/v1/files/  ← getFiles() in files/index.ts:62"""
        token = _signup(client, "list@test.com")
        _upload(client, token)
        r = client.get("/api/v1/files/", headers=_auth(token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) == 1

    def test_get_file_by_id(self, client):
        """GET /api/v1/files/{id}  ← getFileById() in files/index.ts:93"""
        token = _signup(client, "get@test.com")
        file_id = _upload(client, token).json()["id"]
        r = client.get(f"/api/v1/files/{file_id}", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["id"] == file_id

    def test_get_file_content(self, client):
        """GET /api/v1/files/{id}/content  ← getFileContentById() in files/index.ts:158"""
        token = _signup(client, "content@test.com")
        file_id = _upload(client, token, content=b"hello world").json()["id"]
        r = client.get(f"/api/v1/files/{file_id}/content", headers=_auth(token))
        assert r.status_code == 200
        assert r.content == b"hello world"

    def test_get_file_content_requires_auth(self, client):
        """Content endpoint requires authentication — no anonymous access."""
        token = _signup(client, "noauth@test.com")
        file_id = _upload(client, token).json()["id"]
        assert client.get(f"/api/v1/files/{file_id}/content").status_code == 403

    def test_update_file_content(self, client):
        """POST /api/v1/files/{id}/data/content/update  ← updateFileDataContentById() in files/index.ts:124"""
        token = _signup(client, "update@test.com")
        file_id = _upload(client, token).json()["id"]
        r = client.post(
            f"/api/v1/files/{file_id}/data/content/update",
            json={"content": "updated text"},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["data"]["content"] == "updated text"

    def test_delete_file(self, client):
        """DELETE /api/v1/files/{id}  ← deleteFileById() in files/index.ts:186"""
        token = _signup(client, "del@test.com")
        file_id = _upload(client, token).json()["id"]
        r = client.delete(f"/api/v1/files/{file_id}", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["id"] == file_id
        # Confirm gone
        assert (
            client.get(f"/api/v1/files/{file_id}", headers=_auth(token)).status_code
            == 404
        )

    def test_delete_all_files(self, client):
        """DELETE /api/v1/files/all  ← deleteAllFiles() in files/index.ts:217"""
        token = _signup(client, "delall@test.com")
        _upload(client, token)
        _upload(client, token, filename="b.txt")
        r = client.delete("/api/v1/files/all", headers=_auth(token))
        assert r.status_code == 200
        assert r.json()["count"] == 2
        assert client.get("/api/v1/files/", headers=_auth(token)).json() == []

    def test_upload_ownership(self, client):
        """Another user cannot access a file they don't own."""
        token_a = _signup(client, "owna@test.com")
        token_b = _signup(client, "ownb@test.com")
        file_id = _upload(client, token_a).json()["id"]
        assert (
            client.get(f"/api/v1/files/{file_id}", headers=_auth(token_b)).status_code
            == 403
        )
