# User Stories — Module Blockly OpenTutorAI

## Acteurs
- **Étudiant** : apprenant connecté avec rôle `student`
- **Système IA** : Ollama (qwen2.5:0.5b)
- **Sandbox** : exécuteur Python isolé (subprocess)

---

## US-B01 — Accès au module Blockly
**En tant qu'** étudiant,
**Je veux** cliquer sur un bouton "🧩 Blockly" dans mon tableau de bord,
**Afin de** accéder à un formulaire de configuration d'exercice.

**Critères d'acceptation :**
- [ ] Bouton visible dans `/student/dashboard`
- [ ] Popup avec : Cours (obligatoire), Objectifs, Prérequis, Niveau
- [ ] Niveau par défaut : "Débutant"
- [ ] Bouton "Démarrer" désactivé si Cours vide

---

## US-B02 — Génération d'exercice par IA
**En tant qu'** étudiant,
**Je veux** que l'IA génère un exercice Python adapté à mon cours et niveau,
**Afin d'** avoir un exercice pertinent.

**Critères d'acceptation :**
- [ ] L'exercice a un titre et une description
- [ ] L'exercice contient des indices (hints)
- [ ] Génération < 30 secondes
- [ ] En cas d'erreur : message + bouton "Réessayer"

---

## US-B03 — Éditeur Blockly visuel
**En tant qu'** étudiant,
**Je veux** glisser-déposer des blocs pour construire mon programme,
**Afin d'** apprendre à programmer visuellement.

**Critères d'acceptation :**
- [ ] Toolbox : Logique, Boucles, Maths, Texte, Variables
- [ ] Niveau Intermédiaire ajoute : Listes
- [ ] Niveau Avancé ajoute : Fonctions
- [ ] Code Python généré automatiquement à chaque modification
- [ ] Bouton Reset efface le workspace

---

## US-B04 — Exécution du code
**En tant qu'** étudiant,
**Je veux** exécuter le code Python généré par mes blocs,
**Afin de** voir le résultat immédiatement.

**Critères d'acceptation :**
- [ ] Bouton ▶ Exécuter lance le code
- [ ] stdout s'affiche dans la console
- [ ] stderr affiché avec préfixe ⚠️
- [ ] Boucles infinies tuées après 5 secondes
- [ ] Temps d'exécution < 5 secondes

---

## US-B05 — Soumission et feedback IA
**En tant qu'** étudiant,
**Je veux** soumettre ma solution pour recevoir un score et un feedback,
**Afin de** savoir si ma solution est correcte.

**Critères d'acceptation :**
- [ ] Score sur 100 affiché
- [ ] Feedback IA bienveillant en français
- [ ] Feedback en streaming (SSE)
- [ ] Score ≥ 70 → badge vert ✅
- [ ] Score < 70 → badge rouge ❌

---

## US-B06 — Progression automatique de niveau
**En tant qu'** étudiant,
**Je veux** passer automatiquement au niveau suivant après 2 succès consécutifs,
**Afin de** progresser de Débutant → Intermédiaire → Avancé.

**Critères d'acceptation :**
- [ ] 2 scores ≥ 70 consécutifs → passage de niveau
- [ ] Message de félicitations affiché
- [ ] Toolbox Blockly mise à jour
- [ ] Niveau persisté (localStorage)
- [ ] Nouvel exercice généré automatiquement

---

## US-B07 — Sauvegarde du workspace
**En tant qu'** étudiant,
**Je veux** que mon workspace Blockly soit sauvegardé,
**Afin de** pouvoir reprendre mon travail plus tard.

**Critères d'acceptation :**
- [ ] POST `/api/blockly/workspace/save` sauvegarde le XML
- [ ] GET `/api/blockly/workspace/{id}` restaure le XML

---

## Priorités
| US   | Priorité   | Sprint |
|------|------------|--------|
| B01  | P0 — Clé   | 1      |
| B02  | P0 — Clé   | 1      |
| B03  | P0 — Clé   | 1      |
| B04  | P0 — Clé   | 1      |
| B05  | P1         | 1      |
| B06  | P1         | 2      |
| B07  | P2         | 2      |
