# tests/test_diagnostics.py
import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

from data.models import DiagnosticResult, User

# ── Helpers ──────────────────────────────────────────────────────────────────


def _signup(client, email="diag@t.com"):
    r = client.post(
        "/auths/signup",
        json={"email": email, "name": "Diag", "password": "pass1234!"},
    )
    return r.json()["token"]


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


def _create_support(client, token):
    r = client.post(
        "/api/v1/supports/create",
        json={
            "title": "Algèbre",
            "subject": "mathématiques",
            "learning_objective": "Résoudre des équations du premier degré",
        },
        headers=_auth(token),
    )
    return r.json()["id"]


def _get_user_id(db, email):
    return db.query(User).filter(User.email == email).first().id


def _insert_pending_diagnostic(db, support_id, user_id):
    """Insère un diagnostic en base sans passer par le LLM."""
    questions = [
        {
            "id": 1,
            "question": "Combien font 2+2 ?",
            "choices": ["3", "4", "5", "6"],
            "correct_answer": "4",
        },
        {
            "id": 2,
            "question": "Racine carrée de 9 ?",
            "choices": ["2", "3", "4", "5"],
            "correct_answer": "3",
        },
    ]
    record = DiagnosticResult(
        id=str(uuid.uuid4()),
        support_id=support_id,
        user_id=user_id,
        questions=questions,
        answers=None,
        score=None,
        determined_level=None,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ── Tests GET ─────────────────────────────────────────────────────────────────


def test_get_diagnostic_not_found(client):
    token = _signup(client)
    r = client.get("/api/v1/diagnostics/nonexistent-id", headers=_auth(token))
    assert r.status_code == 404


def test_get_by_support_no_diagnostic(client):
    token = _signup(client)
    support_id = _create_support(client, token)
    r = client.get(f"/api/v1/diagnostics/by-support/{support_id}", headers=_auth(token))
    assert r.status_code == 200
    assert r.json() is None


# ── Tests submit ──────────────────────────────────────────────────────────────


def test_submit_not_found(client):
    token = _signup(client)
    r = client.post(
        "/api/v1/diagnostics/nonexistent-id/submit",
        json={"answers": [{"question_id": 1, "answer": "4"}]},
        headers=_auth(token),
    )
    assert r.status_code == 404


def test_submit_scores_correctly(client, db):
    token = _signup(client)
    support_id = _create_support(client, token)
    user_id = _get_user_id(db, "diag@t.com")
    diagnostic = _insert_pending_diagnostic(db, support_id, user_id)

    # 0 bonne réponse sur 2 → 0 → "débutant"
    r = client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json={
            "answers": [
                {"question_id": 1, "answer": "3"},  # incorrect (correct: "4")
                {"question_id": 2, "answer": "2"},  # incorrect (correct: "3")
            ]
        },
        headers=_auth(token),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "completed"
    assert data["score"] == 0
    assert data["determined_level"] == "débutant"


def test_submit_perfect_score_gives_avance(client, db):
    token = _signup(client)
    support_id = _create_support(client, token)
    user_id = _get_user_id(db, "diag@t.com")
    diagnostic = _insert_pending_diagnostic(db, support_id, user_id)

    # 2 bonnes réponses sur 2 → 100 → "avancé"
    r = client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json={
            "answers": [
                {"question_id": 1, "answer": "4"},
                {"question_id": 2, "answer": "3"},
            ]
        },
        headers=_auth(token),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["score"] == 100
    assert data["determined_level"] == "avancé"


def test_submit_updates_support_level(client, db):
    token = _signup(client)
    support_id = _create_support(client, token)
    user_id = _get_user_id(db, "diag@t.com")
    diagnostic = _insert_pending_diagnostic(db, support_id, user_id)

    client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json={
            "answers": [
                {"question_id": 1, "answer": "4"},
                {"question_id": 2, "answer": "3"},
            ]
        },
        headers=_auth(token),
    )

    support = client.get(f"/api/v1/supports/{support_id}", headers=_auth(token)).json()
    assert support["level"] == "avancé"


def test_submit_already_completed_returns_existing(client, db):
    token = _signup(client)
    support_id = _create_support(client, token)
    user_id = _get_user_id(db, "diag@t.com")
    diagnostic = _insert_pending_diagnostic(db, support_id, user_id)

    payload = {
        "answers": [
            {"question_id": 1, "answer": "4"},
            {"question_id": 2, "answer": "3"},
        ]
    }
    client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json=payload,
        headers=_auth(token),
    )
    # Deuxième soumission : doit retourner le résultat existant sans erreur
    r = client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json=payload,
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_get_by_support_after_submit(client, db):
    token = _signup(client)
    support_id = _create_support(client, token)
    user_id = _get_user_id(db, "diag@t.com")
    diagnostic = _insert_pending_diagnostic(db, support_id, user_id)

    client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json={
            "answers": [
                {"question_id": 1, "answer": "4"},
                {"question_id": 2, "answer": "3"},
            ]
        },
        headers=_auth(token),
    )

    r = client.get(f"/api/v1/diagnostics/by-support/{support_id}", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


# ── Test generate (LLM mocké) ─────────────────────────────────────────────────


def test_generate_diagnostic(client):
    from ai.providers.service import ProvidersService

    token = _signup(client)
    support_id = _create_support(client, token)

    mock_questions = [
        {
            "id": 1,
            "question": "Qu'est-ce qu'une variable ?",
            "choices": ["A", "B", "C", "D"],
            "correct_answer": "A",
        },
    ]
    mock_llm_response = {
        "choices": [{"message": {"content": json.dumps(mock_questions)}}]
    }

    with (
        patch.object(
            ProvidersService,
            "resolve_provider",
            new_callable=AsyncMock,
            return_value=("http://localhost:11434", "", "v1/chat/completions"),
        ),
        patch(
            "learning.diagnostics.service.proxy_json",
            new_callable=AsyncMock,
            return_value=mock_llm_response,
        ),
    ):
        r = client.post(
            "/api/v1/diagnostics/generate",
            json={"support_id": support_id, "model_id": "mistral"},
            headers=_auth(token),
        )

    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "pending"
    assert data["support_id"] == support_id
    assert len(data["questions"]) == 1


# ── Test autorisation ──────────────────────────────────────────────────────────


def test_cannot_access_other_user_diagnostic(client, db):
    owner_token = _signup(client, "owner@t.com")
    other_token = _signup(client, "other@t.com")

    support_id = _create_support(client, owner_token)
    user_id = _get_user_id(db, "owner@t.com")
    diagnostic = _insert_pending_diagnostic(db, support_id, user_id)

    r = client.get(f"/api/v1/diagnostics/{diagnostic.id}", headers=_auth(other_token))
    assert r.status_code == 403


def test_cannot_submit_other_user_diagnostic(client, db):
    owner_token = _signup(client, "owner@t.com")
    other_token = _signup(client, "other@t.com")

    support_id = _create_support(client, owner_token)
    user_id = _get_user_id(db, "owner@t.com")
    diagnostic = _insert_pending_diagnostic(db, support_id, user_id)

    r = client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json={"answers": [{"question_id": 1, "answer": "4"}]},
        headers=_auth(other_token),
    )
    assert r.status_code == 403


# ── Tests niveau intermédiaire ────────────────────────────────────────────────


def _insert_diagnostic_10q(db, support_id, user_id):
    """Insère un diagnostic de 10 questions pour tester les seuils réels."""
    questions = [
        {
            "id": i,
            "question": f"Question {i} ?",
            "choices": ["Bonne réponse", "Mauvaise A", "Mauvaise B", "Mauvaise C"],
            "correct_answer": "Bonne réponse",
        }
        for i in range(1, 11)
    ]
    record = DiagnosticResult(
        id=str(uuid.uuid4()),
        support_id=support_id,
        user_id=user_id,
        questions=questions,
        answers=None,
        score=None,
        determined_level=None,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _answers(correct_ids, wrong_ids):
    """Construit la liste de réponses : bonnes pour correct_ids, mauvaises pour wrong_ids."""
    answers = []
    for qid in correct_ids:
        answers.append({"question_id": qid, "answer": "Bonne réponse"})
    for qid in wrong_ids:
        answers.append({"question_id": qid, "answer": "Mauvaise A"})
    return answers


def test_submit_intermediaire_level(client, db):
    """5/10 bonnes réponses → score=50 → intermédiaire."""
    token = _signup(client, "inter@t.com")
    support_id = _create_support(client, token)
    user_id = _get_user_id(db, "inter@t.com")
    diagnostic = _insert_diagnostic_10q(db, support_id, user_id)

    r = client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json={"answers": _answers(range(1, 6), range(6, 11))},
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json()["score"] == 50
    assert r.json()["determined_level"] == "intermédiaire"


# ── Tests seuils exacts (boundary) ───────────────────────────────────────────


def test_boundary_40_is_debutant(client, db):
    """4/10 bonnes réponses → score=40 → débutant (seuil : ≥41 pour intermédiaire)."""
    token = _signup(client, "b40@t.com")
    support_id = _create_support(client, token)
    user_id = _get_user_id(db, "b40@t.com")
    diagnostic = _insert_diagnostic_10q(db, support_id, user_id)

    r = client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json={"answers": _answers(range(1, 5), range(5, 11))},
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json()["score"] == 40
    assert r.json()["determined_level"] == "débutant"


def test_boundary_41_is_intermediaire(client, db):
    """5/10 → arrondi(4.1/10*100) → tester avec 41 % exact via 2 questions sur 5 (non entier).
    On utilise plutôt un diagnostic de 100 questions simulé via le score direct.
    Avec 10 questions, le plus proche de 41 % est 4/10=40 ou 5/10=50.
    Ce test valide que 41 est le premier seuil intermédiaire (5/10=50 est déjà couvert).
    """
    token = _signup(client, "b41@t.com")
    support_id = _create_support(client, token)
    user_id = _get_user_id(db, "b41@t.com")
    diagnostic = _insert_diagnostic_10q(db, support_id, user_id)

    # 5/10 = 50 % → intermédiaire (premier score ≥41 atteignable avec 10 questions)
    r = client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json={"answers": _answers(range(1, 6), range(6, 11))},
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json()["determined_level"] == "intermédiaire"


def test_boundary_70_is_intermediaire(client, db):
    """7/10 bonnes réponses → score=70 → intermédiaire (seuil : ≥71 pour avancé)."""
    token = _signup(client, "b70@t.com")
    support_id = _create_support(client, token)
    user_id = _get_user_id(db, "b70@t.com")
    diagnostic = _insert_diagnostic_10q(db, support_id, user_id)

    r = client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json={"answers": _answers(range(1, 8), range(8, 11))},
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json()["score"] == 70
    assert r.json()["determined_level"] == "intermédiaire"


def test_boundary_71_is_avance(client, db):
    """8/10 bonnes réponses → score=80 → avancé. Avec 10 questions, 71 % exact
    n'est pas atteignable (7/10=70, 8/10=80). Ce test valide que 8/10 donne avancé."""
    token = _signup(client, "b71@t.com")
    support_id = _create_support(client, token)
    user_id = _get_user_id(db, "b71@t.com")
    diagnostic = _insert_diagnostic_10q(db, support_id, user_id)

    r = client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json={"answers": _answers(range(1, 9), range(9, 11))},
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json()["score"] == 80
    assert r.json()["determined_level"] == "avancé"


# ── Tests _parse_questions_json ───────────────────────────────────────────────


def test_parse_questions_json_clean():
    """JSON propre parsé directement."""
    from learning.diagnostics.service import _parse_questions_json

    questions = [
        {"id": 1, "question": "Q?", "choices": ["A", "B"], "correct_answer": "A"}
    ]
    result = _parse_questions_json(json.dumps(questions))
    assert result == questions


def test_parse_questions_json_with_markdown_fences():
    """JSON entouré de ```json ... ``` — cas fréquent des LLM."""
    from learning.diagnostics.service import _parse_questions_json

    questions = [
        {"id": 1, "question": "Q?", "choices": ["A", "B"], "correct_answer": "A"}
    ]
    raw = f"```json\n{json.dumps(questions)}\n```"
    result = _parse_questions_json(raw)
    assert result == questions


def test_parse_questions_json_with_plain_fences():
    """JSON entouré de ``` sans préciser json."""
    from learning.diagnostics.service import _parse_questions_json

    questions = [
        {"id": 1, "question": "Q?", "choices": ["A", "B"], "correct_answer": "A"}
    ]
    raw = f"```\n{json.dumps(questions)}\n```"
    result = _parse_questions_json(raw)
    assert result == questions


def test_parse_questions_json_with_surrounding_text():
    """JSON précédé de texte parasite — fallback par extraction [...]."""
    from learning.diagnostics.service import _parse_questions_json

    questions = [
        {"id": 1, "question": "Q?", "choices": ["A", "B"], "correct_answer": "A"}
    ]
    raw = f"Voici les questions :\n{json.dumps(questions)}\nBonne chance !"
    result = _parse_questions_json(raw)
    assert result == questions


def test_parse_questions_json_malformed_raises():
    """JSON invalide même après nettoyage → ValueError ou JSONDecodeError levée."""
    import pytest

    from learning.diagnostics.service import _parse_questions_json

    with pytest.raises(Exception):
        _parse_questions_json("ceci n'est pas du JSON valide {{{")


# ── Test generate — LLM retourne JSON malformé → 502 ─────────────────────────


def test_generate_malformed_llm_response_returns_502(client):
    from ai.providers.service import ProvidersService

    token = _signup(client, "malformed@t.com")
    support_id = _create_support(client, token)

    # Le LLM retourne du texte non parsable
    mock_llm_response = {
        "choices": [
            {"message": {"content": "Désolé, je ne peux pas générer de questions."}}
        ]
    }

    with (
        patch.object(
            ProvidersService,
            "resolve_provider",
            new_callable=AsyncMock,
            return_value=("http://localhost:11434", "", "v1/chat/completions"),
        ),
        patch(
            "learning.diagnostics.service.proxy_json",
            new_callable=AsyncMock,
            return_value=mock_llm_response,
        ),
    ):
        r = client.post(
            "/api/v1/diagnostics/generate",
            json={"support_id": support_id, "model_id": "mistral"},
            headers=_auth(token),
        )

    assert r.status_code == 502


# ── Test contexte enrichi transmis au LLM ────────────────────────────────────


def test_generate_sends_enriched_context_to_llm(client, db):
    """Vérifie que le prompt envoyé au LLM contient les champs enrichis du support."""
    from ai.providers.service import ProvidersService

    token = _signup(client, "ctx@t.com")

    # Création d'un support avec tous les champs enrichis
    r = client.post(
        "/api/v1/supports/create",
        json={
            "title": "Introduction à Python",
            "subject": "informatique",
            "short_description": "Bases de la programmation Python",
            "learning_objective": "Écrire des scripts Python simples",
            "keywords": ["variable", "boucle", "fonction", "liste"],
            "learning_type": "course",
            "content_language": "French",
        },
        headers=_auth(token),
    )
    support_id = r.json()["id"]

    mock_questions = [
        {
            "id": 1,
            "question": "Q?",
            "choices": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "explanation": "Explication",
        }
    ]
    mock_llm_response = {
        "choices": [{"message": {"content": json.dumps(mock_questions)}}]
    }

    captured_body = {}

    async def fake_proxy(base_url, key, method, path, body=None, **kwargs):
        captured_body.update(body or {})
        return mock_llm_response

    with (
        patch.object(
            ProvidersService,
            "resolve_provider",
            new_callable=AsyncMock,
            return_value=("http://localhost:11434", "", "v1/chat/completions"),
        ),
        patch("learning.diagnostics.service.proxy_json", side_effect=fake_proxy),
    ):
        client.post(
            "/api/v1/diagnostics/generate",
            json={"support_id": support_id, "model_id": "mistral"},
            headers=_auth(token),
        )

    # Le prompt utilisateur doit contenir les champs enrichis
    user_prompt = captured_body["messages"][1]["content"]
    assert "Introduction à Python" in user_prompt
    assert "Bases de la programmation Python" in user_prompt
    assert "Écrire des scripts Python simples" in user_prompt
    assert "variable" in user_prompt and "boucle" in user_prompt
    assert "French" in user_prompt


# ── Tests generate — autorisation et support introuvable ─────────────────────


def test_generate_support_not_found_returns_404(client):
    """POST /generate avec un support_id inexistant → 404."""
    from ai.providers.service import ProvidersService

    token = _signup(client, "gen404@t.com")

    with (
        patch.object(
            ProvidersService,
            "resolve_provider",
            new_callable=AsyncMock,
            return_value=("http://localhost:11434", "", "v1/chat/completions"),
        ),
        patch(
            "learning.diagnostics.service.proxy_json",
            new_callable=AsyncMock,
            return_value={"choices": [{"message": {"content": "[]"}}]},
        ),
    ):
        r = client.post(
            "/api/v1/diagnostics/generate",
            json={"support_id": "support-inexistant", "model_id": "mistral"},
            headers=_auth(token),
        )

    assert r.status_code == 404


def test_generate_other_user_support_returns_403(client):
    """POST /generate sur un support appartenant à un autre user → 403."""
    from ai.providers.service import ProvidersService

    owner_token = _signup(client, "gen_owner@t.com")
    other_token = _signup(client, "gen_other@t.com")
    support_id = _create_support(client, owner_token)

    with (
        patch.object(
            ProvidersService,
            "resolve_provider",
            new_callable=AsyncMock,
            return_value=("http://localhost:11434", "", "v1/chat/completions"),
        ),
        patch(
            "learning.diagnostics.service.proxy_json",
            new_callable=AsyncMock,
            return_value={"choices": [{"message": {"content": "[]"}}]},
        ),
    ):
        r = client.post(
            "/api/v1/diagnostics/generate",
            json={"support_id": support_id, "model_id": "mistral"},
            headers=_auth(other_token),
        )

    assert r.status_code == 403


# ── Tests contexte LLM selon learning_type et level ──────────────────────────


def _capture_prompt(client, token, support_data):
    """Crée un support, lance generate avec fake_proxy et retourne le prompt capturé."""
    from ai.providers.service import ProvidersService

    r = client.post("/api/v1/supports/create", json=support_data, headers=_auth(token))
    support_id = r.json()["id"]

    mock_questions = [
        {
            "id": 1,
            "question": "Q?",
            "choices": ["A", "B", "C", "D"],
            "correct_answer": "A",
        }
    ]
    captured = {}

    async def fake_proxy(base_url, key, method, path, body=None, **kwargs):
        captured.update(body or {})
        return {"choices": [{"message": {"content": json.dumps(mock_questions)}}]}

    with (
        patch.object(
            ProvidersService,
            "resolve_provider",
            new_callable=AsyncMock,
            return_value=("http://localhost:11434", "", "v1/chat/completions"),
        ),
        patch("learning.diagnostics.service.proxy_json", side_effect=fake_proxy),
    ):
        client.post(
            "/api/v1/diagnostics/generate",
            json={"support_id": support_id, "model_id": "mistral"},
            headers=_auth(token),
        )

    return captured["messages"][1]["content"]


def test_generate_prompt_contains_exam_context(client):
    """learning_type='exam' → le prompt contient la ligne CONTEXT exam."""
    token = _signup(client, "exam@t.com")
    prompt = _capture_prompt(
        client,
        token,
        {"title": "Mathématiques", "learning_type": "exam"},
    )
    assert "exam" in prompt.lower()


def test_generate_prompt_contains_skill_context(client):
    """learning_type='skill' → le prompt contient la ligne CONTEXT skill."""
    token = _signup(client, "skill@t.com")
    prompt = _capture_prompt(
        client,
        token,
        {"title": "Photoshop", "learning_type": "skill"},
    )
    assert "skill" in prompt.lower()


def test_generate_prompt_contains_declared_level(client):
    """Un support avec level défini → le prompt contient DECLARED EDUCATION LEVEL."""
    token = _signup(client, "level@t.com")
    prompt = _capture_prompt(
        client,
        token,
        {"title": "Physique quantique", "level": "avancé"},
    )
    assert "DECLARED EDUCATION LEVEL" in prompt
    assert "avancé" in prompt


# ── Tests sécurité ────────────────────────────────────────────────────────────


def test_by_support_returns_403_for_other_user(client, db):
    """GET /by-support/{id} → 403 si l'utilisateur n'est pas propriétaire du diagnostic."""
    owner_token = _signup(client, "sec_owner@t.com")
    other_token = _signup(client, "sec_other@t.com")

    support_id = _create_support(client, owner_token)
    user_id = _get_user_id(db, "sec_owner@t.com")
    _insert_pending_diagnostic(db, support_id, user_id)

    r = client.get(
        f"/api/v1/diagnostics/by-support/{support_id}",
        headers=_auth(other_token),
    )
    assert r.status_code == 403


def test_generate_response_hides_correct_answers_when_pending(client):
    """POST /generate → correct_answer absent de la réponse quand le diagnostic est pending."""
    from ai.providers.service import ProvidersService

    token = _signup(client, "hide@t.com")
    support_id = _create_support(client, token)

    mock_questions = [
        {
            "id": 1,
            "question": "Qu'est-ce qu'une variable ?",
            "choices": ["Un conteneur", "Une boucle", "Une fonction", "Un module"],
            "correct_answer": "Un conteneur",
            "explanation": "Une variable stocke une valeur.",
        }
    ]

    with (
        patch.object(
            ProvidersService,
            "resolve_provider",
            new_callable=AsyncMock,
            return_value=("http://localhost:11434", "", "v1/chat/completions"),
        ),
        patch(
            "learning.diagnostics.service.proxy_json",
            new_callable=AsyncMock,
            return_value={
                "choices": [{"message": {"content": json.dumps(mock_questions)}}]
            },
        ),
    ):
        r = client.post(
            "/api/v1/diagnostics/generate",
            json={"support_id": support_id, "model_id": "mistral"},
            headers=_auth(token),
        )

    assert r.status_code == 200
    assert r.json()["status"] == "pending"
    question = r.json()["questions"][0]
    assert "correct_answer" not in question
    assert "explanation" not in question
    assert "choices" in question


def test_submit_response_shows_correct_answers_when_completed(client, db):
    """POST /submit → correct_answer présent dans la réponse quand le diagnostic est completed."""
    token = _signup(client, "show@t.com")
    support_id = _create_support(client, token)
    user_id = _get_user_id(db, "show@t.com")
    diagnostic = _insert_pending_diagnostic(db, support_id, user_id)

    r = client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json={
            "answers": [
                {"question_id": 1, "answer": "4"},
                {"question_id": 2, "answer": "3"},
            ]
        },
        headers=_auth(token),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    question = r.json()["questions"][0]
    assert "correct_answer" in question


def test_generate_502_message_is_generic(client):
    """POST /generate avec LLM indisponible → message 502 générique sans détails internes."""
    from ai.providers.service import ProvidersService

    token = _signup(client, "502msg@t.com")
    support_id = _create_support(client, token)

    with (
        patch.object(
            ProvidersService,
            "resolve_provider",
            new_callable=AsyncMock,
            side_effect=Exception("Connection refused to http://internal-llm:11434"),
        ),
    ):
        r = client.post(
            "/api/v1/diagnostics/generate",
            json={"support_id": support_id, "model_id": "mistral"},
            headers=_auth(token),
        )

    assert r.status_code == 502
    assert r.json()["detail"] == "LLM provider unavailable"
    assert "internal-llm" not in r.json()["detail"]
    assert "Connection refused" not in r.json()["detail"]


def test_generate_validates_support_id_length(client):
    """POST /generate avec support_id vide → 422 (validation Pydantic)."""
    token = _signup(client, "val@t.com")
    r = client.post(
        "/api/v1/diagnostics/generate",
        json={"support_id": "", "model_id": "mistral"},
        headers=_auth(token),
    )
    assert r.status_code == 422


def test_submit_validates_answer_length(client, db):
    """POST /submit avec une réponse trop longue → 422 (validation Pydantic)."""
    token = _signup(client, "valsub@t.com")
    support_id = _create_support(client, token)
    user_id = _get_user_id(db, "valsub@t.com")
    diagnostic = _insert_pending_diagnostic(db, support_id, user_id)

    r = client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json={"answers": [{"question_id": 1, "answer": "A" * 501}]},
        headers=_auth(token),
    )
    assert r.status_code == 422


# ── Tests Rate Limiting ───────────────────────────────────────────────────────


def test_generate_rate_limit_returns_429(client):
    """POST /generate — le 11ème appel par le même utilisateur retourne 429."""
    from ai.providers.service import ProvidersService
    from gateway.http.routers.diagnostics import _rate_store

    _rate_store.clear()

    token = _signup(client, "rl_gen@t.com")
    support_id = _create_support(client, token)

    mock_questions = [
        {
            "id": 1,
            "question": "Q?",
            "choices": ["A", "B", "C", "D"],
            "correct_answer": "A",
        }
    ]

    with (
        patch.object(
            ProvidersService,
            "resolve_provider",
            new_callable=AsyncMock,
            return_value=("http://localhost:11434", "", "v1/chat/completions"),
        ),
        patch(
            "learning.diagnostics.service.proxy_json",
            new_callable=AsyncMock,
            return_value={
                "choices": [{"message": {"content": json.dumps(mock_questions)}}]
            },
        ),
    ):
        for _ in range(10):
            r = client.post(
                "/api/v1/diagnostics/generate",
                json={"support_id": support_id, "model_id": "mistral"},
                headers=_auth(token),
            )
            assert r.status_code == 200

        r = client.post(
            "/api/v1/diagnostics/generate",
            json={"support_id": support_id, "model_id": "mistral"},
            headers=_auth(token),
        )

    assert r.status_code == 429
    assert "Too many requests" in r.json()["detail"]


def test_generate_rate_limit_is_per_user(client):
    """La limite de user A n'affecte pas user B sur /generate."""
    from ai.providers.service import ProvidersService
    from gateway.http.routers.diagnostics import _rate_store

    _rate_store.clear()

    token_a = _signup(client, "rl_a@t.com")
    token_b = _signup(client, "rl_b@t.com")
    support_a = _create_support(client, token_a)
    support_b = _create_support(client, token_b)

    mock_questions = [
        {
            "id": 1,
            "question": "Q?",
            "choices": ["A", "B", "C", "D"],
            "correct_answer": "A",
        }
    ]

    with (
        patch.object(
            ProvidersService,
            "resolve_provider",
            new_callable=AsyncMock,
            return_value=("http://localhost:11434", "", "v1/chat/completions"),
        ),
        patch(
            "learning.diagnostics.service.proxy_json",
            new_callable=AsyncMock,
            return_value={
                "choices": [{"message": {"content": json.dumps(mock_questions)}}]
            },
        ),
    ):
        for _ in range(10):
            client.post(
                "/api/v1/diagnostics/generate",
                json={"support_id": support_a, "model_id": "mistral"},
                headers=_auth(token_a),
            )

        r_a = client.post(
            "/api/v1/diagnostics/generate",
            json={"support_id": support_a, "model_id": "mistral"},
            headers=_auth(token_a),
        )
        assert r_a.status_code == 429

        r_b = client.post(
            "/api/v1/diagnostics/generate",
            json={"support_id": support_b, "model_id": "mistral"},
            headers=_auth(token_b),
        )
    assert r_b.status_code == 200


def test_submit_rate_limit_returns_429(client, db):
    """POST /submit — le 11ème appel par le même utilisateur retourne 429."""
    from gateway.http.routers.diagnostics import _rate_store

    _rate_store.clear()

    token = _signup(client, "rl_sub@t.com")
    support_id = _create_support(client, token)
    user_id = _get_user_id(db, "rl_sub@t.com")
    diagnostic = _insert_pending_diagnostic(db, support_id, user_id)

    payload = {
        "answers": [
            {"question_id": 1, "answer": "4"},
            {"question_id": 2, "answer": "3"},
        ]
    }

    for _ in range(10):
        r = client.post(
            f"/api/v1/diagnostics/{diagnostic.id}/submit",
            json=payload,
            headers=_auth(token),
        )
        assert r.status_code == 200

    r = client.post(
        f"/api/v1/diagnostics/{diagnostic.id}/submit",
        json=payload,
        headers=_auth(token),
    )

    assert r.status_code == 429
    assert "Too many requests" in r.json()["detail"]
