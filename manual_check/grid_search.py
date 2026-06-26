#!/usr/bin/env python3
"""Grid search — validation des poids de fusion multimodale.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

# Rendre le projet importable quel que soit le dossier d'appel
# (le script vit dans <repo>/manual_check/).
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# On réutilise la VRAIE fonction de fusion de l'application : le grid search
# explore exactement le même calcul que celui exécuté en production.
from ai.engagement.fusion import compute_overall_score  # noqa: E402

# Helpers déjà écrits et testés dans analyze.py (DRY) : chargement DB/labels,
# seuils de niveau, métriques. Aucune logique dupliquée.
from analyze import (  # noqa: E402
    load_rows,
    load_labels,
    level_of,
    row_scores,
    _accuracy,
    _f1_macro,
    _spearman,
    _fmt,
)

MODALITIES = ("text", "video", "audio")
BASELINE = {"text": 0.4, "video": 0.3, "audio": 0.3}


# ── ÉTAPE 1 — Vérité terrain : un point (scores agrégés + niveau réel) / session
# ───────────────────────────────────────────────────────────────────────────────


def build_session_samples(
    rows: List[dict], labels: Dict[str, dict]
) -> List[dict]:
    """Agrège les lignes de chaque session labellisée en un seul échantillon.

    La note (rating) est donnée *par session* ; on résume donc les nombreuses
    lignes d'une session en une moyenne par modalité. Résultat : un échantillon
    = {scores par modalité, niveau réel, note} prêt pour la comparaison.
    """
    by_session: Dict[str, List[dict]] = {}
    for r in rows:
        sid = r.get("session_id")
        if sid in labels:
            by_session.setdefault(sid, []).append(r)

    samples: List[dict] = []
    for sid, rs in by_session.items():
        agg: Dict[str, Optional[float]] = {}
        for mod in MODALITIES:
            vals = [row_scores(r)[mod] for r in rs]
            vals = [v for v in vals if v is not None]
            agg[mod] = float(np.mean(vals)) if vals else None
        # Au moins une modalité doit être présente pour évaluer la session.
        if all(agg[m] is None for m in MODALITIES):
            continue
        samples.append(
            {
                "session_id": sid,
                "scores": agg,
                "true_level": labels[sid]["level"],
                "rating": labels[sid]["rating"],
            }
        )
    return samples


# ── ÉTAPE 2 — Grille de poids : tous les triplets sommant à 1 ────────────────────


def weight_grid(step: float, min_weight: float) -> List[Dict[str, float]]:
    """Énumère les triplets (texte, vidéo, audio) avec texte+vidéo+audio = 1.

    On travaille en pas entiers pour éviter les erreurs d'arrondi flottant :
    step=0.1 → unités de 1 sur 10. Chaque triplet dont la somme fait 10 (et dont
    chaque poids ≥ min_weight) est conservé.
    """
    n = round(1.0 / step)  # nombre d'unités (10 pour step=0.1)
    min_units = round(min_weight / step)
    grid: List[Dict[str, float]] = []
    for t in range(min_units, n - 2 * min_units + 1):
        for v in range(min_units, n - t - min_units + 1):
            a = n - t - v
            if a < min_units:
                continue
            grid.append(
                {"text": t / n, "video": v / n, "audio": a / n}
            )
    return grid


# ── ÉTAPE 3 — Évaluer un jeu de poids sur un ensemble d'échantillons ─────────────


def evaluate(
    samples: Sequence[dict], weights: Dict[str, float]
) -> Dict[str, Optional[float]]:
    """Calcule accuracy, F1-macro et Spearman pour un triplet de poids donné.

    Pour chaque session : on fusionne ses scores avec ``compute_overall_score``
    (la vraie fonction), on en dérive le niveau prédit (≥0,7 HIGH / ≥0,4 MEDIUM /
    sinon LOW), puis on compare au niveau réel.
    """
    pred_levels: List[str] = []
    true_levels: List[str] = []
    fused_scores: List[float] = []
    ratings: List[float] = []
    for s in samples:
        fused = compute_overall_score(s["scores"], weights)
        if fused is None:
            continue
        pred_levels.append(level_of(fused))
        true_levels.append(s["true_level"])
        fused_scores.append(fused)
        ratings.append(s["rating"])
    return {
        "n": len(pred_levels),
        "accuracy": _accuracy(pred_levels, true_levels),
        "f1": _f1_macro(pred_levels, true_levels),
        "spearman": _spearman(fused_scores, ratings),
    }


def _objective(metrics: Dict[str, Optional[float]], key: str) -> float:
    """Valeur à maximiser (None traité comme -1 pour ne jamais être choisi)."""
    v = metrics.get(key)
    return -1.0 if v is None else v


def rank_weights(
    samples: Sequence[dict], grid: List[Dict[str, float]], metric: str
) -> List[Tuple[Dict[str, float], Dict[str, Optional[float]]]]:
    """Classe tous les triplets de la grille par métrique décroissante."""
    scored = [(w, evaluate(samples, w)) for w in grid]
    scored.sort(
        key=lambda wm: (
            _objective(wm[1], metric),
            _objective(wm[1], "f1"),  # départage 1
            _objective(wm[1], "spearman"),  # départage 2
        ),
        reverse=True,
    )
    return scored


# ── ÉTAPE 4 — Validation croisée (k-fold) ────────────────────────────────────────


def kfold_indices(n: int, k: int, seed: int = 42) -> List[List[int]]:
    """Découpe [0..n-1] en k plis mélangés de tailles ~égales."""
    idx = list(range(n))
    random.Random(seed).shuffle(idx)
    return [idx[i::k] for i in range(k)]


def cross_validate(
    samples: List[dict], grid: List[Dict[str, float]], metric: str, k: int
) -> Optional[dict]:
    """Évalue honnêtement la procédure de sélection des poids.

    Pour chaque pli : on cherche les meilleurs poids sur les (k-1) autres plis
    (entraînement), puis on les évalue sur le pli laissé de côté (test). On
    moyenne la métrique de test. On évalue aussi le baseline sur les mêmes plis
    de test, pour une comparaison équitable.

    But : montrer que les poids choisis généralisent, et ne sont pas juste
    sur-ajustés à l'ensemble des données.
    """
    n = len(samples)
    if n < k or n < 4:
        return None  # trop peu de sessions pour une CV crédible
    folds = kfold_indices(n, k)
    sel_scores: List[float] = []
    base_scores: List[float] = []
    for i in range(k):
        test_idx = set(folds[i])
        train = [samples[j] for j in range(n) if j not in test_idx]
        test = [samples[j] for j in range(n) if j in test_idx]
        if not train or not test:
            continue
        best_w, _ = rank_weights(train, grid, metric)[0]
        sel = evaluate(test, best_w).get(metric)
        base = evaluate(test, BASELINE).get(metric)
        if sel is not None:
            sel_scores.append(sel)
        if base is not None:
            base_scores.append(base)
    if not sel_scores:
        return None
    return {
        "k": k,
        "selected_mean": float(np.mean(sel_scores)),
        "selected_std": float(np.std(sel_scores)),
        "baseline_mean": float(np.mean(base_scores)) if base_scores else None,
        "baseline_std": float(np.std(base_scores)) if base_scores else None,
    }


# ── ÉTAPE 5 — Rapport ────────────────────────────────────────────────────────────


def _wfmt(w: Dict[str, float]) -> str:
    return f"{w['text']:.2f}/{w['video']:.2f}/{w['audio']:.2f}"


def report(
    samples: List[dict],
    grid: List[Dict[str, float]],
    metric: str,
    k: int,
    top: int,
) -> None:
    print("# Grid search — validation des poids de fusion\n")
    print(f"Sessions labellisées exploitables : {len(samples)}")
    print(f"Triplets de poids testés          : {len(grid)}")
    print(f"Métrique optimisée                : {metric}")
    if len(samples) < 8:
        print(
            "\n> ⚠️ Peu de sessions : les résultats sont indicatifs. Ajoutez des "
            "labels pour une conclusion solide (voir manual_check/README.md)."
        )

    ranked = rank_weights(samples, grid, metric)

    # 5a. Baseline de référence
    base = evaluate(samples, BASELINE)
    print("\n## Baseline (poids actuels de l'application)\n")
    print("| poids T/V/A | n | accuracy | F1-macro | Spearman ρ |")
    print("|-------------|---|----------|----------|------------|")
    print(
        f"| {_wfmt(BASELINE)} | {base['n']} | {_fmt(base['accuracy'])} | "
        f"{_fmt(base['f1'])} | {_fmt(base['spearman'])} |"
    )

    # 5b. Meilleurs triplets sur l'ensemble des données
    print(f"\n## Top {top} triplets (recherche sur toutes les données)\n")
    print("| rang | poids T/V/A | accuracy | F1-macro | Spearman ρ |")
    print("|------|-------------|----------|----------|------------|")
    for rank, (w, m) in enumerate(ranked[:top], 1):
        flag = "  ← baseline" if w == BASELINE else ""
        print(
            f"| {rank} | {_wfmt(w)}{flag} | {_fmt(m['accuracy'])} | "
            f"{_fmt(m['f1'])} | {_fmt(m['spearman'])} |"
        )

    best_w, best_m = ranked[0]
    print(
        f"\n_Meilleur triplet : **{_wfmt(best_w)}** "
        f"({metric} = {_fmt(best_m[metric])}) vs baseline "
        f"{metric} = {_fmt(base[metric])}._"
    )

    # 5c. Validation croisée (la mesure honnête)
    cv = cross_validate(samples, grid, metric, k)
    print("\n## Validation croisée (k-fold) — généralisation\n")
    if cv is None:
        print(
            "_Trop peu de sessions pour une validation croisée crédible "
            f"(il en faut au moins {max(4, k)}). Les chiffres ci-dessus "
            "restent indicatifs._"
        )
    else:
        print(
            f"Procédure : pour chacun des {cv['k']} plis, on sélectionne les "
            "meilleurs poids sur l'entraînement et on mesure sur le test "
            "jamais vu.\n"
        )
        print(f"| procédure | {metric} test (moyenne ± écart-type) |")
        print("|-----------|-------------------------------------|")
        print(
            f"| poids sélectionnés par grid search | "
            f"{cv['selected_mean']:.3f} ± {cv['selected_std']:.3f} |"
        )
        if cv["baseline_mean"] is not None:
            print(
                f"| baseline 0,4/0,3/0,3 | "
                f"{cv['baseline_mean']:.3f} ± {cv['baseline_std']:.3f} |"
            )
        print(
            "\n_Lecture : si « poids sélectionnés » dépasse le baseline en test, "
            "le grid search apporte un gain qui généralise. Sinon, le baseline "
            "heuristique est déjà compétitif — un résultat tout aussi publiable._"
        )


# ── CLI ──────────────────────────────────────────────────────────────────────────


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="var/engagement.db", help="chemin de la base d'engagement")
    p.add_argument("--labels", required=True, help="CSV de vérité terrain (session_id,rating,...)")
    p.add_argument("--step", type=float, default=0.1, help="pas de la grille (def. 0.1)")
    p.add_argument(
        "--min-weight",
        type=float,
        default=0.0,
        help="poids minimal par modalité ; 0.1 force les 3 modalités présentes",
    )
    p.add_argument(
        "--metric",
        choices=("accuracy", "f1", "spearman"),
        default="accuracy",
        help="métrique à maximiser (def. accuracy)",
    )
    p.add_argument("--folds", type=int, default=5, help="nombre de plis pour la CV")
    p.add_argument("--top", type=int, default=10, help="nombre de triplets affichés")
    args = p.parse_args()

    rows = load_rows(args.db)
    labels = load_labels(args.labels)
    samples = build_session_samples(rows, labels)
    if not samples:
        sys.exit(
            "Aucune session labellisée exploitable. Vérifiez que les session_id "
            "de labels.csv correspondent à ceux de la base (python "
            "manual_check/analyze.py --list-sessions)."
        )

    grid = weight_grid(args.step, args.min_weight)
    report(samples, grid, args.metric, args.folds, args.top)


if __name__ == "__main__":
    main()
