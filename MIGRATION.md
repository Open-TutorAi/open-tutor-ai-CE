# Migration from OpenWebUI-Based Backend to Root-Driven Domain Architecture

## Overview

OpenTutorAI has been restructured from a nested `backend/open_tutorai/gateway/` hierarchy with OpenWebUI dependencies to a **root-driven, domain-based architecture** following patterns from Hermes. OpenWebUI and Hermes remain references for UI contract and implementation techniques; they are not runtime dependencies and their package names are not used as internal domains.

## Key Changes

### File Structure

**Before:**

```
backend/
  main.py                    ← Mounted entire OpenWebUI
  open_tutorai/
    main.py
    config.py
    models/
      database.py
    routers/
      auths.py
      supports.py
      response_feedbacks.py
  routers/
    auths.py
    supports.py
    response_feedbacks.py
  models/
    database.py
  config/
    config.py
```

**After (v1.0.0):**

```
open-tutor-ai-CE/
│
├── main.py                        ← Uvicorn entry point
│
├── ── Application Domains ───────────────────────────────────────────────
│
├── config/                        ← App settings & constants
│   ├── settings.py
│   └── constants.py
│
├── common/                        ← Shared utilities
│   ├── exceptions.py
│   └── logging.py
│
├── gateway/                       ← Transport layer (HTTP + Realtime)
│   ├── http/
│   │   ├── app.py                 ← lifespan, CORS, SPA mount, router registration
│   │   ├── dependencies.py        ← auth guard + service factories
│   │   └── routers/               ← one file per domain
│   │       ├── auth.py            ← /auths/* + /api/v1/auths/*
│   │       ├── users.py           ← /api/v1/users/*
│   │       ├── chats.py           ← /api/v1/chats/*
│   │       ├── configs.py         ← /api/v1/configs/*
│   │       ├── models.py          ← /api/v1/models/*
│   │       ├── providers.py       ← /api/v1/providers/*
│   │       ├── files.py           ← /api/v1/files/*
│   │       ├── supports.py        ← /api/v1/supports/*
│   │       ├── self_regulation.py ← /api/v1/self_regulation/*
│   │       ├── app_info.py        ← /api/v1/platform/*
│   │       ├── retrieval.py       ← /api/v1/retrieval/*
│   │       ├── audio.py           ← /api/v1/audio/*
│   │       └── images.py          ← /api/v1/images/*
│   └── realtime/
│       └── socket.py              ← Socket.IO ASGI; JWT auth; /realtime/socket.io
│
├── data/                          ← Data layer
│   ├── database.py                ← SQLAlchemy engine + session factory
│   ├── models/                    ← ORM models (one file per entity)
│   └── repositories/
│       └── base.py                ← Generic CRUD repository
│
├── accounts/                      ← Auth, users, roles, permissions
│   ├── users/                     ← User repository + AccountService
│   ├── auth/                      ← Reserved for auth flows
│   ├── roles/                     ← Reserved for role policies
│   └── permissions/               ← Reserved for permission policies
├── learning/                      ← Tutoring workflows
│   ├── sessions/                  ← Chat CRUD, tags, sharing, search
│   ├── supports/                  ← Personalized tutoring supports
│   ├── learners/                  ← Reserved learner domain
│   ├── teachers/                  ← Reserved teacher domain
│   ├── classrooms/                ← Reserved classroom domain
│   └── courses/                   ← Reserved course domain
├── ai/                            ← AI capabilities
│   ├── llm/                       ← LLM schemas, service, transports
│   ├── model_catalog/             ← Model overlays/catalog
│   ├── providers/                 ← Provider registry, config, proxy, adapters
│   ├── retrieval/                 ← RAG pipeline
│   │   └── knowledge/             ← Knowledge bases for RAG
│   ├── media/                     ← Audio (TTS/STT) + image generation
│   ├── memory/                    ← Reserved for future agent memory
│   └── tools/                     ← Reserved for future agent tools
├── content/                       ← Files and learning resources
│   ├── files/                     ← File upload & ownership
│   └── resources/                 ← Reserved learning resources
├── governance/                    ← Governance and HITL evaluation
│   └── self_regulation/           ← LLM response evaluation feedback
├── system/                        ← App-level services
│   ├── configs/                   ← App config KV (AppConfig)
│   └── app/                       ← Reserved app info/bootstrap services
│
├── tests/                         ← Pytest suite (one file per domain)
│
├── ── Frontend ──────────────────────────────────────────────────────────
│
├── ui/                            ← SvelteKit application
│   ├── src/
│   │   ├── lib/apis/              ← API clients (one folder per domain)
│   │   ├── lib/components/        ← Reusable Svelte components
│   │   ├── lib/i18n/              ← i18n translations (AR / FR / EN)
│   │   └── routes/                ← SvelteKit file-based routing
│   ├── static/                    ← Assets (avatars, images, audio)
│   ├── cypress/                   ← E2E tests
│   ├── .eslintrc.cjs
│   ├── .prettierrc
│   └── package.json
│
├── ── DevOps ────────────────────────────────────────────────────────────
│
├── devops/
│   ├── docker/                    ← Dockerfiles + Docker Compose overlays
│   │   ├── Dockerfile.backend     ← Multi-stage: Node build → Python API serve
│   │   ├── Dockerfile.frontend
│   │   ├── docker-compose.yaml    ← Base stack (Python API + Ollama)
│   │   ├── docker-compose.gpu.yaml
│   │   ├── docker-compose.amdgpu.yaml
│   │   ├── docker-compose.api.yaml
│   │   └── docker-compose.data.yaml
│   └── scripts/                   ← Dev & ops shell scripts
│       ├── dev.sh                 ← Local Python API hot-reload
│       ├── run.sh                 ← Build + run Docker container
│       ├── run-compose.sh         ← Full Compose stack with GPU/API flags
│       └── run-ollama-docker.sh   ← Start Ollama in Docker
│
├── ── Project ───────────────────────────────────────────────────────────
│
├── docs/                          ← Documentation
├── kubernetes/                    ← Helm charts (in progress)
├── .github/workflows/             ← CI/CD (Python app format, frontend build, release)
├── requirements.txt
├── pyproject.toml
├── Makefile
├── .env.example
└── var/                           ← Runtime only, gitignored (DB, uploads, vector_db)
```

### Dependency Changes

**Removed:**

- `open_webui` runtime dependency
- All imports from `open_webui.models`, `open_webui.routers`, `open_webui.utils`
- `open_webui` patches and configuration

**Added:**

- `fastapi`, `sqlalchemy`, `pydantic` (now explicit)
- `pyjwt`, `passlib`, `bcrypt` (for auth)

### API Endpoint Changes — OpenTutorAI Public Contract

Routes are grouped by domain. All versioned routes are under `/api/v1/*`. Auth is mounted
at two prefixes to match the UI's `TUTOR_BASE_URL` / `TUTOR_API_BASE_URL` split.

The public route names intentionally keep OpenTutorAI's UI contract (`auths`, `chats`,
`models`, `providers`, `self_regulation`, `knowledge`, `audio`, `images`). Internal
packages use professional domain names: `accounts`, `learning`, `ai`, `content`,
`governance`, `system`, `gateway`, `data`, `common`, and `config`.

| Domain                       | Routes                                                                                                                                                                                                                                                                                                                                                                  | Notes                                                                  |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `health`                     | `GET /health`                                                                                                                                                                                                                                                                                                                                                           | No version prefix. Docker healthcheck.                                 |
| `accounts (auths)`           | `POST /auths/signup`, `GET /auths/user-count`                                                                                                                                                                                                                                                                                                                           | Root mount — `TUTOR_BASE_URL`                                          |
| `accounts (auths)`           | `POST /api/v1/auths/signin`, `GET /api/v1/auths/`, `GET /api/v1/auths/signout`                                                                                                                                                                                                                                                                                          | `/api/v1` mount                                                        |
| `app_info`                   | `GET /api/v1/platform/version\|changelog\|banners`                                                                                                                                                                                                                                                                                                                      | Public route kept for UI contract; no root `platform/` package         |
| `users`                      | `GET /api/v1/users/`, `GET/POST /api/v1/users/user/settings\|info`, `POST /api/v1/users/update/role`, `GET/POST/{id} DELETE/{id}`                                                                                                                                                                                                                                       | User management (admin-gated list/role/delete)                         |
| `system/configs`             | `GET/POST /api/v1/configs/models\|banners\|suggestions\|...`, `GET /api/v1/configs/export`, `POST /api/v1/configs/import`                                                                                                                                                                                                                                               | App-level KV config (writes admin-gated)                               |
| `ai/model_catalog`           | `GET /api/v1/models/`, `POST /api/v1/models/create`, `GET/POST/DELETE /api/v1/models/model?id=`, `POST /api/v1/models/model/toggle`                                                                                                                                                                                                                                     | Model overlays (ownership-gated mutations)                             |
| `ai/providers (OpenAI)`      | `GET/POST /api/v1/providers/openai/config\|urls\|keys\|verify`, `GET /api/v1/providers/openai/models[/{idx}]`, `POST /api/v1/providers/openai/chat/completions`, `POST /api/v1/providers/openai/audio/speech`                                                                                                                                                           | Hermes-style core; model-list TTL cache; admin config, non-admin proxy |
| `ai/providers (Ollama)`      | `GET/POST /api/v1/providers/ollama/config\|urls\|verify`, `GET /api/v1/providers/ollama/api/version[/{idx}]`, `GET /api/v1/providers/ollama/api/tags[/{idx}]`, `POST /api/v1/providers/ollama/api/generate\|embeddings\|chat`, `POST/DELETE /api/v1/providers/ollama/api/pull\|create\|delete[/{idx}]`, `POST /api/v1/providers/ollama/models/download\|upload[/{idx}]` | Native Ollama adapter isolated; model-mgmt admin-only                  |
| `learning/sessions`          | `GET/POST/DELETE /api/v1/chats/*`                                                                                                                                                                                                                                                                                                                                       | Full chat CRUD + archive/pin/share/tags/folder/search/clone            |
| `learning/supports`          | `POST /api/v1/supports/create`, `POST /api/v1/supports/upload-file`, `GET /api/v1/supports/list[?status=]`, `GET/PATCH/DELETE /api/v1/supports/{id}`, `PATCH /api/v1/supports/{id}/update-chat`                                                                                                                                                                         | Tutoring support requests                                              |
| `governance/self_regulation` | `GET/POST /api/v1/self_regulation/config\|feedback`, `GET /api/v1/self_regulation/feedbacks/all[/export]`, `GET/DELETE /api/v1/self_regulation/feedback/{id}`                                                                                                                                                                                                           | HITL evaluation of LLM responses                                       |
| `content/files`              | `POST /api/v1/files/`, `GET /api/v1/files/`, `GET /api/v1/files/all`, `GET/DELETE /api/v1/files/{id}`, `GET /api/v1/files/{id}/content`                                                                                                                                                                                                                                 | Owned file upload                                                      |
| `ai/retrieval/knowledge`     | `GET/POST/DELETE /api/v1/knowledge/*`                                                                                                                                                                                                                                                                                                                                   | Knowledge bases used by RAG                                            |
| `ai/media`                   | `GET/POST /api/v1/audio/*`, `GET/POST /api/v1/images/*`                                                                                                                                                                                                                                                                                                                 | AI audio and image capabilities                                        |
| `realtime`                   | Socket.IO ASGI sub-app at `/realtime/socket.io`                                                                                                                                                                                                                                                                                                                         | JWT auth on connect; replaces `/ws/socket.io`                          |

**Removed (forbidden namespaces):**

| Old path           | Replaced by                                                 |
| ------------------ | ----------------------------------------------------------- |
| `/openai/*`        | `/api/v1/providers/openai/*`                                |
| `/ollama/*`        | `/api/v1/providers/ollama/*`                                |
| `/api/chat/*`      | `/api/v1/chats/*` or `/api/v1/providers/*/chat/completions` |
| `/ws/socket.io`    | `/realtime/socket.io`                                       |
| `WEBUI_SECRET_KEY` | `SECRET_KEY`                                                |

### Database Model Changes

**User Model**

- Moved from `open_webui.models.users` to `data.models.user.User`
- Added `profile_image_url`, `created_at`, `updated_at` fields
- Uses direct SQLAlchemy (no open_webui Base)

**Support Model**

- Moved from custom location to `data.models.support.Support`
- Rich schema aligned with UI: `subject`, `short_description`, `learning_type`, `level`,
  `content_language`, `access_type`, `keywords` (comma-separated), `chat_id`, `avatar_id`, …
- Status: `pending` (default), no hard constraint on values
- `SupportFile` model added for upload attachments (ownership validated in `SupportsService`)

**Feedback Model**

- Moved from `open_webui.models.feedbacks` to `data.models.feedback.Feedback`
- Renamed context: "response_feedbacks" → "self_regulation"
- Maintains backward compatibility with response tracking

### Configuration

Environment variables moved from various sources to unified `config/settings.py`:

```env
# Database (now SQLite by default — runtime file in var/, not tracked by Git)
DATABASE_URL=sqlite:///./var/tutorai.db

# Auth (JWT instead of open_webui tokens)
SECRET_KEY=your-secret-key
JWT_EXPIRATION_HOURS=24

# CORS (direct config, no open_webui dependency)
CORS_ALLOW_ORIGIN=http://localhost:3000,http://localhost:5173
```

### Running the Application

**Before:**

```bash
cd backend
uvicorn backend.main:app --reload
```

**After:**

```bash
uvicorn main:app --reload
# or
python main.py
```

## Migration Checklist

- [x] Extract configuration to root-level `config/` module
- [x] Create independent database models (User, Support, Feedback)
- [x] Implement repository pattern for data access
- [x] Create domain services (AccountService, SupportsService, SelfRegulationService)
- [x] Create HTTP gateway with dependency injection
- [x] Implement JWT authentication (replace open_webui auth)
- [x] Create API routers for each domain
- [x] Remove backend/ directory
- [x] Update project dependencies (remove open-webui)
- [x] Add test suite
- [x] Verify all imports clean of open_webui/backend references
- [x] Implement full provider surface (OpenAI + Ollama — config/proxy/discovery/model-mgmt)
- [x] Socket.IO ASGI sub-mount at /realtime/socket.io
- [x] Repoint UI base-URL constants to /api/v1/providers/\* and /realtime/socket.io
- [x] Replace hardcoded contract test with UI-scanner (test_contract_coverage.py)
- [x] Reorganize root domains into `accounts/`, `learning/`, `ai/`, `content/`, `governance/`, and `system/`

## Current Status

The root-driven structure is complete and fully operational:

- **210 tests passing** across all domains (auth, users, configs, models, providers, chats, realtime, files, supports, self_regulation)
- All provider endpoints implemented — Hermes-style unified proxy core matching the full UI contract (~25 endpoints per provider)
- Socket.IO realtime layer mounted at `/realtime/socket.io`; UI repointed
- Contract test dynamically scans `ui/src/lib/apis/**/*.ts` to verify API coverage; no hardcoded paths
- Service/repository separation applied throughout — routers contain no ORM access
- Internal package names now separate gateway, accounts, learning, AI, content, governance, system, data, UI, and devops concerns
- Single Docker image (multi-stage: Node build → Python serve)
- Runtime data isolated to `var/` (gitignored)

## Future Steps — Agentic Phase

The architecture follows the Hermes pattern intentionally:

1. **Agent Framework** — add `ai/agents/` when the agentic phase begins
2. **LLM Integration** — `ai/providers/proxy.py` unified transport is the base; add multi-provider routing via `ProviderProfile.transport` field
3. **Provider Registry** — `ai/providers/profiles.py` ready to add new providers (one dict entry each)
4. **Vector Storage** — `var/vector_db/` runtime path; `ai/retrieval/` wraps retrieval behavior
5. **MCP / Tool Use** — extend the reserved `ai/tools/` domain following Hermes techniques

## Database Migration

If upgrading from previous OpenTutorAI installation:

1. Export existing data from old database
2. Run new application to create fresh schema
3. Import data into new models (schema may differ)
4. Verify data integrity

### Schema strategy & the teacher section

This project does **not** use a schema-migration framework (e.g. Alembic). On startup the app
calls SQLAlchemy's `create_all()`, which **creates any missing tables** but **never alters an
existing table** (it will not add a column to a table that already exists).

**Teacher section:** it introduces **only new tables** — `classrooms`, `enrollments`,
`invitations`, `guardian_links`, `assignments`, `submissions`, `class_resources`,
`assignment_templates`, `monitor_states`, `monitor_away_events`, `conversations`,
`conversation_participants`, `messages`, `exam_configs`, `exam_sessions`, `exam_violations`. It
adds **no columns to any pre-existing table**. So on a clean existing install these tables are
created automatically on the next start — **no manual step, no loss of existing data**.

**General caveat (any future column change, or a DB that already holds an _older_ version of the
teacher tables):** because there are no migrations, a new/renamed column on an already-created
table won't be applied, and queries against it will fail. On a **development** database, reset it:

```bash
rm -f var/tutorai.db   # or the file named by your DATABASE_URL, then restart
```

⚠️ This **deletes all local data** — development/throwaway installs only, never a database with
real user data. The long-term fix is to adopt **Alembic** (versioned, in-place migrations); it is
tracked as a project-wide improvement, independent of the teacher section.

## Known Differences

1. **Authentication**: Now uses JWT tokens instead of open_webui session tokens
2. **Database**: Default to SQLite instead of PostgreSQL (configurable)
3. **Feedback naming**: "response_feedbacks" → "self_regulation" for domain clarity
4. **UI serving**: `gateway.http.app` mounts `ui/build/` as a SPA via `SPAStaticFiles` when the
   directory exists (production/Docker). In local dev the build is absent and the Python app serves
   API only; the SvelteKit dev server runs independently on port 5173.

## Support

For questions or issues with the migration:

- Check `TROUBLESHOOTING.md`
- Review specific module `__init__.py` files for available exports
- Ensure all dependencies in `requirements.txt` are installed
