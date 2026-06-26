#!/usr/bin/env python3
"""A/B mono-sujet — « avec adaptation » vs « sans adaptation ».
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List, Optional, Sequence

import numpy as np

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from ai.engagement.fusion import compute_overall_score  # noqa: E402
from analyze import load_rows, load_labels, _fmt, mann_whitney_u, row_scores  # noqa: E402

ADAPTIVE = {"adaptive", "adaptatif", "a", "on", "true"}
CONTROL = {"control", "controle", "contrôle", "c", "off", "false"}


def _norm_condition(c: Optional[str]) -> Optional[str]:
    if not c:
        return None
    c = c.strip().lower()
    if c in ADAPTIVE:
        return "adaptive"
    if c in CONTROL:
        return "control"
    return None


def session_scores(rows: List[dict], labels: Dict[str, dict]) -> List[dict]:
    """Un point par session labellisée : score système moyen + note + condition."""
    by_session: Dict[str, List[dict]] = {}
    for r in rows:
        sid = r.get("session_id")
        if sid in labels:
            by_session.setdefault(sid, []).append(r)
    out: List[dict] = []
    for sid, rs in by_session.items():
        cond = _norm_condition(labels[sid].get("condition"))
        if cond is None:
            continue
        agg = {}
        for mod in ("text", "video", "audio"):
            vals = [row_scores(r)[mod] for r in rs]
            vals = [v for v in vals if v is not None]
            agg[mod] = float(np.mean(vals)) if vals else None
        fused = compute_overall_score(agg)
        if fused is None:
            continue
        out.append(
            {
                "session_id": sid,
                "condition": cond,
                "system_score": fused,
                "rating": labels[sid]["rating"],
            }
        )
    return out


def cliffs_delta(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    """Taille d'effet de Cliff : (#x>y − #x<y)/(n·m). ∈ [−1, 1].

    |δ| ≈ 0,15 petit, 0,33 moyen, 0,47 grand (seuils usuels).
    """
    if not x or not y:
        return None
    gt = sum(1 for a in x for b in y if a > b)
    lt = sum(1 for a in x for b in y if a < b)
    return (gt - lt) / (len(x) * len(y))


def _stats(vals: Sequence[float]) -> str:
    if not vals:
        return "—"
    a = np.asarray(vals, float)
    q1, q3 = np.percentile(a, [25, 75])
    return f"{np.median(a):.2f} [{q1:.2f}–{q3:.2f}] (moy {a.mean():.2f})"


def compare(points: List[dict], measure: str, label: str) -> None:
    adin = [p[measure] for p in points if p["condition"] == "adaptive"]
    ctrl = [p[measure] for p in points if p["condition"] == "control"]
    print(f"\n## {label}\n")
    print("| Condition | n | médiane [IQR] (moyenne) |")
    print("|-----------|---|--------------------------|")
    print(f"| Adaptatif | {len(adin)} | {_stats(adin)} |")
    print(f"| Contrôle  | {len(ctrl)} | {_stats(ctrl)} |")
    if adin and ctrl:
        u, p = mann_whitney_u(adin, ctrl)
        d = cliffs_delta(adin, ctrl)
        print(
            f"\n**Mann-Whitney** U = {_fmt(u, 1)}, p = {_fmt(p)} ; "
            f"**Cliff's δ = {_fmt(d)}** "
            f"(adaptatif {'>' if (d or 0) > 0 else '≤'} contrôle)."
        )
        if p is not None:
            print(
                "_"
                + (
                    "Différence significative (p < 0,05)."
                    if p < 0.05
                    else "Non significatif (effectif faible) — rapporter la "
                    "tendance + la taille d'effet δ."
                )
                + "_"
            )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default="var/engagement.db")
    ap.add_argument("--labels", required=True)
    args = ap.parse_args()

    rows = load_rows(args.db)
    labels = load_labels(args.labels)
    points = session_scores(rows, labels)
    print("# A/B mono-sujet — avec vs sans adaptation\n")
    if not points:
        sys.exit(
            "Aucune session avec condition adaptive/control. Renseignez la colonne "
            "`condition` de labels.csv avec 'adaptive' ou 'control'."
        )
    n_a = sum(1 for p in points if p["condition"] == "adaptive")
    n_c = sum(1 for p in points if p["condition"] == "control")
    print(f"Sessions : {n_a} adaptatif, {n_c} contrôle.")
    if min(n_a, n_c) < 5:
        print(
            "\n> ⚠️ Étude mono-sujet à faible effectif : résultat **illustratif**. "
            "Visez ≥ 8 sessions par condition. Présentez comme preuve de concept."
        )

    # Mesure PRIMAIRE (indépendante) : l'auto-rapport.
    compare(points, "rating", "Engagement auto-rapporté (1-5) — mesure primaire")
    # Mesure SECONDAIRE (non indépendante) : le score du système.
    compare(
        points,
        "system_score",
        "Score d'engagement système — mesure secondaire (non indépendante)",
    )

    print(
        "\n---\n_Rappel mémoire : étude mono-sujet → illustrative ; l'auto-rapport "
        "est la mesure primaire, le score système est secondaire (produit par le "
        "système lui-même)._"
    )


if __name__ == "__main__":
    main()
