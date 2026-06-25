# Guide de test — Carte d'erreur instantanée

Ce fichier documente tous les tests à effectuer pour valider la fonctionnalité
Error Cards : tests automatisés (pytest), tests manuels (curl), et tests frontend.

---

## 1. Prérequis

```bash
# Environnement Python
~/.pyenv/versions/tutorai-env/bin/pytest -q

# Lancer les tests du projet
cd /home/kaoutar/Documents/projetopen/open-tutor-ai-CE
~/.pyenv/versions/tutorai-env/bin/pytest tests/ -v
```

Le projet utilise **SQLite en mémoire** pour les tests — aucune base externe requise.
Le `conftest.py` fournit les fixtures `db` (session SQLAlchemy) et `client` (TestClient).

---

## 2. Fichier à créer : `tests/test_error_cards.py`

Copier ce code dans `tests/test_error_cards.py` en suivant le pattern du projet.

```python
# tests/test_error_cards.py
"""Tests for error cards endpoints — POST analyze, GET list, DELETE."""

from unittest.mock import AsyncMock, patch


# ── Helpers ──────────────────────────────────────────────────────────────────


def _signup(client, email="ec@t.com"):
    r = client.post(
        "/auths/signup",
        json={"email": email, "name": "Student", "password": "pass1234!"},
    )
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _create_support(client, token):
    r = client.post(
        "/api/v1/supports/create",
        json={"title": "Maths Support"},
        headers=_auth(token),
    )
    assert r.status_code == 200
    return r.json()["id"]


def _create_card(client, token, support_id):
    """Insert a card directly via the repository (bypasses LLM)."""
    from data.database import get_db
    from learning.supports.error_cards.repository import ErrorCardRepository

    db = next(get_db())
    repo = ErrorCardRepository(db)
    card = repo.create(
        support_id=support_id,
        user_id=_get_user_id(client, token),
        concept="Dérivée",
        error_description="Mauvaise application de la règle.",
        simple_explanation="La règle de la chaîne s'applique aux fonctions composées.",
        correct_example="Si f(x) = sin(x²), alors f'(x) = cos(x²) · 2x",
        source_user_message="Est-ce que f'(x) = 2x ?",
        source_assistant_message="Presque, il faut appliquer la règle de la chaîne.",
    )
    return card.id


def _get_user_id(client, token):
    r = client.get("/api/v1/auths/", headers=_auth(token))
    return r.json()["id"]


# ── GET /supports/{id}/error-cards ───────────────────────────────────────────


def test_list_error_cards_empty(client):
    """GET returns empty list when no cards exist for this support."""
    token = _signup(client, "list1@t.com")
    support_id = _create_support(client, token)

    r = client.get(
        f"/api/v1/supports/{support_id}/error-cards",
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json() == []


def test_list_error_cards_unauthenticated(client):
    """GET without token returns 401."""
    r = client.get("/api/v1/supports/fake-id/error-cards")
    assert r.status_code == 401


def test_list_error_cards_scoped_to_user(client):
    """GET only returns cards belonging to the authenticated user."""
    token_a = _signup(client, "usera@t.com")
    token_b = _signup(client, "userb@t.com")
    support_a = _create_support(client, token_a)
    support_b = _create_support(client, token_b)

    _create_card(client, token_a, support_a)

    # User B cannot see User A's cards
    r = client.get(
        f"/api/v1/supports/{support_a}/error-cards",
        headers=_auth(token_b),
    )
    assert r.status_code == 200
    assert r.json() == []


# ── POST /supports/{id}/error-cards/analyze ──────────────────────────────────


def test_analyze_unauthenticated(client):
    """POST analyze without token returns 401."""
    r = client.post(
        "/api/v1/supports/fake-id/error-cards/analyze",
        json={
            "user_message": "test",
            "assistant_message": "test",
            "model": "llama3",
        },
    )
    assert r.status_code == 401


def test_analyze_support_not_found(client):
    """POST analyze on a non-existent support returns 404."""
    token = _signup(client, "ana1@t.com")
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


def test_analyze_missing_user_message(client):
    """POST analyze with empty user_message returns 422 (Field validation)."""
    token = _signup(client, "ana2@t.com")
    support_id = _create_support(client, token)
    r = client.post(
        f"/api/v1/supports/{support_id}/error-cards/analyze",
        json={
            "user_message": "",          # min_length=1 → 422
            "assistant_message": "réponse",
            "model": "llama3",
        },
        headers=_auth(token),
    )
    assert r.status_code == 422


def test_analyze_message_too_long(client):
    """POST analyze with user_message > 10000 chars returns 422."""
    token = _signup(client, "ana3@t.com")
    support_id = _create_support(client, token)
    r = client.post(
        f"/api/v1/supports/{support_id}/error-cards/analyze",
        json={
            "user_message": "x" * 10001,    # max_length=10000 → 422
            "assistant_message": "réponse",
            "model": "llama3",
        },
        headers=_auth(token),
    )
    assert r.status_code == 422


def test_analyze_llm_unavailable_returns_empty(client):
    """POST analyze returns { cards: [] } when LLM is unreachable — no 500."""
    token = _signup(client, "ana4@t.com")
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
    """DELETE without token returns 401."""
    r = client.delete("/api/v1/supports/fake/error-cards/fake")
    assert r.status_code == 401


def test_delete_card_not_found(client):
    """DELETE on non-existent card_id returns 404."""
    token = _signup(client, "del1@t.com")
    support_id = _create_support(client, token)
    r = client.delete(
        f"/api/v1/supports/{support_id}/error-cards/nonexistent-card",
        headers=_auth(token),
    )
    assert r.status_code == 404


def test_delete_card_wrong_support_id(client):
    """DELETE with mismatched support_id returns 404 (anti-IDOR)."""
    token = _signup(client, "del2@t.com")
    support_id = _create_support(client, token)
    other_support_id = _create_support(client, token)
    card_id = _create_card(client, token, support_id)

    # Card belongs to support_id, not other_support_id → 404
    r = client.delete(
        f"/api/v1/supports/{other_support_id}/error-cards/{card_id}",
        headers=_auth(token),
    )
    assert r.status_code == 404


def test_delete_card_other_user(client):
    """DELETE on another user's card returns 404 (anti-IDOR)."""
    token_a = _signup(client, "del3a@t.com")
    token_b = _signup(client, "del3b@t.com")
    support_id = _create_support(client, token_a)
    card_id = _create_card(client, token_a, support_id)

    # User B tries to delete User A's card
    r = client.delete(
        f"/api/v1/supports/{support_id}/error-cards/{card_id}",
        headers=_auth(token_b),
    )
    assert r.status_code == 404


# ── Service unit test — _extract_json ────────────────────────────────────────


def test_extract_json_valid():
    """_extract_json parses plain JSON correctly."""
    from learning.supports.error_cards.service import ErrorCardsService
    result = ErrorCardsService._extract_json('{"errors": []}')
    assert result == {"errors": []}


def test_extract_json_with_markdown_fences():
    """_extract_json strips ```json fences before parsing."""
    from learning.supports.error_cards.service import ErrorCardsService
    raw = '```json\n{"errors": []}\n```'
    result = ErrorCardsService._extract_json(raw)
    assert result == {"errors": []}


def test_extract_json_invalid_returns_none():
    """_extract_json returns None on unparseable content."""
    from learning.supports.error_cards.service import ErrorCardsService
    result = ErrorCardsService._extract_json("Ce n'est pas du JSON")
    assert result is None


def test_extract_json_empty_returns_none():
    """_extract_json returns None on empty input."""
    from learning.supports.error_cards.service import ErrorCardsService
    assert ErrorCardsService._extract_json("") is None
    assert ErrorCardsService._extract_json(None) is None
```

---

## 3. Lancer uniquement les tests error cards

```bash
~/.pyenv/versions/tutorai-env/bin/pytest tests/test_error_cards.py -v
```

Résultat attendu :

```
tests/test_error_cards.py::test_list_error_cards_empty                PASSED
tests/test_error_cards.py::test_list_error_cards_unauthenticated      PASSED
tests/test_error_cards.py::test_list_error_cards_scoped_to_user       PASSED
tests/test_error_cards.py::test_analyze_unauthenticated               PASSED
tests/test_error_cards.py::test_analyze_support_not_found             PASSED
tests/test_error_cards.py::test_analyze_missing_user_message          PASSED
tests/test_error_cards.py::test_analyze_message_too_long              PASSED
tests/test_error_cards.py::test_analyze_llm_unavailable_returns_empty PASSED
tests/test_error_cards.py::test_delete_card_unauthenticated           PASSED
tests/test_error_cards.py::test_delete_card_not_found                 PASSED
tests/test_error_cards.py::test_delete_card_wrong_support_id          PASSED
tests/test_error_cards.py::test_delete_card_other_user                PASSED
tests/test_error_cards.py::test_extract_json_valid                    PASSED
tests/test_error_cards.py::test_extract_json_with_markdown_fences     PASSED
tests/test_error_cards.py::test_extract_json_invalid_returns_none     PASSED
tests/test_error_cards.py::test_extract_json_empty_returns_none       PASSED

16 passed in 0.XX s
```

---

## 4. Test manuel avec curl

### Signup et récupération du token

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auths/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@t.com","name":"Test","password":"pass1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
```

### Créer un support

```bash
SUPPORT_ID=$(curl -s -X POST http://localhost:8000/api/v1/supports/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Support"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

### Analyser un échange (retourne [] si LLM absent)

```bash
curl -X POST http://localhost:8000/api/v1/supports/$SUPPORT_ID/error-cards/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "Est-ce que f(x)=x² a comme dérivée f(x)=2 ?",
    "assistant_message": "Non, la dérivée de x² est 2x, pas 2.",
    "model": "llama3"
  }'
# Réponse attendue : { "cards": [...] } ou { "cards": [] }
```

### Lister les fiches

```bash
curl http://localhost:8000/api/v1/supports/$SUPPORT_ID/error-cards \
  -H "Authorization: Bearer $TOKEN"
```

### Supprimer une fiche

```bash
curl -X DELETE \
  http://localhost:8000/api/v1/supports/$SUPPORT_ID/error-cards/<card_id> \
  -H "Authorization: Bearer $TOKEN"
```

### Vérifier la protection IDOR (doit retourner 404)

```bash
curl -X DELETE \
  http://localhost:8000/api/v1/supports/wrong-support-id/error-cards/<card_id> \
  -H "Authorization: Bearer $TOKEN"
# Attendu : 404
```

---

## 5. Test frontend

| Action | Résultat attendu |
|--------|-----------------|
| Ouvrir `/student/support/:id` | Panneau "Rapport d'erreurs" visible sous le chat |
| Envoyer un message contenant une erreur | Toast après quelques secondes, badge incrémenté |
| Envoyer un message correct | Aucun toast, aucune nouvelle fiche |
| Cliquer sur l'en-tête du panneau | Panneau se déplie / se replie |
| Cliquer sur l'icône corbeille d'une fiche | Fiche supprimée, badge décrémenté |
| Cliquer sur "↓ PDF" | Fenêtre d'impression Chrome s'ouvre avec toutes les fiches |
| Ouvrir la page sans être connecté | Redirection vers `/auth` |

---

## 6. Couverture du contrat UI ↔ API

Le test `tests/test_contract_coverage.py` vérifie que chaque `fetch()` dans
`ui/src/lib/apis/` a un endpoint backend correspondant.

Les routes error-cards sont déjà implémentées et n'ont **pas** besoin d'être
ajoutées à `_SCANNED_PATH_EXCLUSIONS`. Si le test échoue avec ces routes,
vérifier que le router est bien enregistré dans `gateway/http/app.py`.

```bash
~/.pyenv/versions/tutorai-env/bin/pytest tests/test_contract_coverage.py -v
```
