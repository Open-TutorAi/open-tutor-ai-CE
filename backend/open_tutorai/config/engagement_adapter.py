from __future__ import annotations
from datetime import datetime
from typing import Optional, Tuple


# ── Seuils ────────────────────────────────────────────────────────────────────

THRESHOLD_LOW  = 0.40
THRESHOLD_HIGH = 0.70

# ── Instructions pédagogiques adaptatives ─────────────────────────────────────

ADAPTATIONS: dict[str, str] = {
    "low": (
        "The student seems disengaged. "
        "Simplify your explanation, add one concrete example, "
        "and end with a single short interactive question."
    ),
    "medium": (
        "The student is moderately engaged. "
        "Maintain the current level and confirm understanding "
        "with a brief question at the end."
    ),
    "high": (
        "The student is highly engaged. "
        "Go deeper, introduce nuances or edge cases, "
        "and accelerate the pedagogical pace."
    ),
}


# ── Calcul textuel ────────────────────────────────────────────────────────────

def _text_score(message: str) -> float:
    """
    Score basé sur 3 signaux comportementaux textuels :

    1. Longueur du message  → proxy de l'implication
    2. Diversité lexicale   → proxy de la réflexion (Type-Token Ratio)
    3. Nombre de questions  → proxy de la curiosité active

    Retourne un float entre 0.0 et 1.0.
    """
    words = message.strip().split()
    n = len(words)

    if n == 0:
        return 0.0

    # 1. Score longueur (0.0 → 1.0)
    if   n >= 20: length_score = 1.0
    elif n >= 10: length_score = 0.75
    elif n >= 5:  length_score = 0.50
    elif n >= 2:  length_score = 0.25
    else:         length_score = 0.10

    # 2. Diversité lexicale (Type-Token Ratio)
    ttr = len(set(w.lower() for w in words)) / n

    # 3. Bonus questions (plafonné à 0.15)
    q_bonus = min(message.count("?") * 0.05, 0.15)

    # Fusion pondérée
    score = (
        0.50 * length_score
      + 0.35 * ttr
      + 0.15 * (q_bonus / 0.15)   # normalisé 0→1 avant pondération
    )

    return round(max(0.0, min(1.0, score)), 3)


# ── API publique ──────────────────────────────────────────────────────────────

def compute_engagement_score(
    message: str,
    video_score:       Optional[float] = None,  # Phase 2 — webcam
    audio_score:       Optional[float] = None,  # Phase 3 — micro
    interaction_score: Optional[float] = None,  # Phase 4 — UI events
) -> Tuple[float, str]:
    """
    Calcule le score d'engagement fusionné et son niveau.

    Phase 1 : seul le score textuel est utilisé.
    Phase 2+ : les scores supplémentaires sont intégrés
               avec des poids adaptatifs selon disponibilité.

    Returns
    -------
    (score, level) : float ∈ [0,1], str ∈ {"low","medium","high"}
    """
    sources: list[tuple[float, float]] = [
        (_text_score(message), 1.0),  # (valeur, poids)
    ]

    if video_score is not None:
        sources.append((video_score, 1.5))   # signal fort
    if audio_score is not None:
        sources.append((audio_score, 1.2))
    if interaction_score is not None:
        sources.append((interaction_score, 0.8))

    total_weight = sum(w for _, w in sources)
    fused = sum(v * w for v, w in sources) / total_weight
    fused = round(max(0.0, min(1.0, fused)), 3)

    if   fused < THRESHOLD_LOW:  level = "low"
    elif fused < THRESHOLD_HIGH: level = "medium"
    else:                        level = "high"

    return fused, level


def build_adaptive_instruction(level: str) -> str:
    """Retourne l'instruction pédagogique pour le niveau d'engagement donné."""
    return ADAPTATIONS.get(level, ADAPTATIONS["medium"])


def build_engagement_record(
    message: str,
    score:   float,
    level:   str,
) -> dict:
    """
    Construit le dictionnaire de métadonnées pour :
    - journalisation JSONL (dataset offline)
    - retour optionnel vers le frontend
    """
    words = message.strip().split()
    n     = max(len(words), 1)

    return {
        "timestamp":        datetime.now().isoformat(),
        "engagement_score": score,
        "engagement_level": level,
        "message_length":   len(words),
        "word_diversity":   round(len(set(w.lower() for w in words)) / n, 3),
        "question_marks":   message.count("?"),
        "preview":          message[:80],
        "modalities":       ["text"],  # Phase 2+ : ["text","video","audio"]
    }


