# Teacher Section — Security

This document records the security controls applied across the teacher-section backend
(`classrooms`, `assignments`, `exams`, `resources`, `messaging`, `guardians`) and how they map to
the project's security requirements (OWASP-aligned: access control, input validation, safe
uploads, security headers, rate limiting).

## Scope

Every teacher-domain endpoint is HTTP-thin: it authenticates the caller, delegates to a service,
and maps domain errors to HTTP status codes. Authorization, validation and data access live in the
service/repository layers, so the rules below are enforced in one place per concern rather than
scattered across routers.

## Controls

### 1. Authentication & authorization (anti-IDOR)
- Endpoints require a valid bearer token (`require_teacher` / `get_current_user`).
- **Being authenticated is never treated as being authorized.** After loading a resource, the
  service verifies the caller's relationship to it:
  - teachers act only on classes they own (`_owned`, `_owned_class`, `_owned_assignment`);
  - students act only within classes they're enrolled in (enrolment checks);
  - a user reads only their own state (e.g. `GET /me/monitor`).
- Violations raise `AuthorizationError` → **403**; missing resources raise `NotFoundError` →
  **404**. The two are kept distinct.
- Identifiers are opaque **UUIDv4** — no sequential IDs in URLs.

### 2. Input validation
- Request models use Pydantic `Field` constraints (min/max length, numeric range) on every field —
  e.g. `grade` is bounded `ge=0, le=1000`, `title ≤ 255`, `feedback ≤ 2000`, exam
  `max_violations ≤ 3`, classroom `capacity ≥ 1`.
- Email fields use `EmailStr`.
- These bounds are defence-in-depth; services still enforce semantic rules (non-blank, date
  ranges, policy caps). Both layers reject with **422** consistently.

### 3. File uploads
- Server-side **MIME allowlist** (`config.settings.ALLOWED_MATERIAL_MIME`, with `image/*` and
  `text/*` prefixes) — anything else (executables, scripts, unknown types) is refused with **415**
  before any bytes are stored. The list is env-tunable.
- A streamed **size cap** (`MAX_UPLOAD_SIZE_MB`) rejects oversize uploads with **413**.
- Assignment/message attachments are referenced by an already-uploaded **file id** owned by the
  uploader (`files.require_owned`) — not by a client-supplied URL, so there is no SSRF surface.

### 4. Pagination
- A shared `Pagination` dependency (`gateway/http/dependencies.py`) adds `limit`/`offset` query
  params to every list endpoint, **hard-capped at 100** items per page, bounding response size.
  Endpoints that return an envelope object (not a bare list) are intentionally excluded.

### 5. Security response headers
A middleware (`gateway/http/app.py`) sets, on every response:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: frame-ancestors 'none'; object-src 'none'; base-uri 'self'`

The CSP is deliberately limited to directives that harden without breaking the SvelteKit app's
inline runtime (it does not restrict `script-src`/`style-src`).

### 6. Rate limiting
- `gateway/http/rate_limit.py` provides a dependency-free **sliding-window limiter** applied to
  sensitive mutating routes (`/signin`, `/signup`, `/submit`, `/grade`) at **10 requests / minute**
  per caller (bearer token, falling back to client IP), returning **429** with `Retry-After`.
- It is wired only when `DEBUG=false` (production), so it never throttles local development or the
  test suite. The limiter's counting logic is unit-tested (`tests/test_rate_limit.py`).
- The store is in-memory and per-process; a shared store (e.g. Redis) is the next step for a
  multi-node deployment.

### 7. Data access & secrets
- SQLAlchemy ORM is used exclusively — no string-concatenated SQL.
- Error responses are generic; internal details are not surfaced to the client.
- Secrets (JWT key, provider keys) come from environment/settings — never hardcoded.

## Known limitation

- **Session tokens are kept in `localStorage`** (inherited from the base platform), not in
  HttpOnly+Secure cookies. Moving to cookie-based sessions — and the CSRF double-submit protection
  that becomes relevant once cookies carry credentials — is a **platform-wide auth change** that
  touches login, the realtime handshake, and every client API call. It is tracked separately from
  the teacher section to avoid destabilising authentication app-wide.

## Verification

The full backend suite (`pytest`) is green, including the upload-MIME rejection test
(`tests/test_resources.py`) and the rate-limiter unit tests (`tests/test_rate_limit.py`). The app
boots cleanly in both `DEBUG=true` (limiter off) and `DEBUG=false` (limiter wired).
