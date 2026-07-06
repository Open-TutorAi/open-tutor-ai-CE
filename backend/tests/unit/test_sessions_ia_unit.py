import pytest
import uuid
from typing import Optional


# ═══════════════════════════════════════════════════════════════════
# MODÈLES MÉTIER — import depuis le vrai module domain
# ═══════════════════════════════════════════════════════════════════
from learning.sessions.domain import IASession, MetriquesSession, Alerte, StatutSession


# ═══════════════════════════════════════════════════════════════════
# TESTS — calculer_qualite()
# ═══════════════════════════════════════════════════════════════════


class TestCalculerQualite:

    def test_calcul_qualite_scores_eleves(self):
        session = IASession(
            session_id=str(uuid.uuid4()),
            matiere="Mathématiques",
            statut=StatutSession.TERMINEE,
            duree_minutes=38,
            metriques=MetriquesSession(
                score_engagement=9.1, score_comprehension=8.5, score_autonomie=8.8
            ),
        )
        qualite = session.calculer_qualite()
        assert qualite == pytest.approx(8.8, rel=0.01)

    def test_calcul_qualite_scores_faibles(self):
        session = IASession(
            session_id=str(uuid.uuid4()),
            matiere="Physique-Chimie",
            statut=StatutSession.TERMINEE,
            duree_minutes=22,
            metriques=MetriquesSession(
                score_engagement=4.0, score_comprehension=5.0, score_autonomie=3.5
            ),
        )
        qualite = session.calculer_qualite()
        assert qualite == pytest.approx(4.17, rel=0.01)

    def test_calcul_qualite_sans_metriques_leve_exception(self):
        session = IASession(
            session_id=str(uuid.uuid4()),
            matiere="Histoire",
            statut=StatutSession.EN_COURS,
            duree_minutes=5,
            metriques=None,
        )
        with pytest.raises(ValueError, match="Métriques manquantes"):
            session.calculer_qualite()

    def test_calcul_qualite_arrondi_deux_decimales(self):
        session = IASession(
            session_id=str(uuid.uuid4()),
            matiere="Français",
            statut=StatutSession.TERMINEE,
            duree_minutes=45,
            metriques=MetriquesSession(
                score_engagement=7.0, score_comprehension=8.0, score_autonomie=9.0
            ),
        )
        qualite = session.calculer_qualite()
        assert qualite == 8.0
        assert isinstance(qualite, float)


# ═══════════════════════════════════════════════════════════════════
# TESTS — detecter_difficultes()
# Règle : score_engagement < 6.0 → Alerte  (losange ◇ du diagramme d'activité)
# ═══════════════════════════════════════════════════════════════════


class TestDetecterDifficultes:

    def test_alerte_declenchee_si_engagement_sous_le_seuil(self):
        session = IASession(
            session_id=str(uuid.uuid4()),
            matiere="Physique-Chimie",
            statut=StatutSession.TERMINEE,
            duree_minutes=22,
            metriques=MetriquesSession(
                score_engagement=5.5, score_comprehension=7.0, score_autonomie=6.0
            ),
        )
        alerte = session.detecter_difficultes()
        assert alerte is not None
        assert alerte.type == "DIFFICULTE_DETECTEE"

    def test_pas_alerte_si_engagement_au_dessus_du_seuil(self):
        session = IASession(
            session_id=str(uuid.uuid4()),
            matiere="Mathématiques",
            statut=StatutSession.TERMINEE,
            duree_minutes=38,
            metriques=MetriquesSession(
                score_engagement=9.1, score_comprehension=8.5, score_autonomie=8.8
            ),
        )
        alerte = session.detecter_difficultes()
        assert alerte is None

    def test_pas_alerte_si_engagement_exactement_au_seuil(self):
        session = IASession(
            session_id=str(uuid.uuid4()),
            matiere="SVT",
            statut=StatutSession.TERMINEE,
            duree_minutes=30,
            metriques=MetriquesSession(
                score_engagement=6.0, score_comprehension=7.0, score_autonomie=7.0
            ),
        )
        alerte = session.detecter_difficultes()
        assert alerte is None

    def test_pas_alerte_sans_metriques(self):
        session = IASession(
            session_id=str(uuid.uuid4()),
            matiere="Anglais",
            statut=StatutSession.EN_COURS,
            duree_minutes=10,
            metriques=None,
        )
        alerte = session.detecter_difficultes()
        assert alerte is None

    def test_message_alerte_contient_le_score_et_le_seuil(self):
        session = IASession(
            session_id=str(uuid.uuid4()),
            matiere="Physique-Chimie",
            statut=StatutSession.TERMINEE,
            duree_minutes=22,
            metriques=MetriquesSession(
                score_engagement=3.2, score_comprehension=4.0, score_autonomie=4.5
            ),
        )
        alerte = session.detecter_difficultes()
        assert "3.2" in alerte.message
        assert "6.0" in alerte.message


# ═══════════════════════════════════════════════════════════════════
# TESTS — est_terminee()
# ═══════════════════════════════════════════════════════════════════


class TestStatutSession:

    def test_session_terminee_est_terminee(self):
        session = IASession(
            session_id=str(uuid.uuid4()),
            matiere="Maths",
            statut=StatutSession.TERMINEE,
            duree_minutes=40,
        )
        assert session.est_terminee() is True

    def test_session_en_cours_nest_pas_terminee(self):
        session = IASession(
            session_id=str(uuid.uuid4()),
            matiere="Maths",
            statut=StatutSession.EN_COURS,
            duree_minutes=12,
        )
        assert session.est_terminee() is False
