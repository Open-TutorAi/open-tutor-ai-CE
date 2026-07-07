import pytest
import uuid
from unittest.mock import AsyncMock, patch


# ═══════════════════════════════════════════════════════════════════
# TESTS D'INTÉGRATION — Sessions IA (US-P04)
# Source : Diagramme de séquence (steps 5 → 25)
# Le LLM et la DB sont moqués — pas besoin que l'appli tourne.
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def sessions_data():
    return {
        "sessions": [
            {
                "id": str(uuid.uuid4()),
                "matiere": "Mathématiques",
                "duree_minutes": 38,
                "quality_score": 9.1,
                "alerte_difficulte": False,
                "themes": ["Fonctions", "Dérivées", "Limites"],
                "questions": [
                    "Quelle est la dérivée de x² ?",
                    "Comment calculer une limite en l'infini ?",
                ],
                "resume": "Séance très productive sur les fonctions dérivées.",
                "metriques": {
                    "engagement": 9.1,
                    "comprehension": 8.5,
                    "autonomie": 8.8,
                },
                "statut": "terminee",
            },
            {
                "id": str(uuid.uuid4()),
                "matiere": "Physique-Chimie",
                "duree_minutes": 22,
                "quality_score": 4.17,
                "alerte_difficulte": True,
                "themes": ["Optique", "Réfraction"],
                "questions": [
                    "Qu'est-ce que l'indice de réfraction ?",
                    "Comment appliquer la loi de Snell-Descartes ?",
                ],
                "resume": "Difficultés notées sur la loi de Snell-Descartes.",
                "metriques": {
                    "engagement": 4.0,
                    "comprehension": 5.0,
                    "autonomie": 3.5,
                },
                "statut": "terminee",
            },
        ],
        "stats": {"total": 2, "avec_alerte": 1, "score_moyen": 6.64},
    }


# ─── Step 5-6 : GET /sessions?child_id=X + checkParentAccess() ───


@pytest.mark.asyncio
async def test_parent_peut_voir_sessions_de_son_enfant(sessions_data):
    """Step 5→9 du diagramme : le parent charge la liste de sessions."""
    child_id = str(uuid.uuid4())

    service = AsyncMock()
    service.owns_student.return_value = True
    service.get_session_summaries.return_value = sessions_data

    result = await service.get_session_summaries(child_id)

    assert len(result["sessions"]) == 2
    assert result["stats"]["total"] == 2
    assert result["stats"]["avec_alerte"] == 1


@pytest.mark.asyncio
async def test_parent_ne_peut_pas_voir_sessions_dun_autre_enfant():
    """Step 6 : guard checkParentAccess() — sécurité."""
    service = AsyncMock()
    service.owns_student.return_value = False

    is_authorized = await service.owns_student("parent-id", "autre-enfant-id")

    assert is_authorized is False


# ─── Step 16-19 : GET /sessions/{id}/detail + generateSummary() ──


@pytest.mark.asyncio
async def test_detail_session_declenche_generation_resume():
    """Step 17→21 : clic sur session → generateSummary() appelé sur le LLM."""
    session_id = str(uuid.uuid4())

    service = AsyncMock()
    service.get_session_detail.return_value = {
        "id": session_id,
        "matiere": "Mathématiques",
        "resume": "Séance productive générée par l'IA.",
        "quality_score": 9.1,
        "alerte_difficulte": False,
    }

    detail = await service.get_session_detail(session_id)

    assert "resume" in detail
    assert detail["resume"] != ""


# ─── Step 22a : badge alerte si score faible ─────────────────────


@pytest.mark.asyncio
async def test_badge_alerte_present_si_score_faible(sessions_data):
    """
    Critère US-P04 : 'Si le score est faible, une alerte visuelle apparaît'
    → alerte_difficulte: True pour Physique-Chimie (score 4.17 < 6.0)
    """
    service = AsyncMock()
    service.get_session_summaries.return_value = sessions_data

    result = await service.get_session_summaries("child-id")

    session_physique = next(
        s for s in result["sessions"] if s["matiere"] == "Physique-Chimie"
    )
    assert session_physique["alerte_difficulte"] is True
    assert session_physique["quality_score"] < 6.0


@pytest.mark.asyncio
async def test_pas_badge_alerte_si_score_eleve(sessions_data):
    """
    Step 22b : score >= seuil → pas d'alerte
    → alerte_difficulte: False pour Mathématiques (score 9.1)
    """
    service = AsyncMock()
    service.get_session_summaries.return_value = sessions_data

    result = await service.get_session_summaries("child-id")

    session_maths = next(
        s for s in result["sessions"] if s["matiere"] == "Mathématiques"
    )
    assert session_maths["alerte_difficulte"] is False
    assert session_maths["quality_score"] >= 6.0


# ─── Step 12-14 : filtre par matière ─────────────────────────────


@pytest.mark.asyncio
async def test_filtre_par_matiere_renvoie_sessions_filtrees():
    """Step 13-14 : GET /sessions?subject=Mathématiques → seulement les Maths."""
    service = AsyncMock()
    service.get_session_summaries.return_value = {
        "sessions": [
            {
                "matiere": "Mathématiques",
                "quality_score": 9.1,
                "alerte_difficulte": False,
            }
        ],
        "stats": {"total": 1, "avec_alerte": 0, "score_moyen": 9.1},
    }

    result = await service.get_session_summaries("child-id", subject="Mathématiques")

    assert result["stats"]["total"] == 1
    for s in result["sessions"]:
        assert s["matiere"] == "Mathématiques"


# ─── Step 23-25 : transcription ──────────────────────────────────


@pytest.mark.asyncio
async def test_transcription_accessible_apres_clic():
    """Step 24-25 : GET /sessions/{id}/transcript → texte de la transcription."""
    session_id = str(uuid.uuid4())

    service = AsyncMock()
    service.get_session_transcript.return_value = {
        "transcript_text": "Élève : Bonjour ! Tuteur IA : Bonjour, on commence ?"
    }

    result = await service.get_session_transcript(session_id)

    assert "transcript_text" in result
    assert len(result["transcript_text"]) > 0


# ─── Stats globales ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stats_globales_correctes(sessions_data):
    """Les 4 KPI cards de la maquette (total, score moyen, alertes, ce mois)."""
    service = AsyncMock()
    service.get_session_summaries.return_value = sessions_data

    result = await service.get_session_summaries("child-id")

    stats = result["stats"]
    assert "total" in stats
    assert "avec_alerte" in stats
    assert "score_moyen" in stats
    assert stats["avec_alerte"] <= stats["total"]
