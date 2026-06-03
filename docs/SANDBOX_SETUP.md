# Piston Sandbox — Setup & Usage Guide

This document explains how to set up and run the Piston sandbox service
that isolates student Python code execution in Open TutorAI.

---

## Why a Sandbox?

Before this PR, student-submitted Python code ran via `exec()` inside the
API process. The `asyncio.wait_for()` timeout only cancelled the coroutine
waiting for the thread — the underlying thread kept running until completion,
even after the request had already failed.

**With Piston, each submission runs in a short-lived Docker container:**

| Guarantee | Detail |
|-----------|--------|
| Hard 5s timeout | Container killed by OS (SIGKILL) — no zombie threads |
| 64 MB memory limit | Enforced via cgroups |
| Network disabled | No outbound connections from student code |
| Filesystem isolation | No access to server files or internals |
| cgroups v2 compatible | Works on Ubuntu 22+, Debian 12 |

---

## Requirements

- **Docker** installed and running
- **Docker Compose** v2+ (`docker compose version`)
- The project cloned locally

---

## Setup — Option A: Local Development (`./dev.sh`)

Use this if you run the backend directly on your machine without Docker.

### Step 1 — Start Piston

```bash
# From the project root
docker compose -f docker-compose.piston.yml up -d
```

First run downloads the Piston image (~300 MB). Subsequent starts are instant.

### Step 2 — Install Python runtime in Piston

This only needs to be done once. Piston stores runtimes in a persistent volume.

```bash
curl -X POST http://localhost:2000/api/v2/packages \
  -H "Content-Type: application/json" \
  -d '{"language": "python", "version": "3.10.0"}'
```

Expected response: `{"language":"python","version":"3.10.0"}`

If already installed: `{"message":"Already installed"}` — that's fine.

### Step 3 — Start the backend

```bash
source venv/bin/activate
cd backend
./dev.sh
```

The backend uses `PISTON_URL=http://localhost:2000` by default
(set in `executor.py`). No extra configuration needed.

### Step 4 — Verify everything works

```bash
# Normal execution
curl -X POST http://localhost:8080/api/blockly/execute \
  -H "Content-Type: application/json" \
  -d '{"python_code": "print(3 + 5)"}'
```

Expected: `{"stdout":"8\n","error":null,...}`

```bash
# Timeout test (should be killed after 5 seconds)
curl -X POST http://localhost:8080/api/blockly/execute \
  -H "Content-Type: application/json" \
  -d '{"python_code": "while True: pass"}'
```

Expected: `{"error":"Délai dépassé...","timed_out":true,...}`

---

## Setup — Option B: Docker Compose (full stack)

Use this if you run the entire project with `docker compose up`.

### Step 1 — Start all services including Piston

The `docker-compose.piston.yml` adds Piston to the existing `app-network`
so the backend container can reach it by service name.

```bash
# Start the main stack
docker compose up -d

# Start Piston (in the same network)
docker compose -f docker-compose.piston.yml up -d
```

The backend automatically uses `PISTON_URL=http://piston:2000`
because `docker-compose.yaml` sets this environment variable:

```yaml
environment:
  - PISTON_URL=http://piston:2000
```

### Step 2 — Install Python runtime in Piston

```bash
curl -X POST http://localhost:2000/api/v2/packages \
  -H "Content-Type: application/json" \
  -d '{"language": "python", "version": "3.10.0"}'
```

### Step 3 — Verify

```bash
curl -X POST http://localhost:8080/api/blockly/execute \
  -H "Content-Type: application/json" \
  -d '{"python_code": "print(3 + 5)"}'
```

Expected: `{"stdout":"8\n","error":null,...}`

---

## How PISTON_URL is resolved

| Environment | Value | Set by |
|-------------|-------|--------|
| Local dev (`./dev.sh`) | `http://localhost:2000` | Default in `executor.py` |
| Docker Compose | `http://piston:2000` | `docker-compose.yaml` env var |

The code in `executor.py`:

```python
import os
PISTON_URL = os.getenv("PISTON_URL", "http://localhost:2000")
```

---

## Starting Piston on Every Session

Piston stops when Docker restarts. Run this at the start of each dev session:

```bash
# Option A — local dev
docker compose -f docker-compose.piston.yml up -d

# Option B — full Docker stack
docker compose up -d
docker compose -f docker-compose.piston.yml up -d
```

The Python runtime (`3.10.0`) persists in the `piston_data` Docker volume
and does not need to be reinstalled each time.

---

## Useful Commands

```bash
# Check Piston is running
docker ps | grep piston

# Check Piston logs
docker logs piston --tail 20

# List installed runtimes
curl http://localhost:2000/api/v2/runtimes

# Stop Piston
docker compose -f docker-compose.piston.yml down

# Stop Piston and delete runtime data (forces reinstall)
docker compose -f docker-compose.piston.yml down -v
```

---

## Troubleshooting

### "Service d'exécution indisponible"

Piston is not running. Start it:

```bash
docker compose -f docker-compose.piston.yml up -d
```

### "400 Bad Request" from Piston

Python runtime not installed. Run:

```bash
curl -X POST http://localhost:2000/api/v2/packages \
  -H "Content-Type: application/json" \
  -d '{"language": "python", "version": "3.10.0"}'
```

### "permission denied" connecting to Docker

Add your user to the docker group:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### "Failed to create control group" (Judge0 users)

Judge0 does not support cgroups v2 (Ubuntu 22+, Debian 12).
This PR uses Piston instead, which is fully compatible.

### Docker Compose command not found

Install the Compose plugin:

```bash
sudo apt update
sudo apt install docker-compose-v2 -y
```

---

## New API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/blockly/execute` | Free code execution (no test cases) |
| POST | `/api/blockly/test` | Run code against exercise test cases |
| POST | `/api/blockly/submit` | Score + AI feedback (SSE streaming) |

All three endpoints execute student code inside an isolated Piston container.
