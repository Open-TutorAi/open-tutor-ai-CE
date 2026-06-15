<div align="center">
<br/>
<img src="static/static/splash.png" width="120px" alt="">
<br/>

# Open TutorAI 👋

![GitHub stars](https://img.shields.io/github/stars/Open-TutorAi/open-tutor-ai-CE?style=social)
![GitHub forks](https://img.shields.io/github/forks/Open-TutorAi/open-tutor-ai-CE?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/Open-TutorAi/open-tutor-ai-CE?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/Open-TutorAi/open-tutor-ai-CE)
![GitHub language count](https://img.shields.io/github/languages/count/Open-TutorAi/open-tutor-ai-CE)
![GitHub top language](https://img.shields.io/github/languages/top/Open-TutorAi/open-tutor-ai-CE)
![GitHub last commit](https://img.shields.io/github/last-commit/Open-TutorAi/open-tutor-ai-CE)
[![Discord](https://img.shields.io/badge/Discord-Open_TutorAI-blue?logo=discord&logoColor=white)](https://discord.gg/BTQtE2deEm)

</div>
<br>
<div align="left">

**OpenTutorAI-CE** (Community Edition) is an open-source project designed to provide an educational and collaborative AI-powered platform. This public edition is the foundation for a proprietary Enterprise Edition (EE) and is built to encourage community contributions.

> [!TIP]

> **Looking for a Support?** – **[Speak with our support Team Today!](mailto:opentutorai@gmail.com)**

> Get **enhanced capabilities**, including **custom theming and branding**, **Service Level Agreement (SLA) support**, **Long-Term Support (LTS) versions**, and **more!**

For more information, be sure to check out our [Open TutorAI Documentation](https://opentutorai.com/docs/intro).

## ⭐ Key Features of Open TutorAI

Open TutorAI-CE is packed with powerful features designed for educational and collaborative AI experiences. Here's what makes it stand out:

- 🚀 **Effortless Setup with Docker**
  Set up your environment in minutes using Docker with support for `:ollama` and `:cuda` tagged images, ensuring a streamlined and hassle-free deployment.

- 🤖 **Ollama & OpenAI API Compatibility**
  Easily integrate OpenAI-compatible APIs for flexible conversations. Customize the API endpoint to connect with services like **LMStudio**, **GroqCloud**, **Mistral**, **OpenRouter**, and more—alongside local **Ollama** models.

- 🛡️ **Granular Permissions & User Groups**
  Admins can define detailed roles and permissions, allowing for secure, customized user experiences while promoting accountability and collaboration.

- 🧑‍💻 **Responsive & Mobile-Optimized Design**
  Enjoy a smooth user experience across desktops, laptops, and mobile devices with a fully responsive interface.

- 📱 **Progressive Web App (PWA) Support**
  Install Open TutorAI on your mobile device for an app-like experience, including **offline mode** on localhost and full access to core functionality.

- 🎤📹 **Voice, Video & Avatar Discussion Mode**
  Interact hands-free using integrated **voice and video calls**, or dive into an engaging experience with our **avatar-powered discussion mode**—a lifelike conversational interface that brings your AI to life.

- 🧑‍🏫 **Personalized Learning Experience**
  Open TutorAI is purpose-built for education:
  - 🎓 **Customize learning support** to meet individual learner needs.
  - 🧠 **Generate a personalized LLM**, optionally paired with a user-selected **avatar**, tailored to each learner's style, personality, or curriculum.

- 🛠️ **Model Builder**: Easily create Ollama models. Create and add custom characters/agents, customize chat elements, and import models effortlessly.

- 📚 **Local RAG Integration for Educational Content**
  Empower learners and educators with **Retrieval-Augmented Generation (RAG)** tailored for education. Seamlessly integrate textbooks, lecture notes, assignments, and research papers into the chat experience. Students can load documents directly into the conversation or access classroom resources from their document library using the `#` command—enabling **context-aware tutoring**, **assignment help**, and **in-depth discussion of study material**.

- 🔍 **Educational Web Search for RAG**
  Enhance learning with real-time **web search integration**. Students and educators can perform targeted research using providers like `Google PSE`, `SearXNG`, `Brave`, `DuckDuckGo`, and more—right from the chat. The search results are automatically injected into the conversation, enabling **fact-checking**, **discovery of up-to-date information**, and **exploration of external academic resources** without leaving the tutoring environment.

- 🌐 **Web Browsing Capability**: Seamlessly integrate websites into your chat experience using the `#` command followed by a URL. This feature allows you to incorporate web content directly into your conversations, enhancing the richness and depth of your interactions.

- 🎨 **Image Generation Integration**: Seamlessly incorporate image generation capabilities using options such as AUTOMATIC1111 API or ComfyUI (local), and OpenAI's DALL-E (external), enriching your chat experience with dynamic visual content.

- ⚙️ **Many Models Conversations**: Effortlessly engage with various models simultaneously, harnessing their unique strengths for optimal responses. Enhance your experience by leveraging a diverse set of models in parallel.

- 🔐 **Role-Based Access Control (RBAC)**: Ensure secure access with restricted permissions; only authorized individuals can access your Ollama, and exclusive model creation/pulling rights are reserved for administrators.

- 🌐🌍 **Multilingual Support**: Experience Open TutorAI in your preferred language with our internationalization (i18n) support. Join us in expanding our supported languages! We're actively seeking contributors!

- 🌟 **Continuous Updates**: We are committed to improving Open TutorAI with regular updates, fixes, and new features.

Want to learn more about Open TutorAI's features? Check out our [Open TutorAI documentation](https://opentutorai.com/docs/intro) for a comprehensive overview!

## 🔗 Also Check Out Open TutorAI Community!

Don't forget to explore our sibling project, [Open TutorAI Community](https://discord.gg/BTQtE2deEm), where you can discover, download, and explore customized Modelfiles. Open TutorAI Community offers a wide range of exciting possibilities for enhancing your chat interactions with Open TutorAI! 🚀

## 🔄 Backend Request Flow

### Current Architecture (v1.0+)

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client (Frontend)
    participant Router as Gateway Router<br/>(gateway/http/routers/)
    participant Deps as Dependencies<br/>(gateway/http/dependencies.py)
    participant Service as Domain Service<br/>(e.g., ai/llm/service.py)
    participant Repo as Repository<br/>(data/repositories/)
    participant DB as Databases<br/>(PostgreSQL/SQLite + ChromaDB)
    participant AI_Adapter as AI Provider Adapter<br/>(ai/providers/adapters/)
    participant Ext_AI as External AI<br/>(Ollama / OpenAI / Groq)

    Note over Client, Ext_AI: Complete Backend Request Flow (Clean Architecture v1.0+)

    rect rgb(255, 243, 224)
    Note right of Client: PHASE 1: GATEWAY (Ingress & Security)
    Client->>Router: HTTP Request (e.g., POST /api/v1/chat/completions)
    activate Router
    Router->>Deps: Depends(require_user), Depends(get_db)
    activate Deps
    Deps-->>Router: Authenticated User + DB Session
    deactivate Deps
    end

    rect rgb(243, 229, 245)
    Note right of Client: PHASE 2: CORE BUSINESS LOGIC (Orchestration)
    Router->>Service: service.process_request(user, data)
    activate Service
    Note right of Service: Validates input, checks permissions,<br/>and orchestrates the workflow.

    %% Optional: Fetching context/history (RAG or Chat History)
    Service->>Repo: repo.get_context(session_id, query)
    activate Repo
    Repo->>DB: SELECT history OR Vector Search (ChromaDB)
    activate DB
    DB-->>Repo: Context Chunks / History
    deactivate DB
    Repo-->>Service: Context Data
    deactivate Repo
    end

    rect rgb(230, 240, 255)
    Note right of Client: PHASE 3: AI ORCHESTRATION (The Brain)
    Service->>AI_Adapter: adapter.generate(prompt, context, model_config)
    activate AI_Adapter
    Note right of AI_Adapter: Translates internal request to<br/>provider-specific API format.

    alt Local Model (Ollama)
        AI_Adapter->>Ext_AI: POST http://localhost:11434/api/generate
    else External Model (OpenAI / Groq / Mistral)
        AI_Adapter->>Ext_AI: POST https://api.openai.com/v1/chat/completions<br/>(using API Key from .env)
    end
    activate Ext_AI
    Ext_AI-->>AI_Adapter: Streamed or Full AI Response
    deactivate Ext_AI
    AI_Adapter-->>Service: Standardized Parsed Response
    deactivate AI_Adapter
    end

    rect rgb(232, 245, 233)
    Note right of Client: PHASE 4: DATA PERSISTENCE (Storage)
    Service->>Repo: repo.save_interaction(session_id, user_msg, ai_msg)
    activate Repo
    Repo->>DB: INSERT INTO messages (role, content, session_id)
    activate DB
    DB-->>Repo: Success Confirmation
    deactivate DB
    Repo-->>Service: Saved Message Objects
    deactivate Repo

    Service-->>Router: Processed Result (Pydantic Model / Dict)
    deactivate Service
    end

    rect rgb(255, 243, 224)
    Note right of Client: PHASE 5: EGRESS (Response)
    Router-->>Client: HTTP 200 OK { JSON Response }
    deactivate Router
    end
```

### Target Architecture — Agentic Flow

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client (Frontend)
    participant GW as Gateway Layer<br/>(gateway/http/routers/ & gateway/realtime/)
    participant Deps as Dependencies<br/>(gateway/http/dependencies.py)
    participant Service as Domain Service<br/>(ai/agents/service.py)
    participant Tool as AI Tool<br/>(ai/tools/)
    participant Repo as Repository<br/>(data/repositories/)
    participant DB as Databases<br/>(PostgreSQL + ChromaDB)
    participant AI_Adapter as AI Provider Adapter<br/>(ai/providers/adapters/)
    participant Ext_AI as External AI<br/>(Ollama / OpenAI / Groq)

    Note over Client, Ext_AI: Complete Backend Flow

    rect rgb(255, 243, 224)
    Note right of Client: PHASE 1: GATEWAY LAYER (The Door)

    alt 🌐 Standard HTTP Request (REST)
        Client->>GW: HTTP Request (e.g., POST /api/v1/agents/run)
        GW->>Deps: Depends(require_user), Depends(get_db)
        Deps-->>GW: Authenticated User + DB Session
    else 🔌 Realtime WebSocket (Socket.IO)
        Client->>GW: WS Connect (/realtime/socket.io) + Emit Event
        GW->>Deps: Verify JWT from handshake payload
        Deps-->>GW: Authenticated User + DB Session
    end
    end

    rect rgb(243, 229, 245)
    Note right of Client: PHASE 2: CORE BUSINESS LOGIC (ai/agents/)
    GW->>Service: service.run_task(user, goal)
    activate Service
    Note right of Service: Validates goal, initializes Agent loop.<br/>Logic lives in: ai/agents/service.py

    Service->>Repo: repo.get_agent_memory(session_id)
    activate Repo
    Repo->>DB: SELECT past thoughts/actions
    activate DB
    DB-->>Repo: Memory Context
    deactivate DB
    Repo-->>Service: Past Steps
    deactivate Repo
    end

    rect rgb(230, 240, 255)
    Note right of Client: PHASE 3: AI ORCHESTRATION (ai/providers/ & ai/tools/)
    loop Max Iterations (e.g., 5 steps)
        Service->>AI_Adapter: adapter.generate(prompt, memory, tools)
        activate AI_Adapter
        Note right of AI_Adapter: Translates request to provider format.<br/>Logic lives in: ai/providers/adapters/

        alt Local Model (Ollama)
            AI_Adapter->>Ext_AI: POST http://localhost:11434/api/generate
        else External Model (OpenAI / Groq)
            AI_Adapter->>Ext_AI: POST https://api.openai.com/v1/chat/completions
        end
        activate Ext_AI
        Ext_AI-->>AI_Adapter: AI Decision (Tool Call OR Final Answer)
        deactivate Ext_AI
        AI_Adapter-->>Service: Parsed Decision
        deactivate AI_Adapter

        alt Decision is "Tool Call"
            Service->>Tool: tool.execute(action_input)
            activate Tool
            Note right of Tool: Executes action (e.g., web search).<br/>Logic lives in: ai/tools/
            Tool->>DB: Fetch external data / RAG
            activate DB
            DB-->>Tool: Raw Observation Data
            deactivate DB
            Tool-->>Service: Observation Result
            deactivate Tool

            Service->>Repo: repo.save_agent_step(thought, action, observation)
            activate Repo
            Repo->>DB: INSERT INTO agent_memory
            deactivate Repo
        else Decision is "Final Answer"
            Note right of Service: Loop breaks, proceed to Phase 4.
        end
    end
    end

    rect rgb(232, 245, 233)
    Note right of Client: PHASE 4: DATA PERSISTENCE (data/repositories/)
    Service->>Repo: repo.save_interaction(session_id, goal, final_answer)
    activate Repo
    Repo->>DB: INSERT INTO messages / tasks
    activate DB
    DB-->>Repo: Success Confirmation
    deactivate DB
    Repo-->>Service: Saved Objects
    deactivate Repo

    Service-->>GW: Processed Result (Pydantic Model / Dict)
    deactivate Service
    end

    rect rgb(255, 243, 224)
    Note right of Client: PHASE 5: EGRESS (Response)

    alt 🌐 HTTP Response
        GW-->>Client: HTTP 200 OK { JSON Response }
    else 🔌 Realtime WebSocket Response
        GW-->>Client: Emit Event (e.g., 'agent_task_completed', result)
    end
    end
```

---

## 🗂️ Project Structure

```
open-tutor-ai-CE/
├── main.py                    ← Python entry point (uvicorn)
│
├── ── Application Domains ───────────────────────────────────────────────
├── accounts/                  ← Auth, users, roles, permissions
├── learning/                  ← Learners, teachers, classrooms, courses
│   ├── sessions/              ← Chat sessions, tags, sharing, search
│   └── supports/              ← Personalized tutoring supports
├── ai/                        ← LLM, providers, RAG, media, memory, tools
│   ├── llm/                   ← LLM schemas, service, transports
│   ├── model_catalog/         ← Model overlays/catalog
│   ├── providers/             ← OpenAI-compatible + Ollama providers
│   ├── retrieval/             ← RAG pipeline and knowledge bases
│   └── media/                 ← Audio (TTS/STT) + image generation
├── content/                   ← Files, uploads, learning resources
│   ├── files/                 ← User-owned files and extracted content
│   └── resources/             ← Learning resources not tied to RAG
├── governance/                ← HITL governance and LLM response evaluation
│   └── self_regulation/       ← Self-regulation feedback domain
├── system/                    ← App-level configs and bootstrap services
│   ├── configs/               ← Runtime app configuration store
│   └── app/                   ← App info/bootstrap services
│
├── ── Gateway & Infrastructure ──────────────────────────────────────────
├── gateway/                   ← Transport layer
│   ├── http/                  ← FastAPI app, dependencies, routers/
│   └── realtime/              ← Socket.IO ASGI (/realtime/socket.io)
├── data/                      ← ORM models, DB engine, base repository
├── config/                    ← App settings & constants
├── common/                    ← Shared utilities (exceptions, logging)
├── tests/                     ← Pytest suite
│
├── ── Frontend ──────────────────────────────────────────────────────────
├── ui/                        ← SvelteKit application
│   ├── src/lib/apis/          ← API clients (one folder per domain)
│   ├── src/lib/components/    ← Reusable Svelte components
│   ├── src/lib/i18n/          ← Translations (AR / FR / EN)
│   ├── src/routes/            ← File-based routing
│   ├── static/                ← Assets (avatars, images, audio)
│   └── cypress/               ← E2E tests
│
├── ── DevOps ────────────────────────────────────────────────────────────
├── devops/
│   ├── docker/                ← Dockerfiles + Docker Compose overlays
│   └── scripts/               ← Dev & ops shell scripts
│
├── ── Project ───────────────────────────────────────────────────────────
├── docs/                      ← Documentation
├── kubernetes/                ← Helm charts
├── .github/workflows/         ← CI/CD
└── var/                       ← Runtime only, gitignored (DB, uploads, vector_db)
```

> Full structure with annotations: [MIGRATION.md](MIGRATION.md)

OpenWebUI and Hermes are used as design references only. OpenTutorAI keeps its own
domain names and has no runtime dependency on either project.

---

## How to Install 🚀

Below is a list of essential steps and resources to help you get started, manage, and develop with Open TutorAI.

### 🛠️ Setup Guide — Local Development (without Docker)

Use this path when you want hot-reload for active development or contribution.

**Requirements:** Python 3.11–3.12 · Node.js 18.13–22.x

1. **Fork and Clone the Repository**
   - Go to [GitHub Repository](https://github.com/Open-TutorAi/open-tutor-ai-CE)
   - Click on **Fork**, then clone your forked repo:
     ```bash
     git clone https://github.com/YOUR_USERNAME/open-tutor-ai-CE.git
     cd open-tutor-ai-CE
     ```

2. **Python Application Setup**
   - Create and activate a Python environment (conda or venv):

     ```bash
     # conda
     conda create -n tutorai-env python=3.11
     conda activate tutorai-env

     # or plain venv
     python3 -m venv .venv && source .venv/bin/activate
     ```

   - Install the required packages:
     ```bash
     pip install -r requirements.txt
     ```
   - Copy and configure environment variables:
     ```bash
     cp .env.example .env
     # The defaults in .env.example work for local dev (DEBUG=true).
     # No changes needed unless you use an external API or want production mode.
     ```
   - Start the Python API with hot-reload (available at **http://localhost:8080**):
     ```bash
     uvicorn main:app --reload --port 8080
     ```
     Or use the provided convenience script:
     ```bash
     chmod +x devops/scripts/dev.sh && ./devops/scripts/dev.sh
     ```
   - Interactive API docs: **http://localhost:8080/docs**

3. **Frontend Setup** _(in a second terminal)_
   - Navigate to the `ui/` folder:
     ```bash
     cd ui
     npm install
     npm run dev        # dev server with hot-reload at http://localhost:5173
     ```

4. **Ollama _(optional — for local models)_**
   - Install from [ollama.com](https://ollama.com), then:
     ```bash
     ollama pull llama3.2
     ```
   - Verify `OLLAMA_BASE_URL=http://localhost:11434` is set in your `.env`.

5. **First login**
   - Open **http://localhost:5173** and create an account.
   - The **first account registered becomes the administrator**.

6. **Run tests** _(no external services required)_
   ```bash
   pytest -q
   ```

---

### 🐳 Docker & Docker Compose Setup (Recommended)

For a hassle-free setup without installing Python or Node.js, use Docker. A single container serves both the Python API and the built frontend.

#### Prerequisites

1. **Docker + Docker Compose** from [docker.com](https://www.docker.com/get-started)
2. **Git** for cloning
3. **At least 8 GB RAM** recommended for AI models

#### Step 1: Clone the Repository

```bash
git clone https://github.com/Open-TutorAi/open-tutor-ai-CE.git
cd open-tutor-ai-CE
```

#### Step 2: Set Up Environment Variables

```bash
cp .env.example .env
```

For **production**, replace the placeholder `SECRET_KEY` in your `.env` with a randomly generated value:

```bash
# macOS / Linux — replaces the existing SECRET_KEY line in-place
sed -i.bak "s/^SECRET_KEY=.*/SECRET_KEY=$(openssl rand -hex 32)/" .env && rm .env.bak
```

For **local development**, the defaults in `.env.example` work as-is (`DEBUG=true` bypasses the key check).

#### Step 3: Start the Stack

**With Ollama bundled (recommended for local models):**

```bash
docker compose --env-file .env -f devops/docker/docker-compose.yaml up --build
```

This starts:

- `open-tutorai` — Python API + frontend at **http://localhost:8080**
- `ollama` — local model server at **http://localhost:11434**

**Without Ollama (use an external OpenAI-compatible API):**

```bash
docker compose --env-file .env -f devops/docker/docker-compose.yaml up --build open-tutorai
```

Set `OPENAI_API_BASE_URL` and `OPENAI_API_KEY` in `.env`.

Then in another terminal, you can also start Ollama separately:

```bash
chmod +x devops/scripts/run-ollama-docker.sh
./devops/scripts/run-ollama-docker.sh
```

#### Step 4: Download AI Models (if using Ollama)

```bash
docker exec -it ollama ollama pull llama3.2
```

Verify the model is installed:

```bash
docker exec -it ollama ollama list
```

If the Python API was already running before the model was pulled, restart it:

```bash
docker compose --env-file .env -f devops/docker/docker-compose.yaml restart open-tutorai
```

#### Step 5: Access the Application

Open **http://localhost:8080** in your browser. The **first account created becomes the administrator**.

#### Stopping the Services

```bash
docker compose --env-file .env -f devops/docker/docker-compose.yaml down

# Full reset (removes all data volumes)
docker compose --env-file .env -f devops/docker/docker-compose.yaml down -v
```

#### GPU Support

```bash
# NVIDIA GPU
docker compose --env-file .env -f devops/docker/docker-compose.yaml -f devops/docker/docker-compose.gpu.yaml up --build

# AMD GPU
docker compose --env-file .env -f devops/docker/docker-compose.yaml -f devops/docker/docker-compose.amdgpu.yaml up --build
```

---

### ⚙️ Environment Variables Reference

| Variable              | Default                                       | Description                                                                       |
| --------------------- | --------------------------------------------- | --------------------------------------------------------------------------------- |
| `DEBUG`               | `true`                                        | Set to `false` in production. Enables SECRET_KEY strength check.                  |
| `SECRET_KEY`          | _(dev placeholder)_                           | JWT signing key. Required in production (`openssl rand -hex 32`).                 |
| `DATABASE_URL`        | `sqlite:///./var/tutorai.db`                  | SQLAlchemy URL. SQLite for dev, PostgreSQL for production.                        |
| `OLLAMA_BASE_URL`     | `http://localhost:11434`                      | Ollama server. Use `http://ollama:11434` inside Docker Compose.                   |
| `OPENAI_API_BASE_URL` | _(empty)_                                     | OpenAI-compatible API (LMStudio, GroqCloud, Mistral…).                            |
| `OPENAI_API_KEY`      | _(empty)_                                     | API key for the OpenAI-compatible provider.                                       |
| `GEMINI_API_KEY`      | _(empty)_                                     | Google Gemini API key.                                                            |
| `CORS_ALLOW_ORIGIN`   | `http://localhost:3000,http://localhost:5173` | Comma-separated allowed CORS origins.                                             |
| `UPLOAD_DIR`          | `./var/uploads`                               | Directory for uploaded files.                                                     |
| `MAX_UPLOAD_SIZE_MB`  | `100`                                         | Maximum upload size in MB.                                                        |
| `VECTOR_DB_PATH`      | `./var/vector_db`                             | ChromaDB storage path for RAG.                                                    |
| `EMBEDDING_MODEL`     | `sentence-transformers/all-MiniLM-L6-v2`      | Default embedding model for RAG.                                                  |
| `AUDIO_TTS_ENGINE`    | _(empty)_                                     | TTS engine (e.g. `openai`). Configure via Admin > Settings > Audio.               |
| `AUDIO_STT_ENGINE`    | _(empty)_                                     | STT engine. Configure via Admin > Settings > Audio.                               |
| `IMAGES_ENGINE`       | _(empty)_                                     | Image generation engine (e.g. `openai`). Configure via Admin > Settings > Images. |
| `GLOBAL_LOG_LEVEL`    | `INFO`                                        | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`.                                   |

---

### Troubleshooting

Encountering connection issues? See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common fixes, or visit our [Open TutorAI Documentation](https://opentutorai.com/docs/troubleshooting/). For further assistance, join the [Open TutorAI Discord](https://discord.gg/BTQtE2deEm).

## 🌟 What's Next?

Discover upcoming features on our roadmap in the [Open TutorAI Documentation](https://opentutorai.com/docs/roadmap).

## 📜 License

This project is licensed under the [BSD-3-Clause License](LICENSE) - see the [LICENSE](LICENSE) file for details. 📄

## 💬 Support

If you have any questions, suggestions, or need assistance, please open an issue or join our
[Open TutorAI Discord community](https://discord.gg/BTQtE2deEm) to connect with us! 🤝

## Star History

<a href="https://www.star-history.com/#Open-TutorAi/open-tutor-ai-CE&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Open-TutorAi/open-tutor-ai-CE&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Open-TutorAi/open-tutor-ai-CE&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Open-TutorAi/open-tutor-ai-CE&type=Date" />
 </picture>
</a>

---

Founded by [Mohamed El Hajji](https://github.com/pr-elhajji) and built by the community - Let's make Open TutorAI even more amazing together! 💪
