# Error Cards — Carte d'erreur instantanée

## Description

La fonctionnalité **Carte d'erreur** analyse automatiquement les échanges entre
un étudiant et le tuteur IA pour détecter les erreurs de compréhension et générer
des fiches pédagogiques structurées. Ces fiches sont sauvegardées par support de
cours et peuvent être consultées ou exportées en PDF à tout moment.

**Rôle concerné :** Étudiant uniquement
**Déclencheur :** Chaque réponse du tuteur IA sur une page de support
**Point d'entrée UI :** `/student/support/:id` → panneau `ErrorCardsPanel` sous le chat

---

## Architecture

```
Backend                              Frontend
───────                              ────────
learning/supports/                   ui/src/lib/
  error_cards/                         apis/supports/
    repository.py                        error-cards.ts          ← appels fetch
    service.py                       features/student/components/
    __init__.py                        ErrorCardsPanel.svelte    ← panneau UI
data/models/                           exportErrorCardsPdf.ts    ← export PDF
  error_card.py                        tutor/Chat.svelte         ← déclencheur
gateway/http/routers/
  supports.py                        pages/
gateway/http/                          SupportDetails.svelte     ← intégration
  dependencies.py
```

Le service d'analyse est appelé en **fire-and-forget** depuis `Chat.svelte` :
la réponse du tuteur est affichée immédiatement, l'analyse s'exécute en parallèle.

---

## Modèle de données

**Table :** `error_card`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | `String` (UUID) | Clé primaire |
| `support_id` | `String` | Support de cours associé (FK) |
| `user_id` | `String` | Étudiant propriétaire (FK) |
| `concept` | `String` | Concept mal compris |
| `error_description` | `Text` | Description de l'erreur détectée |
| `simple_explanation` | `Text` | Reformulation pédagogique |
| `correct_example` | `Text` | Exemple correct illustrant le concept |
| `source_user_message` | `Text` | Message de l'étudiant ayant déclenché la détection |
| `source_assistant_message` | `Text` | Réponse du tuteur ayant identifié l'erreur |
| `created_at` | `DateTime` | Date de création (UTC) |

**Méthode :** `to_dict()` — sérialisation JSON pour les endpoints.

**Fichier ORM :** `data/models/error_card.py`

---

## Endpoints

### POST `/supports/{support_id}/error-cards/analyze`

Déclenche l'analyse LLM d'un échange pour détecter des erreurs de compréhension.

**Auth :** JWT requis, rôle `student`

**Body JSON :**
```json
{
  "user_message": "string",
  "assistant_message": "string"
}
```

**Réponse 200 :**
```json
{
  "cards": [
    {
      "id": "uuid",
      "concept": "string",
      "error_description": "string",
      "simple_explanation": "string",
      "correct_example": "string",
      "created_at": "ISO8601"
    }
  ]
}
```

**Réponse 200 sans erreur détectée :** `{ "cards": [] }`

---

### GET `/supports/{support_id}/error-cards`

Liste toutes les fiches d'erreurs du support pour l'utilisateur connecté.
Résultats triés par `created_at` décroissant (plus récent en premier).

**Auth :** JWT requis, rôle `student`

**Réponse 200 :**
```json
[
  {
    "id": "uuid",
    "support_id": "string",
    "user_id": "string",
    "concept": "string",
    "error_description": "string",
    "simple_explanation": "string",
    "correct_example": "string",
    "source_user_message": "string",
    "source_assistant_message": "string",
    "created_at": "ISO8601"
  }
]
```

Retourne `[]` quand aucune fiche n'existe pour cette combinaison étudiant/support.

---

### DELETE `/supports/{support_id}/error-cards/{card_id}`

Supprime définitivement une fiche. Vérifie que la fiche appartient à l'utilisateur
connecté et au support indiqué.

**Auth :** JWT requis, rôle `student`

**Réponse 200 :** `{ "message": "Card deleted" }`
**Réponse 403 :** fiche appartenant à un autre utilisateur
**Réponse 404 :** fiche introuvable ou `card_id`/`support_id` incohérents

---

## Fichiers créés et modifiés

### Créés

| Fichier | Rôle |
|---------|------|
| `data/models/error_card.py` | Modèle SQLAlchemy `ErrorCard` + `to_dict()` |
| `learning/supports/error_cards/__init__.py` | Package marker |
| `learning/supports/error_cards/repository.py` | Accès données : `create`, `list_by_support_and_user`, `delete` |
| `learning/supports/error_cards/service.py` | Logique métier : appel LLM, parsing JSON, orchestration |
| `ui/src/lib/apis/supports/error-cards.ts` | Client fetch typé : `analyzeErrorCards`, `getErrorCards`, `deleteErrorCard` |
| `ui/src/lib/features/student/components/ErrorCardsPanel.svelte` | Panneau repliable avec badge, liste de fiches, bouton export |
| `ui/src/lib/features/student/components/exportErrorCardsPdf.ts` | Export PDF via Blob + `createObjectURL` |

### Modifiés

| Fichier | Modification |
|---------|-------------|
| `gateway/http/routers/supports.py` | Ajout des 3 routes error-cards |
| `gateway/http/dependencies.py` | Ajout de `get_error_cards_service` |
| `ui/src/lib/features/student/components/pages/SupportDetails.svelte` | Monte `ErrorCardsPanel` sous le chat |
| `ui/src/lib/features/student/components/tutor/Chat.svelte` | Appel fire-and-forget à `analyzeErrorCards` après chaque réponse IA |
| `ui/src/lib/features/chat/components/Chat.svelte` | Transmet le prop `supportId` pour activer la détection |

---

## Flux complet

```
1. L'étudiant envoie un message dans le chat (/student/support/:id)
2. Chat.svelte reçoit la réponse du tuteur IA
3. La réponse est affichée immédiatement — aucun blocage
4. Chat.svelte appelle analyzeErrorCards(supportId, userMsg, assistantMsg)
   sans await sur le rendu (fire-and-forget)
5. POST /supports/{id}/error-cards/analyze est appelé
6. ErrorCardsService envoie les deux messages au LLM avec un prompt structuré
7. Le LLM retourne un tableau JSON d'erreurs (peut être vide)
8. Chaque erreur est persistée via ErrorCardsRepository.create()
9. L'API retourne { "cards": [...] }
10. ErrorCardsPanel.svelte rafraîchit la liste
11. Un toast apparaît si cards.length > 0
```

---

## Choix techniques

| Choix | Justification |
|-------|---------------|
| Analyse fire-and-forget | Ne bloque pas l'UX — la réponse du tuteur s'affiche immédiatement |
| `linkedSupportId` au niveau module | Survit aux re-renders Svelte sans réactivité superflue ni store global |
| Tableau `cards[]` (pas un objet seul) | Un seul échange peut révéler plusieurs erreurs sur des concepts distincts |
| Export PDF dans un `.ts` séparé | Le CSS `@page` entre en conflit avec PostCSS/Svelte si placé dans un `<style>` |
| `Blob + URL.createObjectURL` | Remplace `document.write()` déprécié dans les navigateurs modernes |
| `@page { margin: 0; }` | Supprime l'URL `localhost` dans l'en-tête Chrome lors de l'impression PDF |

---

## Changelog

### Added
- `ErrorCard` ORM model and `error_card` database table
- `ErrorCardsRepository` with `create`, `list_by_support_and_user`, `delete`
- `ErrorCardsService` with LLM-based error detection and JSON parsing
- `POST /supports/{support_id}/error-cards/analyze` endpoint
- `GET /supports/{support_id}/error-cards` endpoint
- `DELETE /supports/{support_id}/error-cards/{card_id}` endpoint
- `ErrorCardsPanel.svelte` — collapsible panel with counter badge and per-card delete
- `exportErrorCardsPdf.ts` — PDF export via Blob + createObjectURL
- `error-cards.ts` — typed fetch client for all three endpoints

### Changed
- `SupportDetails.svelte` — mounts `ErrorCardsPanel` below the chat zone
- `Chat.svelte` (student tutor) — triggers fire-and-forget analysis after each AI reply
- `Chat.svelte` (shared) — forwards `supportId` prop to enable error detection
- `supports.py` router — registers the three new error-card routes
- `dependencies.py` — adds `get_error_cards_service` dependency factory
