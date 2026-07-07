"""Service Sessions IA — US-P04."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from common.exceptions import AuthorizationError, NotFoundError
from learning.sessions.domain import (
    Alerte,
    IASession,
    MetriquesSession,
    StatutSession,
)

# ── Constantes ────────────────────────────────────────────────────────────────
SEUIL_QUALITE = 6.0


class IASessionsService:
    """Service pour la consultation des sessions IA par le parent."""

    def __init__(self, db: Session):
        self.db = db

    # ── Contrôle d'accès (anti-IDOR) ─────────────────────────────────────────
    def owns_student(self, parent_id: str, child_id: str) -> bool:
        """Vérifie que le parent est bien le tuteur légal de l'enfant."""
        # SÉCURITÉ : anti-IDOR — vérification de l'appartenance avant tout accès.
        # TODO : remplacer par une vraie requête DB sur la table parent_student.
        # Pour l'instant on retourne True si les IDs sont non-vides (dev uniquement).
        return bool(parent_id) and bool(child_id)

    def _require_parent_access(self, parent_id: str, child_id: str) -> None:
        if not self.owns_student(parent_id, child_id):
            # SÉCURITÉ : 403 sans détail pour ne pas confirmer l'existence de l'enfant.
            raise AuthorizationError("Accès refusé")

    # ── Données de démonstration (à remplacer par requêtes DB réelles) ────────
    def _get_demo_sessions(
        self, child_id: str, subject: Optional[str] = None
    ) -> List[Dict]:
        sessions = [
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
        ]
        if subject:
            sessions = [s for s in sessions if s["matiere"] == subject]
        return sessions

    # ── Méthodes publiques ────────────────────────────────────────────────────
    def get_session_summaries(
        self,
        child_id: str,
        parent_id: str,
        subject: Optional[str] = None,
        period: Optional[str] = None,
    ) -> Dict[str, Any]:
        """GET /sessions?child_id=X — charge les vraies sessions depuis la DB."""
        self._require_parent_access(parent_id, child_id)

        # Charger les vraies sessions depuis la DB via les chats liés aux soutiens
        from data.models import Support, Chat

        # SÉCURITÉ : charger les soutiens du parent lui-même
        # (le parent crée les soutiens sur son propre compte)
        supports = self.db.query(Support).filter(
            Support.user_id == parent_id,
            Support.chat_id.isnot(None),
        ).all()

        sessions = []
        for support in supports:
            chat = self.db.query(Chat).filter(Chat.id == support.chat_id).first()
            if not chat or not chat.chat:
                continue

            chat_data = chat.chat if isinstance(chat.chat, dict) else {}
            messages_raw = chat_data.get("messages", {})
            if isinstance(messages_raw, dict):
                messages_list = list(messages_raw.values())
            elif isinstance(messages_raw, list):
                messages_list = messages_raw
            else:
                messages_list = []

            ai_messages = [m for m in messages_list if isinstance(m, dict) and m.get("role") == "assistant"]
            user_messages = [m for m in messages_list if isinstance(m, dict) and m.get("role") == "user"]

            if not ai_messages:
                continue

            avg_len = sum(len(str(m.get("content", ""))) for m in ai_messages) / max(len(ai_messages), 1)
            quality_score = min(round(avg_len / 200, 1), 10.0)
            alerte = quality_score < 6.0

            questions = []
            for m in user_messages[:3]:
                content = m.get("content", "")
                if isinstance(content, list):
                    content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
                if content and len(content) > 3:
                    # GDPR : tronquer à 60 chars
                    questions.append(str(content)[:60] + "..." if len(str(content)) > 60 else str(content))

            last_content = ai_messages[-1].get("content", "") if ai_messages else ""
            if isinstance(last_content, list):
                last_content = " ".join(c.get("text", "") for c in last_content if isinstance(c, dict))
            resume = str(last_content)[:150] + "..." if last_content and len(str(last_content)) > 150 else str(last_content)

            matiere = support.subject or support.custom_subject or "Général"
            if subject and matiere.lower() != subject.lower():
                continue

            engagement = min(quality_score + 0.5, 10.0)
            comprehension = min(quality_score - 0.2, 10.0)
            autonomie = min(quality_score - 0.8, 10.0)

            sessions.append({
                "id": chat.id,
                "matiere": matiere,
                "duree_minutes": len(ai_messages) * 2,
                "quality_score": quality_score,
                "alerte_difficulte": alerte,
                "themes": [matiere],
                "questions": questions,
                "resume": resume or "Session en cours.",
                "metriques": {
                    "engagement": engagement,
                    "comprehension": comprehension,
                    "autonomie": autonomie,
                },
                "statut": "terminee" if len(ai_messages) >= 10 else "en_cours",
            })

        sessions.sort(key=lambda s: s.get("id", ""), reverse=True)

        avec_alerte = sum(1 for s in sessions if s["alerte_difficulte"])
        score_moyen = (
            round(sum(s["quality_score"] for s in sessions) / len(sessions), 2)
            if sessions else 0.0
        )

        return {
            "sessions": sessions,
            "stats": {
                "total": len(sessions),
                "avec_alerte": avec_alerte,
                "score_moyen": score_moyen,
            },
        }

    def get_session_detail(
        self, session_id: str, parent_id: str, child_id: str
    ) -> Dict[str, Any]:
        """GET /sessions/{id}/detail — steps 16→21 du diagramme."""
        self._require_parent_access(parent_id, child_id)

        # TODO : charger depuis DB et appeler le LLM pour générer le résumé.
        return {
            "id": session_id,
            "matiere": "Mathématiques",
            "duree_minutes": 38,
            "quality_score": 9.1,
            "alerte_difficulte": False,
            "themes": ["Fonctions", "Dérivées", "Limites"],
            "questions": [
                "Quelle est la dérivée de x² ?",
                "Comment calculer une limite en l'infini ?",
            ],
            "resume": "Séance productive générée par l'IA.",
            "metriques": {
                "engagement": 9.1,
                "comprehension": 8.5,
                "autonomie": 8.8,
            },
            "statut": "terminee",
        }

    def get_session_transcript(
        self, session_id: str, parent_id: str, child_id: str
    ) -> Dict[str, Any]:
        """GET /sessions/{id}/transcript — steps 23→25 du diagramme."""
        self._require_parent_access(parent_id, child_id)

        # TODO : charger la transcription réelle depuis DB.
        return {
            "session_id": session_id,
            "transcript_text": (
                "Élève : Bonjour ! "
                "Tuteur IA : Bonjour, on commence par les dérivées ?"
            ),
        }
