# US-P04 — Parent IA Sessions

## Overview
Allows parents to view their child's AI learning sessions with quality metrics and difficulty alerts.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ia-sessions/` | Session list + stats |
| GET | `/api/v1/ia-sessions/{id}/detail` | Session detail + AI summary |
| GET | `/api/v1/ia-sessions/{id}/transcript` | Full transcript |

## Data Model

```json
{
  "sessions": [{
    "id": "uuid",
    "subject": "Mathematics",
    "duration_minutes": 38,
    "quality_score": 9.1,
    "difficulty_alert": false,
    "themes": ["Functions", "Derivatives"],
    "questions": ["Question 1?"],
    "resume": "AI generated summary",
    "metrics": { "engagement": 9.1, "comprehension": 8.5, "autonomy": 8.8 },
    "status": "terminee"
  }],
  "stats": { "total": 2, "avec_alerte": 1, "score_moyen": 6.63 }
}
```

## Security

- Anti-IDOR: `_require_parent_access(parent_id, child_id)` on every request
- JWT auth required on all endpoints
- child_id loaded from `/api/v1/parent/me/students` — never hardcoded

## User Guide (Parent)

1. Log in as parent at `/auth`
2. Navigate to **Sessions IA** in the sidebar
3. View KPI cards: total sessions, time, avg score, questions
4. Filter by subject using the pill buttons
5. Click a session card to view detail + AI summary
6. Click "View full transcript" for the full conversation

## Tests

```bash
python -m pytest backend/tests/unit/test_sessions_ia_unit.py      # 11 tests
python -m pytest backend/tests/integration/test_sessions_ia_integ.py  # 8 tests
RUN_E2E=1 python -m pytest tests/e2e/test_sessions_ia_e2e.py      # E2E
```
