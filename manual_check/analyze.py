"""Engagement evaluation & analysis tool.
"""

from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

# Make the project importable for --benchmark regardless of the invocation dir
# (script lives at <repo>/manual_check/analyze.py).
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# ── Fusion (mirrors ai/engagement/fusion.py so the script stays standalone) ────
DEFAULT_WEIGHTS = {"text": 0.4, "audio": 0.3, "video": 0.3}


def weighted_fusion(
    scores: Dict[str, Optional[float]], weights: Dict[str, float]
) -> Optional[float]:
    """Normalized weighted mean over the present modalities (None = absent)."""
    total_w = 0.0
    acc = 0.0
    for mod, s in scores.items():
        if s is None:
            continue
        w = weights.get(mod, 0.0)
        if w <= 0.0:
            continue
        acc += float(s) * w
        total_w += w
    if total_w == 0.0:
        return None
    return max(0.0, min(1.0, acc / total_w))


# Data-driven thresholds (tertiles), aligned with ai/engagement/service._level.
# See RESULTATS_ANALYSE.md (§7).
LEVEL_LOW_MAX = 0.53
LEVEL_HIGH_MIN = 0.69


def level_of(score: Optional[float]) -> Optional[str]:
    if score is None:
        return None
    if score >= LEVEL_HIGH_MIN:
        return "HIGH"
    if score >= LEVEL_LOW_MAX:
        return "MEDIUM"
    return "LOW"


def rating_to_level(rating: float) -> str:
    """Map a 1-5 self-rating to the three engagement levels."""
    if rating <= 2:
        return "LOW"
    if rating <= 3:
        return "MEDIUM"
    return "HIGH"


# ── Stats helpers (pure numpy; no scipy/sklearn dependency) ────────────────────


def _pearson(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    if len(x) < 2:
        return None
    xa, ya = np.asarray(x, float), np.asarray(y, float)
    if xa.std() == 0 or ya.std() == 0:
        return None
    return float(np.corrcoef(xa, ya)[0, 1])


def _rankdata(a: np.ndarray) -> np.ndarray:
    """Average ranks, ties handled (for Spearman)."""
    order = a.argsort()
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(a) + 1)
    # average tied ranks
    _, inv, counts = np.unique(a, return_inverse=True, return_counts=True)
    sums = np.zeros(len(counts))
    np.add.at(sums, inv, ranks)
    return (sums / counts)[inv]


def _spearman(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    if len(x) < 2:
        return None
    return _pearson(_rankdata(np.asarray(x, float)), _rankdata(np.asarray(y, float)))


def _accuracy(pred: Sequence[str], true: Sequence[str]) -> Optional[float]:
    if not pred:
        return None
    return sum(p == t for p, t in zip(pred, true)) / len(pred)


def _f1_macro(pred: Sequence[str], true: Sequence[str]) -> Optional[float]:
    if not pred:
        return None
    classes = sorted(set(true) | set(pred))
    f1s = []
    for c in classes:
        tp = sum(p == c and t == c for p, t in zip(pred, true))
        fp = sum(p == c and t != c for p, t in zip(pred, true))
        fn = sum(p != c and t == c for p, t in zip(pred, true))
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        f1s.append(f1)
    return float(np.mean(f1s)) if f1s else None


# ── Métriques ordinales (l'engagement est un construit ordinal LOW<MED<HIGH) ────
# L'accuracy 3-classes pénalise autant une confusion LOW↔HIGH qu'une LOW↔MEDIUM,
# alors qu'elles n'ont pas la même gravité. Les métriques ci-dessous tiennent
# compte de l'ordre — c'est le standard sur les benchmarks d'engagement (DAiSEE).

LEVELS = ("LOW", "MEDIUM", "HIGH")
_LEVEL_IDX = {lvl: i for i, lvl in enumerate(LEVELS)}


def confusion_matrix(pred: Sequence[str], true: Sequence[str]) -> np.ndarray:
    """Matrice de confusion 3×3 (lignes = vrai, colonnes = prédit)."""
    m = np.zeros((len(LEVELS), len(LEVELS)), dtype=int)
    for p, t in zip(pred, true):
        if p in _LEVEL_IDX and t in _LEVEL_IDX:
            m[_LEVEL_IDX[t], _LEVEL_IDX[p]] += 1
    return m


def quadratic_weighted_kappa(
    pred: Sequence[str], true: Sequence[str]
) -> Optional[float]:
    """QWK entre niveaux ordinaux. 1 = accord parfait, 0 = hasard, <0 = pire.

    Pénalise les désaccords proportionnellement au *carré* de la distance
    ordinale (LOW↔HIGH pèse 4× plus que LOW↔MEDIUM).
    """
    if not pred:
        return None
    n = len(LEVELS)
    O = confusion_matrix(pred, true).astype(float)
    total = O.sum()
    if total == 0:
        return None
    # Matrice de poids quadratiques
    w = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            w[i, j] = (i - j) ** 2 / (n - 1) ** 2
    # Matrice attendue sous indépendance (produit des marges)
    row_marg = O.sum(axis=1)
    col_marg = O.sum(axis=0)
    E = np.outer(row_marg, col_marg) / total
    denom = float((w * E).sum())
    if denom == 0:
        return None  # dégénéré (une seule classe observée)
    return float(1.0 - (w * O).sum() / denom)


def _norm_cdf(z: float) -> float:
    import math

    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def mann_whitney_u(
    x: Sequence[float], y: Sequence[float]
) -> Tuple[Optional[float], Optional[float]]:
    """Test U de Mann-Whitney (bilatéral), approximation normale + correction des ties.

    Compare deux échantillons indépendants (ex. scores engagé vs désengagé) sans
    hypothèse de normalité. Renvoie (U, p-value). Adapté aux petits effectifs,
    mais l'approximation normale reste indicative pour de très petits n.
    """
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return None, None
    combined = np.concatenate([np.asarray(x, float), np.asarray(y, float)])
    ranks = _rankdata(combined)
    r1 = float(ranks[:n1].sum())
    u1 = r1 - n1 * (n1 + 1) / 2.0
    u = min(u1, n1 * n2 - u1)
    mu = n1 * n2 / 2.0
    # Correction des ex-æquo pour l'écart-type
    _, counts = np.unique(combined, return_counts=True)
    n = n1 + n2
    tie_term = float(np.sum(counts**3 - counts))
    sigma_sq = (n1 * n2 / 12.0) * ((n + 1) - tie_term / (n * (n - 1)))
    if sigma_sq <= 0:
        return u, None
    z = (u - mu) / np.sqrt(sigma_sq)
    p = 2.0 * _norm_cdf(-abs(z))
    return u, float(p)


def _fmt(v: Optional[float], nd: int = 3) -> str:
    return "—" if v is None else f"{v:.{nd}f}"


# ── Data loading ───────────────────────────────────────────────────────────────


def load_rows(db_path: str) -> List[dict]:
    if not os.path.exists(db_path):
        sys.exit(f"DB not found: {db_path}")
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        cur = con.execute(
            "SELECT session_id, modality, text_score, audio_score, video_score, "
            "fusion_score, engagement_level, words, created_at "
            "FROM engagement_metrics ORDER BY created_at"
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


def load_labels(path: str) -> Dict[str, dict]:
    labels: Dict[str, dict] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            sid = (row.get("session_id") or "").strip()
            if not sid:
                continue
            try:
                rating = float(row["rating"])
            except (KeyError, ValueError):
                continue
            labels[sid] = {
                "rating": rating,
                "level": rating_to_level(rating),
                "condition": (row.get("condition") or "").strip() or None,
            }
    return labels


# ── Analyses ───────────────────────────────────────────────────────────────────

# The modality subsets evaluated in the ablation study.
CONFIGS: List[Tuple[str, Tuple[str, ...]]] = [
    ("Texte seul", ("text",)),
    ("Vidéo seule", ("video",)),
    ("Audio seul", ("audio",)),
    ("Texte + Vidéo", ("text", "video")),
    ("Texte + Audio", ("text", "audio")),
    ("Vidéo + Audio", ("video", "audio")),
    ("T + V + A (proposé)", ("text", "video", "audio")),
]


def row_scores(row: dict) -> Dict[str, Optional[float]]:
    return {
        "text": row.get("text_score"),
        "video": row.get("video_score"),
        "audio": row.get("audio_score"),
    }


def config_score(row: dict, mods: Tuple[str, ...]) -> Optional[float]:
    s = {m: row_scores(row).get(m) for m in mods}
    w = {m: DEFAULT_WEIGHTS[m] for m in mods}
    return weighted_fusion(s, w)


def describe(rows: List[dict]) -> None:
    print("\n## Couverture & statistiques descriptives\n")
    print(f"Total d'enregistrements : {len(rows)}")
    sessions = {r["session_id"] for r in rows if r["session_id"]}
    print(f"Sessions distinctes     : {len(sessions)}")
    print()
    print("| Modalité | n (présent) | couverture | moyenne | écart-type |")
    print("|----------|-------------|------------|---------|------------|")
    for mod in ("text", "video", "audio", "fusion"):
        col = "fusion_score" if mod == "fusion" else f"{mod}_score"
        vals = [r[col] for r in rows if r[col] is not None]
        cov = len(vals) / len(rows) if rows else 0
        mean = float(np.mean(vals)) if vals else None
        std = float(np.std(vals)) if vals else None
        print(f"| {mod} | {len(vals)} | {cov:.0%} | {_fmt(mean)} | {_fmt(std)} |")


def inter_modality_corr(rows: List[dict]) -> None:
    print("\n## Corrélations inter-modalités (cohérence des signaux)\n")
    pairs = [("text", "video"), ("text", "audio"), ("video", "audio")]
    print("| Paire | n | Pearson r | Spearman ρ |")
    print("|-------|---|-----------|------------|")
    for a, b in pairs:
        xs, ys = [], []
        for r in rows:
            va, vb = r[f"{a}_score"], r[f"{b}_score"]
            if va is not None and vb is not None:
                xs.append(va)
                ys.append(vb)
        print(
            f"| {a}–{b} | {len(xs)} | {_fmt(_pearson(xs, ys))} | "
            f"{_fmt(_spearman(xs, ys))} |"
        )


def ablation(rows: List[dict], labels: Dict[str, dict]) -> None:
    print("\n## Étude d'ablation — score vs vérité terrain\n")
    # Attach the session label to each row that has one.
    labeled = [(r, labels[r["session_id"]]) for r in rows if r["session_id"] in labels]
    if not labeled:
        print(
            "_Aucune ligne ne correspond aux labels fournis. Vérifiez que les "
            "`session_id` du CSV correspondent à ceux de la base._"
        )
        return
    print(f"Lignes labellisées : {len(labeled)}\n")
    print("| Configuration | n | Pearson r | Spearman ρ | Accuracy | F1-macro |")
    print("|---------------|---|-----------|------------|----------|----------|")
    for name, mods in CONFIGS:
        scores, ratings, pred_levels, true_levels = [], [], [], []
        for r, lab in labeled:
            s = config_score(r, mods)
            if s is None:
                continue
            scores.append(s)
            ratings.append(lab["rating"])
            pred_levels.append(level_of(s))
            true_levels.append(lab["level"])
        if not scores:
            print(f"| {name} | 0 | — | — | — | — |")
            continue
        print(
            f"| {name} | {len(scores)} | {_fmt(_pearson(scores, ratings))} | "
            f"{_fmt(_spearman(scores, ratings))} | "
            f"{_fmt(_accuracy(pred_levels, true_levels))} | "
            f"{_fmt(_f1_macro(pred_levels, true_levels))} |"
        )
    print(
        "\n_Lecture : si la ligne « T + V + A » dépasse chaque ligne unimodale, "
        "l'apport du multimodal (H2) est soutenu._"
    )

    # Métriques ordinales + matrice de confusion pour la config complète (T+V+A).
    pred_levels, true_levels = [], []
    for r, lab in labeled:
        s = config_score(r, ("text", "video", "audio"))
        if s is None:
            continue
        pred_levels.append(level_of(s))
        true_levels.append(lab["level"])
    if pred_levels:
        qwk = quadratic_weighted_kappa(pred_levels, true_levels)
        print("\n### Analyse ordinale — config T + V + A\n")
        print(
            f"**QWK (Quadratic Weighted Kappa) : {_fmt(qwk)}** — accord ordinal "
            "(1 = parfait, 0 = hasard). Plus pertinent que l'accuracy car "
            "l'engagement est ordinal (LOW < MEDIUM < HIGH)."
        )
        cm = confusion_matrix(pred_levels, true_levels)
        print("\nMatrice de confusion (lignes = vrai, colonnes = prédit) :\n")
        header = " | ".join(f"préd. {l}" for l in LEVELS)
        print(f"| vrai \\ prédit | {header} |")
        print("|" + "---|" * (len(LEVELS) + 1))
        for i, lvl in enumerate(LEVELS):
            cells = " | ".join(str(int(cm[i, j])) for j in range(len(LEVELS)))
            print(f"| **{lvl}** | {cells} |")
        print(
            "\n_Lecture : une masse hors-diagonale concentrée sur les cases "
            "adjacentes (LOW↔MEDIUM, MEDIUM↔HIGH) indique un problème de seuils, "
            "pas d'ordre — voir `calibrate.py`._"
        )


def separability(rows: List[dict], labels: Dict[str, dict]) -> None:
    conds = {
        labels[r["session_id"]]["condition"]
        for r in rows
        if r["session_id"] in labels and labels[r["session_id"]]["condition"]
    }
    if len(conds) < 2:
        return
    print("\n## Séparabilité par condition (engagé vs désengagé)\n")
    print("| Condition | n | score fusionné moyen | écart-type |")
    print("|-----------|---|----------------------|------------|")
    by_cond: Dict[str, List[float]] = {}
    for cond in sorted(conds):
        vals = [
            config_score(r, ("text", "video", "audio"))
            for r in rows
            if r["session_id"] in labels
            and labels[r["session_id"]]["condition"] == cond
        ]
        vals = [v for v in vals if v is not None]
        by_cond[cond] = vals
        if vals:
            print(
                f"| {cond} | {len(vals)} | {_fmt(float(np.mean(vals)))} | "
                f"{_fmt(float(np.std(vals)))} |"
            )

    # Test statistique : les deux conditions sont-elles séparées significativement ?
    if "engaged" in by_cond and "disengaged" in by_cond:
        u, p = mann_whitney_u(by_cond["engaged"], by_cond["disengaged"])
        print(
            f"\n**Test de Mann-Whitney (engagé vs désengagé)** : U = {_fmt(u, 1)}, "
            f"p = {_fmt(p)}."
        )
        if p is not None:
            verdict = (
                "différence significative (p < 0,05) → H1 soutenue"
                if p < 0.05
                else "différence non significative au seuil 0,05 (effectif "
                "probablement insuffisant)"
            )
            print(f"_{verdict}._")


# ── Latency benchmark (real-time claim) ────────────────────────────────────────


def benchmark(repeats: int = 20) -> None:
    print("\n## Benchmark de latence (temps réel)\n")
    import base64
    import time

    results: List[Tuple[str, Optional[float], str]] = []

    # Video — score a real face image.
    try:
        import cv2
        from ai.engagement.video_core import compute_video_score, MP_AVAILABLE

        img_path = "ui/static/grad-students.png"
        img = cv2.imread(img_path)
        if img is None or not MP_AVAILABLE:
            results.append(("video", None, "image/CV stack unavailable"))
        else:
            _, buf = cv2.imencode(".jpg", img)
            b64 = base64.b64encode(buf).decode()
            compute_video_score(b64)  # warm-up (model load, weights)
            t0 = time.perf_counter()
            for _ in range(repeats):
                compute_video_score(b64)
            results.append(("video", (time.perf_counter() - t0) / repeats * 1000, "OK"))
    except Exception as e:  # pragma: no cover
        results.append(("video", None, f"error: {e}"))

    # Audio — score a short synthetic voiced tone.
    try:
        import io
        import numpy as _np
        import soundfile as sf
        from ai.engagement.audio_core import compute_audio_score, LIBROSA_AVAILABLE

        if not LIBROSA_AVAILABLE:
            results.append(("audio", None, "librosa unavailable"))
        else:
            sr = 16000
            t = _np.linspace(0, 1.0, sr, False)
            tone = 0.1 * _np.sin(2 * _np.pi * 160 * t).astype("float32")
            bio = io.BytesIO()
            sf.write(bio, tone, sr, format="WAV")
            b64 = base64.b64encode(bio.getvalue()).decode()
            compute_audio_score(b64)  # warm-up
            t0 = time.perf_counter()
            for _ in range(repeats):
                compute_audio_score(b64)
            results.append(("audio", (time.perf_counter() - t0) / repeats * 1000, "OK"))
    except Exception as e:  # pragma: no cover
        results.append(("audio", None, f"error: {e}"))

    # Text — score a representative message.
    try:
        from ai.engagement.text_core import compute_text_metrics

        msg = "Can you explain how photosynthesis works, step by step please?"
        t0 = time.perf_counter()
        for i in range(repeats):
            compute_text_metrics(f"bench-user", msg, session_id="bench")
        results.append(("text", (time.perf_counter() - t0) / repeats * 1000, "OK"))
    except Exception as e:  # pragma: no cover
        results.append(("text", None, f"error: {e}"))

    print("| Composant | latence moyenne (ms) | statut |")
    print("|-----------|----------------------|--------|")
    for name, ms, status in results:
        print(f"| {name} | {_fmt(ms, 1)} | {status} |")
    print(f"\n_Moyenne sur {repeats} exécutions (hors warm-up)._")


def list_sessions(rows: List[dict]) -> None:
    """List each session so you can map it to the scenario you performed.

    Print one row per session with its time span, message count, which
    modalities were captured, and the mean fused score — enough to recognise
    "that was my engaged S1 run" and assign a rating in labels.csv.
    """
    by_session: Dict[str, List[dict]] = {}
    for r in rows:
        by_session.setdefault(r["session_id"] or "(none)", []).append(r)

    print("\n## Sessions enregistrées (pour construire labels.csv)\n")
    print("| session_id | début | n | modalités | fusion moy. |")
    print("|------------|-------|---|-----------|-------------|")
    for sid, rs in sorted(by_session.items(), key=lambda kv: kv[1][0]["created_at"]):
        start = (rs[0]["created_at"] or "")[:19]
        mods = "".join(
            m[0].upper()
            for m in ("text", "video", "audio")
            if any(r[f"{m}_score"] is not None for r in rs)
        )
        fusions = [r["fusion_score"] for r in rs if r["fusion_score"] is not None]
        mean_f = _fmt(float(np.mean(fusions))) if fusions else "—"
        print(f"| {sid} | {start} | {len(rs)} | {mods or '—'} | {mean_f} |")
    print(
        "\n_Copiez les `session_id` voulus dans labels.csv et ajoutez votre "
        "note d'engagement 1-5 (+ condition)._"
    )


# ── CLI ────────────────────────────────────────────────────────────────────────


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="var/engagement.db", help="engagement DB path")
    p.add_argument("--labels", help="optional ground-truth labels CSV")
    p.add_argument(
        "--benchmark",
        action="store_true",
        help="run the latency benchmark (needs mediapipe/librosa)",
    )
    p.add_argument("--repeats", type=int, default=20, help="benchmark repeats")
    p.add_argument(
        "--list-sessions",
        action="store_true",
        help="list sessions (id, time, modalities) to help build labels.csv",
    )
    args = p.parse_args()

    print("# Analyse de l'engagement multimodal\n")

    if args.benchmark:
        benchmark(args.repeats)
        if not (args.labels or args.list_sessions):
            return

    rows = load_rows(args.db)
    if not rows:
        print("Aucun enregistrement dans la base.")
        return

    if args.list_sessions:
        list_sessions(rows)
        if not args.labels:
            return

    describe(rows)
    inter_modality_corr(rows)

    if args.labels:
        labels = load_labels(args.labels)
        print(f"\nLabels chargés : {len(labels)} sessions")
        ablation(rows, labels)
        separability(rows, labels)
    else:
        print(
            "\n_Fournissez `--labels labels.csv` pour l'étude d'ablation "
            "(corrélation/accuracy vs vérité terrain)._"
        )


if __name__ == "__main__":
    main()
