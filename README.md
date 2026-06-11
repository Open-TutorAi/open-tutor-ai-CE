<div align="center">

<img src="ui/static/static/splash.png" width="100px" alt="Open TutorAI Logo" />

# Open TutorAI

**An open-source AI-powered educational platform — built by the community, for the community.**

[![GitHub Stars](https://img.shields.io/github/stars/Open-TutorAi/open-tutor-ai-CE?style=social)](https://github.com/Open-TutorAi/open-tutor-ai-CE)
[![GitHub Forks](https://img.shields.io/github/forks/Open-TutorAi/open-tutor-ai-CE?style=social)](https://github.com/Open-TutorAi/open-tutor-ai-CE)
[![Repo Size](https://img.shields.io/github/repo-size/Open-TutorAi/open-tutor-ai-CE)](https://github.com/Open-TutorAi/open-tutor-ai-CE)
[![Last Commit](https://img.shields.io/github/last-commit/Open-TutorAi/open-tutor-ai-CE)](https://github.com/Open-TutorAi/open-tutor-ai-CE/commits)
[![Discord](https://img.shields.io/badge/Discord-Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.gg/BTQtE2deEm)
[![License](https://img.shields.io/badge/License-BSD--3--Clause-blue)](LICENSE)

[📖 Documentation](https://opentutorai.com/docs/intro) · [🚀 Roadmap](https://opentutorai.com/docs/roadmap) · [💬 Discord](https://discord.gg/BTQtE2deEm) · [📧 Enterprise Support](mailto:opentutorai@gmail.com)

</div>

---

## Overview

**OpenTutorAI-CE** (Community Edition) is an open-source, AI-powered educational platform that makes personalized tutoring accessible to everyone. It serves as the foundation for an Enterprise Edition (EE) and is actively maintained by the community.

> **Enterprise Edition available** — includes custom theming & branding, SLA support, LTS versions, and more. [Contact us →](mailto:opentutorai@gmail.com)

---

## ✨ Features

### 🤖 AI & Model Support

- **Ollama & OpenAI-compatible APIs** — connect to LMStudio, GroqCloud, Mistral, OpenRouter, and more
- **Multi-model conversations** — engage multiple models in parallel for optimal responses
- **Model Builder** — create Ollama models, custom agents, and import models with ease
- **Local RAG** — integrate textbooks, notes, and assignments into context-aware tutoring sessions
- **Web Search for RAG** — real-time research via Google PSE, SearXNG, Brave, DuckDuckGo, and more

### 🎓 Personalized Learning

- **Adaptive tutoring support** — tailor the experience to each learner's style and curriculum
- **Personalized LLM + avatar generation** — pair AI personas with individual learner profiles
- **Avatar discussion mode** — lifelike conversational interface for immersive learning

### 🎙️ Rich Interaction

- **Voice, video & avatar modes** — hands-free, multimodal interactions
- **Web browsing** — load live web content into chat using the `#url` command
- **Image generation** — integrated support for AUTOMATIC1111, ComfyUI, and DALL-E

### 🛡️ Security & Access Control

- **Role-Based Access Control (RBAC)** — granular permissions and user groups
- **Human-in-the-loop governance** — LLM response evaluation and self-regulation framework

### 🌍 Platform & UX

- **Docker-first deployment** — single command setup with `:ollama` and `:cuda` images
- **Progressive Web App (PWA)** — offline mode on localhost, installable on mobile
- **Responsive design** — optimized across desktop, tablet, and mobile
- **Multilingual (i18n)** — Arabic, French, English, with community-contributed translations

---

## 🗂️ Project Structure

```
open-tutor-ai-CE/
│
├── main.py                        # Python entry point (uvicorn)
│
├── ── Application Domains ─────────────────────────────────────────
├── accounts/                      # Auth, users, roles, permissions
├── learning/                      # Learners, teachers, classrooms, courses
│   ├── sessions/                  # Chat sessions, tags, sharing, search
│   └── supports/                  # Personalized tutoring supports
├── ai/                            # LLM, providers, RAG, media, memory, tools
│   ├── llm/                       # LLM schemas, service, transports
│   ├── model_catalog/             # Model overlays/catalog
│   ├── providers/                 # OpenAI-compatible + Ollama providers
│   ├── retrieval/                 # RAG pipeline and knowledge bases
│   └── media/                     # Audio (TTS/STT) + image generation
├── content/                       # Files, uploads, learning resources
├── governance/                    # HITL governance and LLM evaluation
│   └── self_regulation/           # Self-regulation feedback domain
├── system/                        # App-level configs and bootstrap
│
├── ── Gateway & Infrastructure ────────────────────────────────────
├── gateway/
│   ├── http/                      # FastAPI app, routers, dependencies
│   └── realtime/                  # Socket.IO ASGI (/realtime/socket.io)
├── data/                          # ORM models, DB engine, base repository
├── config/                        # App settings & constants
├── common/                        # Shared utilities (exceptions, logging)
├── tests/                         # Pytest suite
│
├── ── Frontend ────────────────────────────────────────────────────
├── ui/                            # SvelteKit application
│   ├── src/lib/apis/              # API clients (one folder per domain)
│   ├── src/lib/components/        # Reusable Svelte components
│   ├── src/lib/i18n/              # Translations (AR / FR / EN)
│   ├── src/routes/                # File-based routing
│   ├── static/                    # Assets (avatars, images, audio)
│   └── cypress/                   # E2E tests
│
├── ── DevOps ──────────────────────────────────────────────────────
├── devops/
│   ├── docker/                    # Dockerfiles + Compose overlays
│   └── scripts/                   # Dev & ops shell scripts
│
├── ── Project ─────────────────────────────────────────────────────
├── docs/                          # Documentation
├── kubernetes/                    # Helm charts
├── .github/workflows/             # CI/CD
└── var/                           # Runtime only, gitignored (DB, uploads, vector_db)
```

> Full annotated structure: [MIGRATION.md](MIGRATION.md)

---

## 🚀 Installation

Choose the setup that fits your workflow:

| Method                                         | Best for                            |
| ---------------------------------------------- | ----------------------------------- |
| [Docker Compose](#-docker-compose-recommended) | Quick start, production, most users |
| [Local Development](#-local-development)       | Hot-reload, active contribution     |

---

### 🐳 Docker Compose (Recommended)

**Prerequisites:** Docker + Docker Compose · Git · 8 GB RAM recommended

#### 1. Clone

```bash
git clone https://github.com/Open-TutorAi/open-tutor-ai-CE.git
cd open-tutor-ai-CE
```

#### 2. Configure Environment

```bash
cp .env.example .env
```

For **production**, generate a secure secret key:

```bash
sed -i.bak "s/^SECRET_KEY=.*/SECRET_KEY=$(openssl rand -hex 32)/" .env && rm .env.bak
```

> For **local development**, the `.env.example` defaults work as-is (`DEBUG=true`).

#### 3. Start the Stack

**With Ollama (local models):**

```bash
docker compose --env-file .env -f devops/docker/docker-compose.yaml up --build
```

This starts:

- `open-tutorai` → API + frontend at **http://localhost:8080**
- `ollama` → local model server at **http://localhost:11434**

**Without Ollama (external OpenAI-compatible API):**

```bash
docker compose --env-file .env -f devops/docker/docker-compose.yaml up --build open-tutorai
```

Set `OPENAI_API_BASE_URL` and `OPENAI_API_KEY` in `.env`.

#### 4. Pull AI Models

```bash
docker exec -it ollama ollama pull llama3.2
docker exec -it ollama ollama list
```

If the API was already running before pulling, restart it:

```bash
docker compose --env-file .env -f devops/docker/docker-compose.yaml restart open-tutorai
```

#### 5. Open the App

Navigate to **http://localhost:8080** — the **first registered account becomes the administrator**.

#### GPU Support

```bash
# NVIDIA
docker compose --env-file .env \
  -f devops/docker/docker-compose.yaml \
  -f devops/docker/docker-compose.gpu.yaml up --build

# AMD
docker compose --env-file .env \
  -f devops/docker/docker-compose.yaml \
  -f devops/docker/docker-compose.amdgpu.yaml up --build
```

#### Stopping / Resetting

```bash
# Stop services
docker compose --env-file .env -f devops/docker/docker-compose.yaml down

# Full reset (removes all data volumes)
docker compose --env-file .env -f devops/docker/docker-compose.yaml down -v
```

---

### 🛠️ Local Development

**Prerequisites:** Python 3.11–3.12 · Node.js 18.13–22.x

#### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/open-tutor-ai-CE.git
cd open-tutor-ai-CE
```

#### 2. Backend Setup

```bash
# Create and activate a virtual environment
python3 -m venv .venv && source .venv/bin/activate
# or with conda:
# conda create -n tutorai-env python=3.11 && conda activate tutorai-env

pip install -r requirements.txt
cp .env.example .env
```

Start the API with hot-reload (available at **http://localhost:8080**):

```bash
uvicorn main:app --reload --port 8080

# Or use the convenience script:
chmod +x devops/scripts/dev.sh && ./devops/scripts/dev.sh
```

> Interactive API docs: **http://localhost:8080/docs**

#### 3. Frontend Setup

```bash
cd ui
npm install
npm run dev    # http://localhost:5173
```

#### 4. Optional: Local Ollama

```bash
# Install from https://ollama.com, then:
ollama pull llama3.2
```

Ensure `OLLAMA_BASE_URL=http://localhost:11434` is set in `.env`.

#### 5. Run Tests

```bash
pytest -q
```

---

## ⚙️ Environment Variables

| Variable              | Default                                       | Description                                                                       |
| --------------------- | --------------------------------------------- | --------------------------------------------------------------------------------- |
| `DEBUG`               | `true`                                        | Set `false` in production. Enables `SECRET_KEY` strength check.                   |
| `SECRET_KEY`          | _(dev placeholder)_                           | JWT signing key. Required in production (`openssl rand -hex 32`).                 |
| `DATABASE_URL`        | `sqlite:///./var/tutorai.db`                  | SQLAlchemy URL. Use PostgreSQL in production.                                     |
| `OLLAMA_BASE_URL`     | `http://localhost:11434`                      | Ollama server. Use `http://ollama:11434` inside Docker Compose.                   |
| `OPENAI_API_BASE_URL` | _(empty)_                                     | OpenAI-compatible API (LMStudio, GroqCloud, Mistral…).                            |
| `OPENAI_API_KEY`      | _(empty)_                                     | API key for the OpenAI-compatible provider.                                       |
| `GEMINI_API_KEY`      | _(empty)_                                     | Google Gemini API key.                                                            |
| `CORS_ALLOW_ORIGIN`   | `http://localhost:3000,http://localhost:5173` | Comma-separated allowed CORS origins.                                             |
| `UPLOAD_DIR`          | `./var/uploads`                               | Directory for uploaded files.                                                     |
| `MAX_UPLOAD_SIZE_MB`  | `100`                                         | Maximum upload size in MB.                                                        |
| `VECTOR_DB_PATH`      | `./var/vector_db`                             | ChromaDB storage path for RAG.                                                    |
| `EMBEDDING_MODEL`     | `sentence-transformers/all-MiniLM-L6-v2`      | Default embedding model for RAG.                                                  |
| `AUDIO_TTS_ENGINE`    | _(empty)_                                     | TTS engine (e.g. `openai`). Configure via Admin → Settings → Audio.               |
| `AUDIO_STT_ENGINE`    | _(empty)_                                     | STT engine. Configure via Admin → Settings → Audio.                               |
| `IMAGES_ENGINE`       | _(empty)_                                     | Image generation engine (e.g. `openai`). Configure via Admin → Settings → Images. |
| `GLOBAL_LOG_LEVEL`    | `INFO`                                        | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`.                               |

---

## 🆘 Troubleshooting

- **Connection issues** → See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or the [docs](https://opentutorai.com/docs/troubleshooting/)
- **Community help** → [Join our Discord](https://discord.gg/BTQtE2deEm)
- **Enterprise support** → [opentutorai@gmail.com](mailto:opentutorai@gmail.com)

---

## 📈 Star History

<a href="https://www.star-history.com/#Open-TutorAi/open-tutor-ai-CE&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Open-TutorAi/open-tutor-ai-CE&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Open-TutorAi/open-tutor-ai-CE&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Open-TutorAi/open-tutor-ai-CE&type=Date" />
  </picture>
</a>

---

## 📜 License

Licensed under the [BSD-3-Clause License](LICENSE).

---

<div align="center">

Founded by [Mohamed El Hajji](https://github.com/pr-elhajji) · Built by the community 💪

**[⭐ Star this repo](https://github.com/Open-TutorAi/open-tutor-ai-CE) · [🐛 Report an issue](https://github.com/Open-TutorAi/open-tutor-ai-CE/issues) · [💬 Join Discord](https://discord.gg/BTQtE2deEm)**

</div>
