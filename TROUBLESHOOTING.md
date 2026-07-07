# Open TutorAI — Troubleshooting

## Architecture recap

The backend is a FastAPI application that:

- Serves the SvelteKit frontend as static files at `/`
- Exposes the REST API at `/api/v1/*`
- Proxies Ollama traffic via `/api/v1/providers/ollama/*`
- Handles real-time events at `/realtime/*` (Socket.IO)

All communication between the browser and Ollama goes through the backend — Ollama is never exposed directly to the frontend.

---

## Backend cannot reach Ollama

### Docker Compose (recommended)

Services share the internal `app-network`. The backend must use the **service name** as hostname:

```bash
OLLAMA_BASE_URL=http://ollama:11434
```

This is already set in `devops/docker/docker-compose.yaml`.

### Standalone Docker container

`localhost` inside a container refers to the container itself, not the host. Use `--network=host` to share the host network:

```bash
docker run -d --network=host \
  -v open-tutorai-var:/app/var \
  -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \
  -e SECRET_KEY=$(openssl rand -hex 32) \
  --name open-tutorai --restart always \
  open-tutorai
```

### Local development

Ollama and the backend both run on your machine. Use:

```bash
OLLAMA_BASE_URL=http://localhost:11434
```

---

## `SECRET_KEY must be set` on startup

The backend refuses to start in production (`DEBUG=false`) without a strong secret key.

**Solution — generate a key and add it to `.env`:**

```bash
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
```

For local development, set `DEBUG=true` in `.env`. The placeholder key is then accepted.

---

## Database errors after an update

If the schema changed, the old SQLite file may be incompatible.

**Drop and recreate (dev only — all data is lost):**

```bash
rm var/tutorai.db
```

**For Docker volumes:**

```bash
docker compose -f devops/docker/docker-compose.yaml down -v
docker compose -f devops/docker/docker-compose.yaml up --build
```

---

## Slow or timed-out Ollama responses

The default timeout for Ollama proxy requests is 5 minutes (300 seconds). The backend uses `httpx` for upstream calls — increase the timeout by setting in `.env`:

```bash
HTTPX_TIMEOUT=600   # seconds
```

---

## Port conflicts

| Service             | Default port | How to change                                                                           |
| ------------------- | ------------ | --------------------------------------------------------------------------------------- |
| Backend / frontend  | `8080`       | Edit `ports` in `docker-compose.yaml`                                                   |
| Ollama              | `11434`      | Set `OLLAMA_WEBAPI_PORT=<port>` in `.env` and use the `docker-compose.api.yaml` overlay |
| Frontend dev server | `5173`       | `npm run dev -- --port 5174`                                                            |

---

## Model not visible after pulling

If you pulled a model while the backend was already running, the model list cache may be stale. Restart the backend:

```bash
# Docker Compose
docker compose -f devops/docker/docker-compose.yaml restart open-tutorai

# Standalone container
docker restart open-tutorai
```

---

## CORS errors in the browser

Add your frontend origin to the `CORS_ALLOW_ORIGIN` variable:

```bash
CORS_ALLOW_ORIGIN=http://localhost:5173,https://your-domain.com
```

Wildcards (`*`) are supported but not recommended in production.

---

## Frontend shows blank page or 404

The backend serves the built frontend from `ui/build/`. If that directory is missing:

```bash
cd ui && npm install && npm run build
```

Then restart the backend. In Docker, the build happens automatically in the multi-stage `devops/docker/Dockerfile.backend`.

---

## Still stuck?

- Check the logs: `docker compose -f devops/docker/docker-compose.yaml logs -f`
- Open an issue: [github.com/Open-TutorAi/open-tutor-ai-CE/issues](https://github.com/Open-TutorAi/open-tutor-ai-CE/issues)
- Join the community: [Discord](https://discord.gg/BTQtE2deEm)
