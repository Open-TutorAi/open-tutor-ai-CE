"""Service métier — domaine Parent.

Fournit :
- vérification de liaison parent-enfant
- création d'un soutien pour l'enfant (délègue à SupportsService)
- lecture du profil de l'enfant pour enrichir le prompt IA
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from accounts.parents.models import ParentStudentLink
from common.exceptions import AuthorizationError, NotFoundError

log = logging.getLogger(__name__)


class ParentService:
    """Logique métier liée au rôle parent."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ── Vérifications de liaison ──────────────────────────────────────────────

    def get_link(self, parent_id: str, student_id: str) -> Optional[ParentStudentLink]:
        """Retourne la liaison active entre parent et enfant, ou None."""
        return (
            self.session.query(ParentStudentLink)
            .filter(
                ParentStudentLink.parent_id == parent_id,
                ParentStudentLink.student_id == student_id,
                ParentStudentLink.status == "active",
            )
            .first()
        )

    def assert_owns_student(self, parent_id: str, student_id: str) -> None:
        """Lève AuthorizationError si la liaison n'existe pas ou est inactive."""
        link = self.get_link(parent_id, student_id)
        if not link:
            raise AuthorizationError(
                "Aucune liaison active entre ce parent et cet étudiant."
            )

    def list_linked_students(self, parent_id: str) -> List[ParentStudentLink]:
        """Retourne toutes les liaisons actives d'un parent."""
        return (
            self.session.query(ParentStudentLink)
            .filter(
                ParentStudentLink.parent_id == parent_id,
                ParentStudentLink.status == "active",
            )
            .all()
        )

    def create_link(self, parent_id: str, student_id: str) -> ParentStudentLink:
        """Crée une liaison active (sans code d'invitation ici)."""
        existing = self.get_link(parent_id, student_id)
        if existing:
            return existing
        link = ParentStudentLink(
            parent_id=parent_id,
            student_id=student_id,
            status="active",
        )
        self.session.add(link)
        self.session.commit()
        self.session.refresh(link)
        return link

    # ── Profil étudiant ───────────────────────────────────────────────────────

    def get_student_profile(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Retourne les informations de profil de l'étudiant."""
        from data.models import User

        student = self.session.query(User).filter(User.id == student_id).first()
        if not student:
            return None
        return {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "role": student.role,
        }

    # ── Création de soutien pour l'enfant ────────────────────────────────────

    def create_support_for_student(
        self,
        parent_id: str,
        student_id: str,
        data: Dict[str, Any],
    ):
        """
        Vérifie la liaison, enrichit les données avec le profil étudiant,
        puis délègue la création à SupportsService (en tant que l'étudiant).
        """
        from learning.supports.service import SupportsService

        # 1. Vérifier la liaison parent-enfant
        self.assert_owns_student(parent_id, student_id)

        # 2. Récupérer le profil étudiant pour enrichir le prompt
        student = self.get_student_profile(student_id)
        if not student:
            raise NotFoundError("Student", student_id)

        # 3. Enrichir les données avec des métadonnées parent
        enriched_data = {
            **data,
            # Marquer comme soutien créé par un parent
            "access_type": "Private",
        }

        # 4. Déléguer la création — le soutien est rattaché à l'étudiant
        svc = SupportsService(self.session)
        support = svc.create(user_id=student_id, data=enriched_data)

        log.info(
            "Parent %s a créé le soutien %s pour l'étudiant %s",
            parent_id,
            support.id,
            student_id,
        )
        return support