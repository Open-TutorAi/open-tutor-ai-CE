"""Contract tests — /api/v1/knowledge/* matches knowledge/index.ts calls."""


def _auth(client, email="kb@test.com"):
    client.post(
        "/auths/signup", json={"email": email, "name": "KB", "password": "pass1234!"}
    )
    r = client.post(
        "/api/v1/auths/signin", json={"email": email, "password": "pass1234!"}
    )
    return {"Authorization": f"Bearer {r.json()['token']}"}


class TestKnowledgeApiV1:
    def test_create(self, client):
        h = _auth(client)
        r = client.post(
            "/api/v1/knowledge/create",
            json={"name": "Math KB", "description": "Algebra content"},
            headers=h,
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Math KB"
        assert "id" in r.json()

    def test_create_with_access_control(self, client):
        h = _auth(client, "kb_ac@test.com")
        r = client.post(
            "/api/v1/knowledge/create",
            json={"name": "Private KB", "access_control": {"read": {"group_ids": []}}},
            headers=h,
        )
        assert r.status_code == 200
        assert r.json()["access_control"] == {"read": {"group_ids": []}}

    def test_list(self, client):
        h = _auth(client, "kb2@test.com")
        r = client.get("/api/v1/knowledge/", headers=h)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_only_shows_own_knowledge(self, client):
        h1 = _auth(client, "kb_own1@test.com")
        h2 = _auth(client, "kb_own2@test.com")
        client.post("/api/v1/knowledge/create", json={"name": "User1 KB"}, headers=h1)
        r = client.get("/api/v1/knowledge/", headers=h2)
        names = [kb["name"] for kb in r.json()]
        assert "User1 KB" not in names

    def test_list_endpoint(self, client):
        h = _auth(client, "kb3@test.com")
        r = client.get("/api/v1/knowledge/list", headers=h)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_by_id(self, client):
        h = _auth(client, "kb4@test.com")
        kb = client.post(
            "/api/v1/knowledge/create", json={"name": "Science"}, headers=h
        ).json()
        r = client.get(f"/api/v1/knowledge/{kb['id']}", headers=h)
        assert r.status_code == 200
        assert r.json()["id"] == kb["id"]

    def test_update(self, client):
        h = _auth(client, "kb5@test.com")
        kb = client.post(
            "/api/v1/knowledge/create", json={"name": "Old Name"}, headers=h
        ).json()
        r = client.post(
            f"/api/v1/knowledge/{kb['id']}/update", json={"name": "New Name"}, headers=h
        )
        assert r.status_code == 200
        assert r.json()["name"] == "New Name"

    def test_update_access_control(self, client):
        h = _auth(client, "kb5b@test.com")
        kb = client.post(
            "/api/v1/knowledge/create", json={"name": "AC Test"}, headers=h
        ).json()
        r = client.post(
            f"/api/v1/knowledge/{kb['id']}/update",
            json={"access_control": {"read": {"group_ids": ["g1"]}}},
            headers=h,
        )
        assert r.status_code == 200
        assert r.json()["access_control"] == {"read": {"group_ids": ["g1"]}}

    def test_add_and_remove_file(self, client):
        h = _auth(client, "kb6@test.com")
        kb = client.post(
            "/api/v1/knowledge/create", json={"name": "With Files"}, headers=h
        ).json()
        r = client.post(
            f"/api/v1/knowledge/{kb['id']}/file/add",
            json={"file_id": "file-abc"},
            headers=h,
        )
        assert r.status_code == 200
        r2 = client.post(
            f"/api/v1/knowledge/{kb['id']}/file/remove",
            json={"file_id": "file-abc"},
            headers=h,
        )
        assert r2.status_code == 200

    def test_update_file(self, client):
        h = _auth(client, "kb6b@test.com")
        kb = client.post(
            "/api/v1/knowledge/create", json={"name": "File Update"}, headers=h
        ).json()
        client.post(
            f"/api/v1/knowledge/{kb['id']}/file/add",
            json={"file_id": "file-xyz"},
            headers=h,
        )
        r = client.post(
            f"/api/v1/knowledge/{kb['id']}/file/update",
            json={"file_id": "file-xyz"},
            headers=h,
        )
        assert r.status_code == 200

    def test_reset(self, client):
        h = _auth(client, "kb7@test.com")
        kb = client.post(
            "/api/v1/knowledge/create", json={"name": "Reset Test"}, headers=h
        ).json()
        r = client.post(f"/api/v1/knowledge/{kb['id']}/reset", headers=h)
        assert r.status_code == 200

    def test_delete(self, client):
        h = _auth(client, "kb8@test.com")
        kb = client.post(
            "/api/v1/knowledge/create", json={"name": "To Delete"}, headers=h
        ).json()
        r = client.delete(f"/api/v1/knowledge/{kb['id']}/delete", headers=h)
        assert r.status_code == 200

    def test_cannot_get_other_user_knowledge(self, client):
        h1 = _auth(client, "kb_get1@test.com")
        h2 = _auth(client, "kb_get2@test.com")
        kb = client.post(
            "/api/v1/knowledge/create", json={"name": "User1 Private"}, headers=h1
        ).json()
        r = client.get(f"/api/v1/knowledge/{kb['id']}", headers=h2)
        assert r.status_code == 404

    def test_cannot_update_other_user_knowledge(self, client):
        h1 = _auth(client, "kb_other1@test.com")
        h2 = _auth(client, "kb_other2@test.com")
        kb = client.post(
            "/api/v1/knowledge/create", json={"name": "User1 Only"}, headers=h1
        ).json()
        r = client.post(
            f"/api/v1/knowledge/{kb['id']}/update", json={"name": "Hacked"}, headers=h2
        )
        assert r.status_code == 404
