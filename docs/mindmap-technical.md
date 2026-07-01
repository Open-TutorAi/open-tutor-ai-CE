# Mind Map Feature — Technical Documentation

## Overview
Brief description of the feature and its purpose.

## API Endpoints

### GET /api/v1/mindmap/context/{chat_id}
Extracts key concepts from a chat session.

**Response:**
```json
{
  "concepts": ["OOP", "Encapsulation", "Héritage", ...]
}
```

### POST /api/v1/mindmap/verify
Verifies the student's mind map against session concepts using the AI agent.

**Request body:**
```json
{
  "chat_id": "...",
  "nodes": [...],
  "edges": [...]
}
```

**Response:**
```json
{
  "validated": true/false,
  "score": ...,
  "covered_concepts": [...],
  "missing_concepts": [...],
  "feedback": "..."
}
```

### POST /api/v1/mindmap/export/pdf
Generates a downloadable PDF from the validated mind map.

**Request body:** ...
**Response:** PDF file (binary)

## Data Models

### MindMapNode
| Field | Type | Description |
|---|---|---|
| id | string | Unique node ID |
| label | string | Concept name |
| color | string | Node color |
| position | {x, y} | Canvas coordinates |

### MindMapEdge
| Field | Type | Description |
|---|---|---|
| source | string | Source node ID |
| target | string | Target node ID |

## Dependencies
- `reportlab` — PDF generation

## Architecture Notes
Brief note on how frontend (Svelte) talks to backend (FastAPI routes), and how the AI agent verification works (which model/prompt is used, minimum concept threshold, etc.)