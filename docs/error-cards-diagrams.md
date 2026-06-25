# Diagrammes UML — Carte d'erreur instantanée

Les fichiers image sont dans `docs/diagrams/`.
Les sources Mermaid supplémentaires sont disponibles en section repliable.

---

## 1. Diagramme d'activité — Flux complet

Montre le déroulement de bout en bout : envoi du message étudiant, génération de
la réponse tuteur, analyse fire-and-forget, insertion en DB, toast de notification,
puis consultation des fiches et export PDF.

![Diagramme d'activité](diagrams/activity-flow.png)

---

## 2. Diagramme de classes — Domaine error_cards

Montre les relations entre `ErrorCardsService`, `ErrorCardsRepository`,
`BaseRepository`, `ProvidersService`, `ErrorCard`, `Support` et `User`.

![Diagramme de classes](diagrams/class-diagram.png)

---

## 3. Diagramme de séquence — Flux détaillé en 4 phases

**Phase 1 — Chargement du support :** `GET /supports/:id/error-cards` au montage
**Phase 2 — Session de chat :** appel LLM tuteur, réponse streamed
**Phase 3 — Analyse fire-and-forget :** `POST .../error-cards/analyze`, loop INSERT par erreur
**Phase 4 — Consultation & export PDF :** rechargement des fiches, `exportErrorCardsToPdf()`, `Blob → window.print()`

![Diagramme de séquence](diagrams/sequence-diagram.png)

---

## Diagrammes Mermaid complémentaires

<details>
<summary>Diagramme entité-relation — Modèle de données</summary>

```mermaid
erDiagram
    USER {
        string id PK
        string name
        string email
    }

    SUPPORT {
        string id PK
        string title
        string user_id FK
    }

    ERROR_CARD {
        string id PK
        string support_id FK
        string user_id FK
        string concept
        text error_description
        text simple_explanation
        text correct_example
        text source_user_message
        text source_assistant_message
        datetime created_at
    }

    USER ||--o{ ERROR_CARD : "possède"
    SUPPORT ||--o{ ERROR_CARD : "contient"
```

</details>

<details>
<summary>Diagramme de composants — Frontend</summary>

```mermaid
graph TD
    SD[SupportDetails.svelte<br/>/student/support/:id]
    CT[Chat.svelte<br/>chat partagé]
    TT[tutor/Chat.svelte<br/>chat étudiant]
    EP[ErrorCardsPanel.svelte]
    EX[exportErrorCardsPdf.ts]
    EC[apis/supports/error-cards.ts]

    SD --> TT
    SD --> EP
    TT --> CT
    TT -->|analyzeErrorCards| EC
    EP -->|getErrorCards| EC
    EP -->|deleteErrorCard| EC
    EP -->|exportToPdf| EX

    style EC fill:#fef3c7,stroke:#d97706
    style EX fill:#fef3c7,stroke:#d97706
```

</details>

<details>
<summary>Diagramme d'état — Panneau ErrorCardsPanel</summary>

```mermaid
stateDiagram-v2
    [*] --> Chargement : Montage du composant
    Chargement --> Vide : GET /error-cards → []
    Chargement --> AvecFiches : GET /error-cards → [...]

    Vide --> AvecFiches : Nouvelles fiches détectées
    AvecFiches --> AvecFiches : Suppression d'une fiche (reste > 0)
    AvecFiches --> Vide : Suppression de la dernière fiche

    state AvecFiches {
        [*] --> Replié
        Replié --> Déplié : Clic sur l'en-tête
        Déplié --> Replié : Clic sur l'en-tête
        Déplié --> ExportPDF : Clic sur ↓ PDF
        ExportPDF --> Déplié : PDF généré
    }
```

</details>
