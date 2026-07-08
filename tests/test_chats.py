# tests/test_chats.py
def _token(client):
    r = client.post(
        "/auths/signup",
        json={"email": "chat@t.com", "name": "C", "password": "pass1234!"},
    )
    return r.json()["token"]


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


def test_create_chat(client):
    token = _token(client)
    r = client.post(
        "/api/v1/chats/new",
        json={"chat": {"title": "Hello", "messages": [], "models": ["gpt-4o"]}},
        headers=_auth(token),
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["title"] == "Hello"


def test_get_chat_list(client):
    token = _token(client)
    client.post(
        "/api/v1/chats/new",
        json={"chat": {"title": "A", "messages": []}},
        headers=_auth(token),
    )
    r = client.get("/api/v1/chats/", headers=_auth(token))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_chat_by_id(client):
    token = _token(client)
    created = client.post(
        "/api/v1/chats/new",
        json={"chat": {"title": "Test", "messages": []}},
        headers=_auth(token),
    ).json()
    r = client.get(f"/api/v1/chats/{created['id']}", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_update_chat(client):
    token = _token(client)
    created = client.post(
        "/api/v1/chats/new",
        json={"chat": {"title": "Old", "messages": []}},
        headers=_auth(token),
    ).json()
    r = client.post(
        f"/api/v1/chats/{created['id']}",
        json={
            "chat": {"title": "New", "messages": [{"role": "user", "content": "hi"}]}
        },
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json()["title"] == "New"


def test_delete_chat(client):
    token = _token(client)
    created = client.post(
        "/api/v1/chats/new",
        json={"chat": {"title": "Del", "messages": []}},
        headers=_auth(token),
    ).json()
    r = client.delete(f"/api/v1/chats/{created['id']}", headers=_auth(token))
    assert r.status_code == 200
    assert (
        client.get(f"/api/v1/chats/{created['id']}", headers=_auth(token)).status_code
        == 404
    )


def test_archive_chat(client):
    token = _token(client)
    created = client.post(
        "/api/v1/chats/new",
        json={"chat": {"title": "Arc", "messages": []}},
        headers=_auth(token),
    ).json()
    r = client.post(f"/api/v1/chats/{created['id']}/archive", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["archived"] is True


def test_pin_chat(client):
    token = _token(client)
    created = client.post(
        "/api/v1/chats/new",
        json={"chat": {"title": "Pin", "messages": []}},
        headers=_auth(token),
    ).json()
    r = client.post(f"/api/v1/chats/{created['id']}/pin", headers=_auth(token))
    assert r.status_code == 200


def test_share_chat(client):
    token = _token(client)
    created = client.post(
        "/api/v1/chats/new",
        json={"chat": {"title": "Share", "messages": []}},
        headers=_auth(token),
    ).json()
    r = client.post(f"/api/v1/chats/{created['id']}/share", headers=_auth(token))
    assert r.status_code == 200
    assert "share_id" in r.json()


def test_add_and_get_tag(client):
    token = _token(client)
    created = client.post(
        "/api/v1/chats/new",
        json={"chat": {"title": "Tagged", "messages": []}},
        headers=_auth(token),
    ).json()
    client.post(
        f"/api/v1/chats/{created['id']}/tags",
        json={"name": "work"},
        headers=_auth(token),
    )
    r = client.get(f"/api/v1/chats/{created['id']}/tags", headers=_auth(token))
    assert r.status_code == 200
    tags = r.json()
    assert any(t.get("name") == "work" for t in tags)


def test_search_chats(client):
    token = _token(client)
    client.post(
        "/api/v1/chats/new",
        json={"chat": {"title": "Unique XYZ", "messages": []}},
        headers=_auth(token),
    )
    r = client.get("/api/v1/chats/search?q=XYZ", headers=_auth(token))
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_delete_all_chats(client):
    token = _token(client)
    client.post(
        "/api/v1/chats/new", json={"chat": {"title": "A"}}, headers=_auth(token)
    )
    r = client.delete("/api/v1/chats/", headers=_auth(token))
    assert r.status_code == 200
    assert client.get("/api/v1/chats/", headers=_auth(token)).json() == []


def test_cannot_access_other_users_chat(client):
    owner = _token(client)  # first signup
    created = client.post(
        "/api/v1/chats/new",
        json={"chat": {"title": "Private", "messages": []}},
        headers=_auth(owner),
    ).json()
    attacker = client.post(
        "/auths/signup",
        json={"email": "atk3@t.com", "name": "A", "password": "pass1234!"},
    ).json()["token"]
    # Non-owner GET must 404 (not 403 — must not leak existence)
    assert (
        client.get(
            f"/api/v1/chats/{created['id']}", headers=_auth(attacker)
        ).status_code
        == 404
    )
    # Non-owner UPDATE must also 404 (consistency with Fix 1)
    upd = client.post(
        f"/api/v1/chats/{created['id']}",
        json={"chat": {"title": "Hacked", "messages": []}},
        headers=_auth(attacker),
    )
    assert upd.status_code == 404
    # Non-owner DELETE must 404
    assert (
        client.delete(
            f"/api/v1/chats/{created['id']}", headers=_auth(attacker)
        ).status_code
        == 404
    )
