"""Fusion for multimodal engagement scoring.

Provides a single function to compute a weighted overall engagement
score from text / audio / video signals. Keeps logic modular so weights
can be adjusted from the API or configuration later.
"""

from typing import Dict, Optional


def compute_overall_score(
    scores: Dict[str, Optional[float]],
    weights: Dict[str, float] = None,
) -> Optional[float]:
    """Compute a weighted overall engagement score.

    - `scores` is a mapping of modality -> score (0.0-1.0) or None.
    - `weights` is a mapping of modality -> relative weight.

    Returns a float between 0 and 1, or None if no valid scores.
    """
    if weights is None:
        weights = {"text": 0.4, "audio": 0.3, "video": 0.3}

    # Filter out missing scores and compute a normalized weighted mean
    total_weight = 0.0
    weighted_sum = 0.0
    for mod, score in scores.items():
        if score is None:
            continue
        w = weights.get(mod, 0.0)
        if w <= 0.0:
            continue
        weighted_sum += float(score) * float(w)
        total_weight += float(w)

    if total_weight == 0.0:
        return None

    overall = weighted_sum / total_weight
    # Clamp and round
    return max(0.0, min(1.0, round(overall, 3)))
