#!/usr/bin/env python3
"""Calibration des seuils de niveau d'engagement.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from ai.engagement.fusion import compute_overall_score  # noqa: E402
from analyze import (  # noqa: E402
    load_rows,
    load_labels,
    _accuracy,
    _f1_macro,
    _spearman,
    _fmt,
    quadratic_weighted_kappa,
    LEVELS,
)
from grid_search import build_session_samples, BASELINE  # noqa: E402

DEFAULT_THRESHOLDS = (0.4, 0.7)


# ── ÉTAPE 2 — score fusionné par session + classification par seuils ─────────────


def level_with_thresholds(score: float, low: float, high: float) -> str:
    """Classe un score en LOW/MEDIUM/HIGH selon des seuils paramétrables."""
    if score >= high:
        return "HIGH"
    if score >= low:
        return "MEDIUM"
    return "LOW"


def fused_scores(
    samples: Sequence[dict], weights: Dict[str, float]
) -> Tuple[List[float], List[str], List[float]]:
    """Retourne (scores fusionnés, niveaux réels, notes) pour les sessions valides."""
    scores, true_levels, ratings = [], [], []
    for s in samples:
        fused = compute_overall_score(s["scores"], weights)
        if fused is None:
            continue
        scores.append(fused)
        true_levels.append(s["true_level"])
        ratings.append(s["rating"])
    return scores, true_levels, ratings


def evaluate_thresholds(
    scores: Sequence[float], true_levels: Sequence[str], low: float, high: float
) -> Dict[str, Optional[float]]:
    """Accuracy / F1 / QWK pour une paire de seuils donnée."""
    pred = [level_with_thresholds(s, low, high) for s in scores]
    return {
        "accuracy": _accuracy(pred, true_levels),
        "f1": _f1_macro(pred, true_levels),
        "qwk": quadratic_weighted_kappa(pred, true_levels),
    }


# ── ÉTAPE 3 — balayage exhaustif des paires de seuils ────────────────────────────


def search_thresholds(
    scores: Sequence[float],
    true_levels: Sequence[str],
    metric: str,
    step: float,
) -> Tuple[Tuple[float, float], Dict[str, Optional[float]]]:
    """Trouve (seuil_bas, seuil_haut) maximisant la métrique, avec bas < haut."""
    grid = [round(x, 4) for x in np.arange(0.05, 1.0, step)]
    best_t: Tuple[float, float] = DEFAULT_THRESHOLDS
    best_m: Dict[str, Optional[float]] = {}
    best_val = -2.0
    for low in grid:
        for high in grid:
            if high <= low:
                continue
            m = evaluate_thresholds(scores, true_levels, low, high)
            val = m.get(metric)
            if val is None:
                continue
            if val > best_val:
                best_val, best_t, best_m = val, (low, high), m
    return best_t, best_m


def percentile_thresholds(scores: Sequence[float]) -> Tuple[float, float]:
    """Seuils data-driven : tertiles (33e / 67e percentiles) des scores observés."""
    arr = np.asarray(scores, float)
    return float(np.percentile(arr, 33.3)), float(np.percentile(arr, 66.7))


# ── ÉTAPE 4 — rapport comparatif ─────────────────────────────────────────────────


def report(samples: List[dict], weights: Dict[str, float], metric: str, step: float):
    scores, true_levels, ratings = fused_scores(samples, weights)
    print("# Calibration des seuils de niveau d'engagement\n")
    print(f"Sessions exploitables : {len(scores)}")
    print(
        f"Poids de fusion       : "
        f"{weights['text']:.2f}/{weights['video']:.2f}/{weights['audio']:.2f} (T/V/A)"
    )
    print(f"Métrique optimisée    : {metric}")
    if len(scores) < 6:
        print(
            "\n> ⚠️ Peu de sessions : conclusions indicatives. La calibration "
            "demande idéalement ≥ 15 sessions réparties sur les 3 niveaux."
        )

    # Validité ordinale, indépendante des seuils.
    rho = _spearman(scores, ratings)
    print("\n## Validité ordinale (indépendante des seuils)\n")
    print(
        f"**Spearman ρ (score fusionné vs note) : {_fmt(rho)}**. Cette mesure ne "
        "dépend PAS des seuils : un ρ élevé avec une accuracy faible prouve que "
        "le problème vient des seuils, pas du score."
    )
    print(
        f"\nÉtendue des scores observés : min={_fmt(min(scores))}, "
        f"max={_fmt(max(scores))}, moyenne={_fmt(float(np.mean(scores)))}, "
        f"écart-type={_fmt(float(np.std(scores)))}."
    )

    # Trois stratégies de seuils.
    default_m = evaluate_thresholds(scores, true_levels, *DEFAULT_THRESHOLDS)
    (best_low, best_high), best_m = search_thresholds(
        scores, true_levels, metric, step
    )
    p_low, p_high = percentile_thresholds(scores)
    perc_m = evaluate_thresholds(scores, true_levels, p_low, p_high)

    print("\n## Comparaison des stratégies de seuils\n")
    print("| Stratégie | seuil bas | seuil haut | accuracy | F1-macro | QWK |")
    print("|-----------|-----------|------------|----------|----------|-----|")
    print(
        f"| Défaut (actuel) | {DEFAULT_THRESHOLDS[0]:.2f} | "
        f"{DEFAULT_THRESHOLDS[1]:.2f} | {_fmt(default_m['accuracy'])} | "
        f"{_fmt(default_m['f1'])} | {_fmt(default_m['qwk'])} |"
    )
    print(
        f"| Optimal (balayage) | {best_low:.2f} | {best_high:.2f} | "
        f"{_fmt(best_m['accuracy'])} | {_fmt(best_m['f1'])} | {_fmt(best_m['qwk'])} |"
    )
    print(
        f"| Percentiles (tertiles) | {p_low:.2f} | {p_high:.2f} | "
        f"{_fmt(perc_m['accuracy'])} | {_fmt(perc_m['f1'])} | {_fmt(perc_m['qwk'])} |"
    )

    print(
        f"\n_Lecture : si « Optimal » ou « Percentiles » relèvent nettement "
        f"l'accuracy/QWK par rapport au défaut, les seuils 0,40/0,70 sont "
        f"mal calibrés pour la distribution réelle des scores. "
        f"À documenter comme recalibration data-driven (vs seuils heuristiques)._"
    )


# ── CLI ──────────────────────────────────────────────────────────────────────────


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="var/engagement.db", help="base d'engagement")
    p.add_argument("--labels", required=True, help="CSV de vérité terrain")
    p.add_argument(
        "--metric",
        choices=("accuracy", "f1", "qwk"),
        default="qwk",
        help="métrique à maximiser pour les seuils optimaux (def. qwk)",
    )
    p.add_argument("--step", type=float, default=0.05, help="pas du balayage des seuils")
    args = p.parse_args()

    rows = load_rows(args.db)
    labels = load_labels(args.labels)
    samples = build_session_samples(rows, labels)  # ÉTAPE 1
    if not samples:
        sys.exit(
            "Aucune session labellisée exploitable. Voir "
            "python manual_check/analyze.py --list-sessions"
        )
    report(samples, BASELINE, args.metric, args.step)


if __name__ == "__main__":
    main()
