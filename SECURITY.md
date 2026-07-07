# Security Policy

## Supported Versions

Only the latest release and the current `main` branches receive security fixes.

| Version | Supported |
| ------------------ | --------- |
| Latest release | ✅ |
| `main` | ✅ |
| Older releases | ❌ |

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Report privately via GitHub: **Security tab → Report a vulnerability** on
[Open-TutorAi/open-tutor-ai-CE](https://github.com/Open-TutorAi/open-tutor-ai-CE/security/advisories/new).

Include:

- A description of the vulnerability and its impact
- Steps to reproduce (a minimal proof of concept helps)
- Affected version, branch, or commit
- Any suggested fix, if you have one

## What to Expect

- **Acknowledgement** within 7 days.
- **Assessment and triage** within 14 days — we confirm the issue, assess severity, and agree on a disclosure timeline with you.
- **Fix and disclosure**: we patch supported versions, publish a GitHub Security Advisory, and credit the reporter (unless you prefer to stay anonymous).

## Scope

In scope:

- The FastAPI backend (auth, JWT handling, ownership checks, file uploads, API routes)
- The SvelteKit frontend (`ui/`)
- Realtime Socket.IO gateway (`/realtime`)
- Docker/Compose assets under `devops/`

Out of scope:

- Vulnerabilities in third-party dependencies already publicly known (report upstream; our weekly OSV scan tracks these)
- Issues requiring a misconfigured deployment (e.g. `DEBUG=true` or a default `SECRET_KEY` in production — both are documented as dev-only)
- Social engineering or physical attacks

## Hardening Notes for Deployers

- Always set a strong `SECRET_KEY` and `DEBUG=false` in production.
- Restrict `CORS_ALLOW_ORIGIN` to your actual origins — never `*` in production.
- Never commit `.env` files, API keys, or user data.
