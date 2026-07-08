# Outils d'évaluation de l'engagement (`manual_check/`)

Ce dossier regroupe les outils d'**évaluation quantitative** de l'estimateur
d'engagement multimodal. Ils analysent les mesures produites par le système
(stockées dans la base dédiée `engagement.db`) en les confrontant à une **vérité
terrain** annotée, et produisent les statistiques, corrélations, étude d'ablation,
test de séparabilité, calibration des seuils et benchmark de latence présentés dans
le mémoire.

---

## 1. Prérequis

- Environnement Python du projet (conda `tutorai-env`).
- La base `var/engagement.db`, alimentée automatiquement par le système à chaque
  interaction (texte, vidéo, vocale).
- Un fichier de vérité terrain `manual_check/labels.csv` (voir §3).

Raccourci pour l'interpréteur Python utilisé dans les exemples :
```bash
PY=/home/anas/miniconda3/envs/tutorai-env/bin/python3.11
```

---

## 2. Contenu du dossier

| Fichier | Rôle |
|---------|------|
| `analyze.py` | Analyse principale : couverture, corrélations, **ablation**, **séparabilité**, benchmark de latence. |
| `calibrate.py` | **Calibration des seuils** de niveau (LOW / MEDIUM / HIGH) à partir de la distribution réelle des scores. |
| `labels.csv` | Vérité terrain : `session_id, rating (1–5), condition`. |
| `RESULTATS_ANALYSE.md` | Synthèse rédigée des résultats. |
| `sortie_benchmark.md` | Sortie brute du benchmark de latence. |
| `ab_analyze.py`, `grid_search.py` | Outils complémentaires (comparaison A/B, recherche de poids de fusion). |

---

## 3. Format de la vérité terrain (`labels.csv`)

Une ligne par session évaluée :

```csv
session_id,rating,condition
d6b2a100-e497-48b2-8210-32ac0bf3e27e,5,engaged
872c803a-971d-4761-8732-65dca048a3ee,2,disengaged
```

- **session_id** : identifiant de la session (voir `--list-sessions`).
- **rating** : auto-évaluation de l'engagement sur une échelle de Likert 1–5
  (1–2 = faible, 3 = moyen, 4–5 = élevé).
- **condition** : `engaged` ou `disengaged` (condition jouée lors du protocole).

---

## 4. Utilisation

### 4.1 Lister les sessions disponibles
Pour retrouver les `session_id` à reporter dans `labels.csv` :
```bash
$PY manual_check/analyze.py --list-sessions
```

### 4.2 Analyse complète (résultat principal)
Produit la couverture, les corrélations inter-modalités, l'étude d'ablation, la
matrice de confusion et le test de séparabilité :
```bash
$PY manual_check/analyze.py --labels manual_check/labels.csv
```

### 4.3 Benchmark de latence (temps réel)
```bash
$PY manual_check/analyze.py --benchmark
```

### 4.4 Calibration des seuils
Compare la stratégie de seuils par défaut à une calibration fondée sur les données :
```bash
$PY manual_check/calibrate.py --labels manual_check/labels.csv
```

> La sortie de chaque commande est au format **Markdown** (tableaux), directement
> exploitable. Pour la sauvegarder dans un fichier :
> ```bash
> $PY manual_check/analyze.py --labels manual_check/labels.csv > sortie_analyze.md
> ```

---

## 5. Lecture des résultats

| Indicateur | Signification |
|------------|---------------|
| **Pearson r / Spearman rho** | Corrélation entre le score estimé et la vérité terrain (proximité / cohérence d'ordre). |
| **Exactitude / F1-macro** | Qualité de la classification en niveaux LOW / MEDIUM / HIGH. |
| **QWK** (Quadratic Weighted Kappa) | Accord ordinal : pénalise davantage une confusion LOW↔HIGH qu'une confusion entre niveaux adjacents. |
| **Mann-Whitney (U, p)** | Test statistique de séparabilité entre conditions engagé et désengagé (p < 0.05 = significatif). |
| **Matrice de confusion** | Répartition des erreurs entre niveaux. |
| **Latence (ms)** | Coût de calcul par modalité (contrainte temps réel). |

L'**étude d'ablation** recombine les scores bruts par sous-ensemble de modalités
(texte seul, texte+vidéo, trimodal…) pour mesurer l'apport de chaque modalité ; la
fusion est renormalisée sur les modalités présentes, reproduisant la dégradation
gracieuse du système.

---

## 6. Reproduire l'ensemble des résultats du mémoire

```bash
PY=/home/anas/miniconda3/envs/tutorai-env/bin/python3.11

$PY manual_check/analyze.py --list-sessions                    # inventaire des sessions
$PY manual_check/analyze.py --labels manual_check/labels.csv   # analyse + ablation + séparabilité
$PY manual_check/analyze.py --benchmark                        # latence temps réel
$PY manual_check/calibrate.py --labels manual_check/labels.csv # calibration des seuils
```

La synthèse rédigée correspondante se trouve dans `RESULTATS_ANALYSE.md`.
