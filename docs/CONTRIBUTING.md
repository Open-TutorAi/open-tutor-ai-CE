# Contributing to Open TutorAI 🌟

🚀 **Welcome, Contributors!** 🚀

Your interest in contributing to Open TutorAI is greatly appreciated. This document is here to guide you through the process, ensuring your contributions enhance the project effectively. Let's make Open TutorAI even better, together!

### 🚨 Reporting Issues

Noticed something off? Have an idea? Check our [Issues tab](https://github.com/Open-TutorAi/open-tutor-ai-CE/issues) to see if it's already been reported or suggested. If not, feel free to open a new issue. When reporting an issue, please follow our issue templates. These templates are designed to ensure that all necessary details are provided from the start, enabling us to address your concerns more efficiently.

> [!IMPORTANT]
>
> - **Template Compliance:** Please be aware that failure to follow the provided issue template, or not providing the requested information at all, will likely result in your issue being closed without further consideration. This approach is critical for maintaining the manageability and integrity of issue tracking.
> - **Detail is Key:** To ensure your issue is understood and can be effectively addressed, it's imperative to include comprehensive details. Descriptions should be clear, including steps to reproduce, expected outcomes, and actual results. Lack of sufficient detail may hinder our ability to resolve your issue.

### 🧭 Scope of Support

We've noticed an uptick in issues not directly related to Open TutorAI but rather to the environment it's run in, especially Docker setups. While we strive to support Docker deployment, understanding Docker fundamentals is crucial for a smooth experience.

- **Docker Deployment Support**: Open TutorAI supports Docker deployment. Familiarity with Docker is assumed. For Docker basics, please refer to the [official Docker documentation](https://docs.docker.com/get-started/overview/).

- **Advanced Configurations**: Setting up reverse proxies for HTTPS and managing Docker deployments requires foundational knowledge. There are numerous online resources available to learn these skills. Ensuring you have this knowledge will greatly enhance your experience with Open TutorAI and similar projects.

## 💡 Contributing

Looking to contribute? Great! Here's how you can help:

### ⚙️ Local Setup (required before contributing)

Before submitting a pull request, set up your local environment so your code is validated automatically.

**1. Install the development dependencies**

```bash
pip install pre-commit
```

**2. Install the git hooks**

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

The hooks run automatically on every `git commit`. They check:

- Python lint and formatting (Ruff)
- Frontend formatting (Prettier — JS/TS/Svelte)
- Frontend lint (ESLint) and i18n keys
- Trailing whitespace and missing end-of-file newlines
- Conventional Commits message format (`feat:`, `fix:`, `chore:`, …)

**3. Validate before pushing**

```bash
make check
```

This command runs `make lint` (pre-commit on all files) then `make test` (pytest + vitest). **A push that has not passed `make check` will be rejected by CI.**

#### Available Make targets

| Target | Action |
| ------------------- | ------------------------------------------------------------ |
| `make lint` | Runs pre-commit on all files (Ruff, Prettier, ESLint, i18n) |
| `make test` | Backend tests (pytest) + frontend tests (vitest) |
| `make check` | `lint` + `test` — the full validation before pushing |
| `make install` | Starts the Docker Compose stack |
| `make start` / `make stop` | Starts / stops existing containers |
| `make startAndBuild` | Rebuilds the images then starts |
| `make update` | `git pull` + rebuild + restart of the stack |

> ⚠️ Bare `make` runs `install` (the first target in the Makefile) and starts Docker Compose. For local validation, always use an explicit target: `make check`.

---

### 🔄 Feature Development Workflow (required)

Every new feature follows this workflow — it guarantees code quality and speeds up PR validation:

```
Documented issue → Architecture check → TDD → Implementation → Documentation → PR
```

**1. Issue first — no PR without an issue**

Open a [feature request](https://github.com/Open-TutorAi/open-tutor-ai-CE/issues/new/choose) that fills in the **Architecture** section of the template: domain boundary, API contract, test plan, documentation impact. A feature PR without a prior issue will not be reviewed.

**2. OpenWebUI-first for the frontend**

The `ui/` frontend is based on **OpenWebUI**. Before introducing a new UI pattern:

- Check whether OpenWebUI already implements this feature or a similar pattern — align with it
- Reuse existing components (`ui/src/lib/components/common`, `chat`, `admin`, `workspace`, `student`)
- **Never import from `open_webui` at runtime** — it is a read-only design reference

**3. DDD architecture for the backend**

- Pick the owning domain boundary before writing code: `accounts`, `learning`, `ai`, `content`, `governance`, or `system`
- Follow the layered pattern: `repository.py` (data access) → `service.py` (business logic) → `gateway/http/routers/` (HTTP only)
- No ORM in routers, no business logic in repositories

**4. TDD — tests go with the code**

- Write tests with (not after) the implementation: success, auth/ownership, missing resource, validation
- Every UI `fetch()` must have a backend route — the contract test (`tests/test_contract_coverage.py`) enforces this in CI

**5. Documentation**

- Update `AGENTS.md` whenever architecture, conventions, or domain rules change
- Update the i18n locales (AR/FR/EN) for any user-visible text

**6. Final validation**

```bash
make check   # lint + tests — required before pushing
```

---

### 🛠 Pull Requests

We welcome pull requests. Before submitting one, please:

1. Open a documented issue first (see the feature workflow above), or a discussion [here](https://github.com/Open-TutorAi/open-tutor-ai-CE/discussions/new/choose).
2. Follow the project's coding standards and include tests for new features.
3. Update documentation as necessary.
4. Write clear, descriptive commit messages.
5. It's essential to complete your pull request in a timely manner. We move fast, and having PRs hang around too long is not feasible. If you can't get it done within a reasonable time frame, we may have to close it to keep the project moving forward.

#### 📁 Project Structure Guidelines

The project uses a **root-driven architecture** since v1.0. Keep this layout in mind when adding new files:

**Python application — project root**

- Use the approved root packages: `accounts/`, `learning/`, `ai/`, `content/`, `governance/`, `system/`, `gateway/`, `data/`, `common/`, and `config/`
- Domain code follows the pattern: `repository.py` → `service.py` → `gateway/http/routers/<public_namespace>.py`
- Keep RAG knowledge bases under `ai/retrieval/knowledge/`, not under `content/`
- Keep AI audio/image capabilities under `ai/media/`, not as a root `media/` package
- New routes must be registered in `gateway/http/app.py` and covered by `tests/test_contract_coverage.py`

**Frontend (SvelteKit — `ui/` subdirectory)**

- ✅ Reusable or shared components go inside `ui/src/lib/components/`
  - Organize by feature or domain (e.g., `components/tutor/`, `components/dashboard/`)
- ✅ Route-specific pages go inside `ui/src/routes/`
- ✅ API client functions go inside `ui/src/lib/apis/<domain>/index.ts`
- ❌ Avoid placing components outside their designated folders

> **Tip:** Every new `fetch()` call in `ui/src/lib/apis/` must have a matching API endpoint — the contract test will catch the gap in CI.

### 📚 Documentation & Tutorials

Help us make Open TutorAI more accessible by improving documentation, writing tutorials, or creating guides on setting up and optimizing the Tutor AI.

### 🌐 Translations and Internationalization

Help us make Open Tutor AI available to a wider audience. In this section, we'll guide you through the process of adding new translations to the project.

We use JSON files to store translations. You can find the existing translation files in the `ui/src/lib/i18n/locales` directory. Each directory corresponds to a specific language, for example, `en-US` for English (US), `fr-FR` for French (France) and so on. You can refer to [ISO 639 Language Codes](http://www.lingoes.net/en/translator/langcode.htm) to find the appropriate code for a specific language.

To add a new language:

- Create a new directory in the `ui/src/lib/i18n/locales` path with the appropriate language code as its name. For instance, if you're adding translations for Spanish (Spain), create a new directory named `es-ES`.
- Copy the American English translation file(s) (from `en-US` directory in `src/lib/i18n/locale`) to this new directory and update the string values in JSON format according to your language. Make sure to preserve the structure of the JSON object.
- Add the language code and its respective title to languages file at `src/lib/i18n/locales/languages.json`.

### 🤔 Questions & Feedback

Got questions or feedback? Join our [Discord community](https://discord.gg/BTQtE2deEm) or open an issue. We're here to help!

## 🙏 Thank You!

Your contributions, big or small, make a significant impact on Open Tutor AI. We're excited to see what you bring to the project!

Together, let's create an even more powerful tool for the community. 🌟
