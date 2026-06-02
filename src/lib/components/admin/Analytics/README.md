# Analytics Dashboard component

Implements upstream issue [#47](https://github.com/Open-TutorAi/open-tutor-ai-CE/issues/47).

## Files

- `Analytics.svelte` — 5-tab dashboard (Overview · Corrections · Models · Contributors · Pedagogy).
- `Sparkline.svelte` — inline SVG sparkline. Zero external deps.
- `BarRow.svelte` — bar-row primitive used by leaderboards.

## Data sources

The dashboard hits six backend endpoints, all admin-only, all under
`/api/v1/analytics/*`. See `backend/open_tutorai/routers/analytics.py`.

| Endpoint | Returns |
|---|---|
| `GET /summary` | totals, positive rate, delta vs previous window |
| `GET /feedback-timeseries` | daily / weekly buckets of positive vs negative |
| `GET /corrections` | trend + top categories + resolution rate |
| `GET /models` | per-model score and 14-day trajectory |
| `GET /contributors` | top users by feedback count |
| `GET /pedagogy` | feedback ⨯ `opentutorai_support` joined by `chat_id` |

## Design choices

- **No new dependencies** — sparklines are inline SVG to avoid pulling
  in Chart.js / D3 (those would block code review on bundle size).
- **Polling, not sockets, in v1** — simpler to merge; the follow-up to add a
  `socket.io` push is tracked in the PR body.
- **AbortController on the client** — every range / tab change cancels in-flight requests so a fast clicker can't corrupt state.
- **DB-portable SQL** — `json_extract` is used because Open WebUI ships
  both Postgres and SQLite. Don't replace it with PG-only operators.

## How to extend

1. To add a new tab, append to the `TABS` array at the top of `Analytics.svelte` and add a `{#if selectedTab === '<id>'}` block.
2. To add a new metric, add an endpoint in the router and a fetcher in `src/lib/apis/analytics/index.ts` — both layers are intentionally thin to keep contributions easy.

See [`docs/analytics-dashboard.md`](../../../../docs/analytics-dashboard.md) for the teacher-facing guide.
