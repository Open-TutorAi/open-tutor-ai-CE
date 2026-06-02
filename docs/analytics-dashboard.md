# Analytics Dashboard — Guide enseignant

> **Public** : enseignant·e·s et administrateur·trice·s d'une instance Open TutorAI
> **Version** : ajoutée par la PR [#239](https://github.com/Open-TutorAi/open-tutor-ai-CE/pull/239)
> **Page concernée** : `/admin/analytics`

Ce document n'est pas un rapport académique. C'est le guide qu'un·e collègue lit avant d'utiliser le tableau de bord pour la première fois en classe.

---

## 1. À quoi sert ce tableau de bord ?

Quand vos élèves utilisent le tuteur IA, ils laissent deux types de traces utiles :

- des **👍 / 👎** sur les réponses,
- des **corrections d'expert** (quand un enseignant compare deux réponses et indique laquelle est la meilleure, avec une raison).

Le tableau de bord agrège ces traces et répond à **quatre questions concrètes** :

| Question pédagogique | Onglet à consulter |
|---|---|
| Est-ce que le tuteur s'améliore vraiment cette semaine ? | **Overview** (taux de réponses positives + delta) |
| Sur quels types d'erreurs mes collègues corrigent le plus ? | **Corrections** (catégories d'erreurs) |
| Quel modèle d'IA donne les meilleures réponses pour ma matière ? | **Models** (score par modèle) |
| Sur quelles matières / quels niveaux l'IA est-elle le plus en difficulté ? | **Pedagogy** (matière × niveau) |

---

## 2. Prérequis techniques

- Une instance Open TutorAI en cours d'exécution (Docker compose ou Kubernetes).
- **Un compte avec le rôle `admin`** — les autres rôles reçoivent un 401.
- Aucune migration de base de données n'est nécessaire : le tableau de bord lit les tables `feedback` (déjà présente) et `opentutorai_support` (déjà présente).

---

## 3. Accéder au tableau de bord

1. Connectez-vous avec votre compte administrateur.
2. Ouvrez l'espace d'administration via la barre de navigation supérieure.
3. Cliquez sur l'onglet **« Analytics »** (à côté de « Models Evaluations »).

L'URL directe est `https://<votre-instance>/admin/analytics`.

---

## 4. Lire chaque onglet

### Overview
- **Total feedback** : nombre total d'événements 👍/👎/correction sur la période.
- **Positive rate** : % de retours positifs. Le **delta** (en vert / rouge) compare avec la période précédente de même durée.
- **Expert corrections** : nombre de corrections déposées par des enseignants.
- **Models in use** : nombre de modèles d'IA distincts utilisés.

Sous les cartes, deux mini-graphiques montrent l'évolution quotidienne (positif en vert, négatif en rouge).

### Corrections
- **Resolution rate** : part des corrections qui ont une « raison » renseignée. Plus ce chiffre est haut, mieux vos collègues documentent leurs corrections.
- **Top error categories** : les catégories d'erreurs les plus fréquentes (par exemple : `erreur-de-calcul`, `hors-sujet`, `langue-incorrecte`). Les catégories sont extraites automatiquement du champ « raison » saisi par les enseignants.

### Models
Pour les 10 modèles les plus utilisés :
- score global (👍 / total),
- évolution sur 14 jours,
- couleur : vert si ≥ 70 %, ambre entre 40 % et 70 %, rouge en dessous.

### Contributors
Classement des utilisateur·trice·s qui ont donné le plus de retours, avec leur rôle (admin / teacher / user / parent). Utile pour reconnaître les enseignant·e·s les plus actif·ve·s dans l'amélioration de l'outil.

### Pedagogy
Tableau matière × niveau, croisé avec les sessions du portail élève (`opentutorai_support`). Le taux de réponses positives par couple matière/niveau montre où l'IA est faible — c'est précisément là où il faut soit changer de modèle, soit améliorer la base de connaissances (RAG).

---

## 5. Sélecteurs et rafraîchissement

- **Range** (en haut à droite) : `24h`, `7d`, `30d`, `90d`, `all`. Tous les compteurs se mettent à jour.
- **Refresh** : bouton manuel.
- Le tableau de bord se rafraîchit automatiquement **toutes les 30 secondes** quand l'onglet est visible. Sur un onglet d'arrière-plan, il s'arrête pour économiser le réseau.

---

## 6. Exemple d'utilisation en classe

> *Contexte* : Mme A. enseigne l'informatique en Tronc Commun. Elle utilise Open TutorAI avec ses 32 élèves pour la révision avant un contrôle.

1. **Avant le cours** : Mme A. ouvre l'onglet **Pedagogy**, filtre sur la période `7d`. Elle voit que pour la matière *« Programmation Python »*, niveau *« beginner »*, le taux positif n'est que de **42 %**.
2. **Pendant le cours** : elle annonce qu'elle va donner un coup de main à l'IA. Elle laisse les élèves discuter avec le tuteur et corrige elle-même 5 réponses faibles (en utilisant l'outil de comparaison de réponses).
3. **Après le cours** : elle ouvre l'onglet **Corrections** et vérifie que ses 5 corrections sont bien comptées. Elle consulte **Top error categories** : la catégorie dominante est `confusion-print-input`.
4. **Action concrète** : elle ajoute une fiche RAG sur la différence `print` / `input` à la base de connaissances. Une semaine plus tard, elle revient sur **Pedagogy** : le taux positif sur « Programmation Python — beginner » passe à **61 %**.

Le tableau de bord ne remplace pas la pédagogie de l'enseignant·e — il sert de **boussole** pour décider où mettre l'effort.

---

## 7. Confidentialité

- Le tableau de bord est **réservé aux administrateurs**. Aucun élève ne voit les notes des autres.
- Les noms d'utilisateur·trice·s apparaissent dans l'onglet **Contributors**. Pour anonymiser, désactivez cet onglet en commentant la `<a>` dans `src/routes/(app)/admin/+layout.svelte`.

---

## 8. Limites connues

- La catégorisation des erreurs est faite par *slug* du champ libre « raison ». Si vos enseignants écrivent des phrases longues et différentes pour la même erreur, elles seront comptées séparément. Une convention d'équipe (mots-clés courts) est recommandée.
- La page utilise du polling. Pour un mode 100 % temps réel, voir la suite (Sprint 4) : intégration Socket.io.
- L'onglet **Pedagogy** ne peut afficher qu'une matière dont au moins un élève a démarré un *Support* lié à un *chat* — c'est-à-dire après au moins une session.

---

## 9. Pour aller plus loin (Sprint 4 envisagé)

- Export CSV des séries temporelles (utile pour le conseil pédagogique).
- Push temps réel via `socket.io` (au lieu du polling 30 s).
- Filtre par classe (`classroom_id`) quand le modèle « Classroom » sera livré.
- Drill-through : cliquer sur une catégorie d'erreur ouvre la liste des conversations concernées.

---

## 10. Support

- **Issue tracker** : <https://github.com/Open-TutorAi/open-tutor-ai-CE/issues>
- **Discussion de cette contribution** : [PR #239](https://github.com/Open-TutorAi/open-tutor-ai-CE/pull/239)
- **Auteur de la contribution** : Badr Essaadaoui (CRMEF Souss-Massa, M2 Informatique)
