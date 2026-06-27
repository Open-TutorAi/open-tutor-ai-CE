"""Tests for /api/v1/models/* endpoints."""


def _token(client):
    r = client.post(
        "/auths/signup",
        json={"email": "mdl@t.com", "name": "M", "password": "pass1234!"},
    )
    return r.json()["token"]


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


def test_get_models(client):
    token = _token(client)
    r = client.get("/api/v1/models/", headers=_auth(token))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_base_models(client):
    token = _token(client)
    r = client.get("/api/v1/models/base", headers=_auth(token))
    assert r.status_code == 200


def test_create_and_get_model(client):
    token = _token(client)
    r = client.post(
        "/api/v1/models/create",
        json={
            "id": "my-model",
            "name": "My Model",
            "base_model_id": "gpt-4o",
            "meta": {"description": "test"},
            "params": {},
        },
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json()["id"] == "my-model"

    r2 = client.get("/api/v1/models/model?id=my-model", headers=_auth(token))
    assert r2.status_code == 200
    assert r2.json()["name"] == "My Model"


def test_toggle_model(client):
    token = _token(client)
    client.post(
        "/api/v1/models/create",
        json={"id": "tog-model", "name": "Tog", "meta": {}, "params": {}},
        headers=_auth(token),
    )
    r = client.post("/api/v1/models/model/toggle?id=tog-model", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["is_active"] is False


def test_delete_model(client):
    token = _token(client)
    client.post(
        "/api/v1/models/create",
        json={"id": "del-model", "name": "Del", "meta": {}, "params": {}},
        headers=_auth(token),
    )
    r = client.delete("/api/v1/models/model/delete?id=del-model", headers=_auth(token))
    assert r.status_code == 200


def test_create_duplicate_id_returns_400(client):
    token = _token(client)
    payload = {"id": "dup", "name": "Dup", "meta": {}, "params": {}}
    client.post("/api/v1/models/create", json=payload, headers=_auth(token))
    r = client.post("/api/v1/models/create", json=payload, headers=_auth(token))
    assert r.status_code == 400


def test_create_missing_id_returns_400(client):
    token = _token(client)
    r = client.post(
        "/api/v1/models/create", json={"name": "NoId"}, headers=_auth(token)
    )
    assert r.status_code == 400


def test_get_nonexistent_model_returns_404(client):
    token = _token(client)
    r = client.get("/api/v1/models/model?id=ghost", headers=_auth(token))
    assert r.status_code == 404


def test_non_owner_cannot_delete_model(client):
    owner = _token(client)  # first signup = admin... so make owner the SECOND user
    # Actually first user is admin; create a second non-admin owner and a third non-admin attacker
    client.post(
        "/api/v1/models/create",
        json={"id": "owned", "name": "Owned", "meta": {}, "params": {}},
        headers=_auth(owner),
    )
    attacker = client.post(
        "/auths/signup",
        json={"email": "atk@t.com", "name": "A", "password": "pass1234!"},
    ).json()["token"]
    r = client.delete("/api/v1/models/model/delete?id=owned", headers=_auth(attacker))
    assert r.status_code == 403
