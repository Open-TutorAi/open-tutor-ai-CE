"""Domaine métier — Sessions IA (US-P04)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class StatutSession(Enum):
    EN_COURS = "en_cours"
    TERMINEE = "terminee"


@dataclass
class MetriquesSession:
    score_engagement: float
    score_comprehension: float
    score_autonomie: float


@dataclass
class Alerte:
    type: str
    message: str = ""


@dataclass
class IASession:
    session_id: str
    matiere: str
    statut: StatutSession
    duree_minutes: int
    metriques: Optional[MetriquesSession] = None
    resume: Optional[str] = None
    questions_posees: list = field(default_factory=list)

    SEUIL_QUALITE: float = 6.0

    def calculer_qualite(self) -> float:
        if not self.metriques:
            raise ValueError("Métriques manquantes : impossible de calculer la qualité")
        return round(
            (
                self.metriques.score_engagement
                + self.metriques.score_comprehension
                + self.metriques.score_autonomie
            )
            / 3,
            2,
        )

    def detecter_difficultes(self) -> Optional[Alerte]:
        if not self.metriques:
            return None
        if self.metriques.score_engagement < self.SEUIL_QUALITE:
            return Alerte(
                type="DIFFICULTE_DETECTEE",
                message=(
                    f"Engagement {self.metriques.score_engagement}"
                    f" < seuil {self.SEUIL_QUALITE}"
                ),
            )
        return None

    def est_terminee(self) -> bool:
        return self.statut == StatutSession.TERMINEE
