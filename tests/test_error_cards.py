# tests/test_error_cards.py
"""Tests for error cards endpoints — GET list, POST analyze, DELETE."""

from unittest.mock import AsyncMock, patch


# ── Helpers ───────────────────────────────────────────────────────────────────


def _signup(client, email="ec@t.com"):
    r = client.post(
        "/auths/signup",
        json={"email": email, "name": "Student", "password": "pass1234!"},
    )
    data = r.json()
    return data["token"], data["id"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _create_support(client, token):
    r = client.post(
        "/api/v1/supports/create",
        json={"title": "Maths Support"},
        headers=_auth(token),
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _insert_card(db, support_id, user_id):
    """Insert a card directly via the repository — bypasses LLM."""
    from learning.supports.error_cards.repository import ErrorCardRepository

    repo = ErrorCardRepository(db)
    return repo.create(
        support_id=support_id,
        user_id=user_id,
        concept="Dérivée",
        error_description="Mauvaise application de la règle.",
        simple_explanation="Il faut appliquer la règle de la chaîne.",
        correct_example="Si f(x)=sin(x²) alors f'(x)=cos(x²)·2x",
        source_user_message="Est-ce que f'(x)=2x pour x² ?",
        source_assistant_message="Non, il faut la règle de la chaîne.",
    )


# ── GET /supports/{id}/error-cards ────────────────────────────────────────────


def test_list_cards_empty(client):
    """Liste vide quand aucune fiche n'existe pour ce support."""
    token, _ = _signup(client, "list1@t.com")
    support_id = _create_support(client, token)

    r = client.get(f"/api/v1/supports/{support_id}/error-cards", headers=_auth(token))
    assert r.status_code == 200
    assert r.json() == []


def test_list_cards_unauthenticated(client):
    """GET sans token → 403 (HTTPBearer renvoie 403 quand le header est absent)."""
    r = client.get("/api/v1/supports/fake-id/error-cards")
    assert r.status_code == 403


def test_list_cards_returns_own_cards_only(client, db):
    """Un utilisateur ne voit que ses propres fiches."""
    token_a, user_a = _signup(client, "usera@t.com")
    token_b, _ = _signup(client, "userb@t.com")
    support_a = _create_support(client, token_a)

    _insert_card(db, support_a, user_a)

    r = client.get(
        f"/api/v1/supports/{support_a}/error-cards",
        headers=_auth(token_b),
    )
    assert r.status_code == 200
    assert r.json() == []


def test_list_cards_shows_existing_card(client, db):
    """GET retourne les fiches existantes de l'utilisateur."""
    token, user_id = _signup(client, "list2@t.com")
    support_id = _create_support(client, token)
    card = _insert_card(db, support_id, user_id)

    r = client.get(f"/api/v1/supports/{support_id}/error-cards", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["concept"] == "Dérivée"
    assert data[0]["id"] == card.id


# ── POST /supports/{id}/error-cards/analyze ──────────────────────────────────


def test_analyze_unauthenticated(client):
    """POST analyze sans token → 403 (HTTPBearer renvoie 403 quand le header est absent)."""
    r = client.post(
        "/api/v1/supports/fake-id/error-cards/analyze",
        json={"user_message": "test", "assistant_message": "test", "model": "llama3"},
    )
    assert r.status_code == 403


def test_analyze_support_not_found(client):
    """POST analyze sur un support inexistant → 404."""
    token, _ = _signup(client, "ana1@t.com")
    r = client.post(
        "/api/v1/supports/nonexistent-id/error-cards/analyze",
        json={
            "user_message": "question",
            "assistant_message": "réponse",
            "model": "llama3",
        },
        headers=_auth(token),
    )
    assert r.status_code == 404


def test_analyze_empty_user_message(client):
    """POST analyze avec user_message vide → 422 (Field min_length=1)."""
    token, _ = _signup(client, "ana2@t.com")
    support_id = _create_support(client, token)
    r = client.post(
        f"/api/v1/supports/{support_id}/error-cards/analyze",
        json={"user_message": "", "assistant_message": "réponse", "model": "llama3"},
        headers=_auth(token),
    )
    assert r.status_code == 422


def test_analyze_message_too_long(client):
    """POST analyze avec user_message > 10000 chars → 422 (Field max_length)."""
    token, _ = _signup(client, "ana3@t.com")
    support_id = _create_support(client, token)
    r = client.post(
        f"/api/v1/supports/{support_id}/error-cards/analyze",
        json={
            "user_message": "x" * 10001,
            "assistant_message": "réponse",
            "model": "llama3",
        },
        headers=_auth(token),
    )
    assert r.status_code == 422


def test_analyze_llm_unavailable_returns_empty(client):
    """POST analyze retourne cards:[] quand le LLM est indisponible — pas de 500."""
    token, _ = _signup(client, "ana4@t.com")
    support_id = _create_support(client, token)

    with patch(
        "learning.supports.error_cards.service.ErrorCardsService.analyze_exchange",
        new_callable=AsyncMock,
        return_value=[],
    ):
        r = client.post(
            f"/api/v1/supports/{support_id}/error-cards/analyze",
            json={
                "user_message": "Est-ce que 2+2=5 ?",
                "assistant_message": "Non, 2+2=4.",
                "model": "llama3",
            },
            headers=_auth(token),
        )
    assert r.status_code == 200
    assert r.json() == {"cards": []}


# ── DELETE /supports/{id}/error-cards/{card_id} ──────────────────────────────


def test_delete_card_unauthenticated(client):
    """DELETE sans token → 403 (HTTPBearer renvoie 403 quand le header est absent)."""
    r = client.delete("/api/v1/supports/fake/error-cards/fake")
    assert r.status_code == 403


def test_delete_card_not_found(client):
    """DELETE sur un card_id inexistant → 404."""
    token, _ = _signup(client, "del1@t.com")
    support_id = _create_support(client, token)
    r = client.delete(
        f"/api/v1/supports/{support_id}/error-cards/nonexistent-card",
        headers=_auth(token),
    )
    assert r.status_code == 404


def test_delete_card_success(client, db):
    """DELETE sur une fiche existante → 200, fiche disparaît du GET."""
    token, user_id = _signup(client, "del2@t.com")
    support_id = _create_support(client, token)
    card = _insert_card(db, support_id, user_id)

    r = client.delete(
        f"/api/v1/supports/{support_id}/error-cards/{card.id}",
        headers=_auth(token),
    )
    assert r.status_code == 200

    remaining = client.get(
        f"/api/v1/supports/{support_id}/error-cards", headers=_auth(token)
    ).json()
    assert remaining == []


def test_delete_card_wrong_support_id(client, db):
    """DELETE avec support_id incorrect → 404 (anti-IDOR)."""
    token, user_id = _signup(client, "del3@t.com")
    support_id = _create_support(client, token)
    other_support_id = _create_support(client, token)
    card = _insert_card(db, support_id, user_id)

    r = client.delete(
        f"/api/v1/supports/{other_support_id}/error-cards/{card.id}",
        headers=_auth(token),
    )
    assert r.status_code == 404


def test_delete_card_other_user(client, db):
    """DELETE sur la fiche d'un autre utilisateur → 404 (anti-IDOR)."""
    token_a, user_a = _signup(client, "del4a@t.com")
    token_b, _ = _signup(client, "del4b@t.com")
    support_id = _create_support(client, token_a)
    card = _insert_card(db, support_id, user_a)

    r = client.delete(
        f"/api/v1/supports/{support_id}/error-cards/{card.id}",
        headers=_auth(token_b),
    )
    assert r.status_code == 404


# ── Tests supplémentaires — couverture complète ───────────────────────────────


def test_analyze_empty_assistant_message(client):
    """POST analyze avec assistant_message vide → 422 (Field min_length=1)."""
    token, _ = _signup(client, "ana5@t.com")
    support_id = _create_support(client, token)
    r = client.post(
        f"/api/v1/supports/{support_id}/error-cards/analyze",
        json={"user_message": "question", "assistant_message": "", "model": "llama3"},
        headers=_auth(token),
    )
    assert r.status_code == 422


def test_analyze_empty_model(client):
    """POST analyze avec model vide → 422 (Field min_length=1)."""
    token, _ = _signup(client, "ana6@t.com")
    support_id = _create_support(client, token)
    r = client.post(
        f"/api/v1/supports/{support_id}/error-cards/analyze",
        json={"user_message": "question", "assistant_message": "réponse", "model": ""},
        headers=_auth(token),
    )
    assert r.status_code == 422


def test_list_cards_unknown_support_returns_empty(client):
    """GET sur un support inexistant → 200 avec liste vide (pas de 404)."""
    token, _ = _signup(client, "list3@t.com")
    r = client.get(
        "/api/v1/supports/support-qui-nexiste-pas/error-cards",
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json() == []


def test_list_cards_isolated_by_support(client, db):
    """Les fiches d'un support A n'apparaissent pas dans le GET du support B."""
    token, user_id = _signup(client, "list4@t.com")
    support_a = _create_support(client, token)
    support_b = _create_support(client, token)
    _insert_card(db, support_a, user_id)

    r = client.get(
        f"/api/v1/supports/{support_b}/error-cards",
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json() == []


def test_list_cards_multiple(client, db):
    """GET retourne toutes les fiches quand il y en a plusieurs."""
    token, user_id = _signup(client, "list5@t.com")
    support_id = _create_support(client, token)
    _insert_card(db, support_id, user_id)
    _insert_card(db, support_id, user_id)

    r = client.get(f"/api/v1/supports/{support_id}/error-cards", headers=_auth(token))
    assert r.status_code == 200
    assert len(r.json()) == 2


# ── Service unit tests — _extract_json ───────────────────────────────────────


def test_extract_json_valid():
    from learning.supports.error_cards.service import ErrorCardsService

    assert ErrorCardsService._extract_json('{"errors": []}') == {"errors": []}


def test_extract_json_with_markdown_fences():
    from learning.supports.error_cards.service import ErrorCardsService

    assert ErrorCardsService._extract_json('```json\n{"errors": []}\n```') == {
        "errors": []
    }


def test_extract_json_invalid_returns_none():
    from learning.supports.error_cards.service import ErrorCardsService

    assert ErrorCardsService._extract_json("pas du JSON") is None


def test_extract_json_empty_returns_none():
    from learning.supports.error_cards.service import ErrorCardsService

    assert ErrorCardsService._extract_json("") is None
    assert ErrorCardsService._extract_json(None) is None
