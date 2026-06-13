# 📊 Student Performance Dashboard 

> **Projet :** Open-TutorAI Community Edition  
> **Fonctionnalité :** Tableau de bord de performance étudiant (dynamique + intégration backend)  
> **Auteur :** [@brahim1818](https://github.com/brahim1818)  
> **Fork :** [github.com/brahim1818/open-tutor-ai-CE](https://github.com/brahim1818/open-tutor-ai-CE)  
> **Pull Request :** [PR #221 — feat(student-dashboard)](https://github.com/Open-TutorAi/open-tutor-ai-CE/pull/221)

---

## 🎯 Description de la contribution

Cette contribution introduit un **tableau de bord de performance étudiant** entièrement fonctionnel, offrant aux apprenants une vue en temps réel et personnalisée de leur progression pédagogique.

Le dashboard s'intègre dans la plateforme Open-TutorAI via les endpoints backend existants, et remplace les données statiques de démonstration par des données dynamiques issues de l'API.

---

## 🛠️ Ce qui a été réalisé

### Composants SVG animés (Frontend)

| Composant | Description |
|---|---|
| `StatisticsPanel.svelte` | Panneau de statistiques globales (sessions, scores, temps moyen) |
| `PerformanceGauge.svelte` | Jauge circulaire SVG animée affichant le score global de l'étudiant |
| `CalendarWidget.svelte` | Widget calendrier interactif visualisant les jours d'activité |

Chaque composant est construit avec **SvelteKit**, animé en SVG natif, et conçu pour être réutilisable indépendamment.

### Intégration backend dynamique

- Connexion aux endpoints REST du backend FastAPI fournis par le collaborateur [@ZakariaElamrani](https://github.com/ZakariaElamrani)
- Remplacement complet des données mock par des appels API réels
- Gestion des états de chargement (`loading`, `error`, `empty`)
- Affichage conditionnel selon les données disponibles

---

## 📁 Structure des fichiers modifiés / créés

```
frontend/
└── src/
    └── lib/
        └── components/
            └── student/
                ├── StatisticsPanel.svelte     # Nouveau
                ├── PerformanceGauge.svelte    # Nouveau
                ├── CalendarWidget.svelte      # Nouveau
                └── StudentDashboard.svelte    # Modifié (intégration API)
```

---

## ⚙️ Installation & utilisation locale

### Prérequis

- Node.js ≥ 18
- Python ≥ 3.10
- Git

### Étapes

```bash
# 1. Cloner le fork
git clone https://github.com/brahim1818/open-tutor-ai-CE.git
cd open-tutor-ai-CE

# 2. Installer les dépendances frontend
cd frontend
npm install

# 3. Lancer le backend FastAPI (depuis la racine)
cd ../backend
pip install -r requirements.txt
uvicorn main:app --reload

# 4. Lancer le frontend SvelteKit
cd ../frontend
npm run dev
```

Accéder à l'application sur : `http://localhost:5173`

---

## 🖥️ Aperçu fonctionnel

Une fois connecté en tant qu'étudiant, le tableau de bord affiche :

- **Score global** via la jauge circulaire animée (en %)
- **Statistiques de session** : nombre de sessions, temps moyen, score moyen
- **Calendrier d'activité** : jours d'activité de la semaine en cours
- **Actualisation automatique** à chaque chargement de page

---

## 🔗 Liens utiles

| Ressource | Lien |
|---|---|
| Dépôt principal | [Open-TutorAi/open-tutor-ai-CE](https://github.com/Open-TutorAi/open-tutor-ai-CE) |
| Fork personnel | [brahim1818/open-tutor-ai-CE](https://github.com/brahim1818/open-tutor-ai-CE) |
| Pull Request | [PR #221](https://github.com/Open-TutorAi/open-tutor-ai-CE/pull/221) |

---

## 👤 Contributeur

**Brahim** — Professeur-stagiaire, filière Informatique  
CRMEF Souss-Massa, Agadir — Année 2025/2026  
GitHub : [@brahim1818](https://github.com/brahim1818)
