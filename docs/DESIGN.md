# Design

A lead-management application for an immigration law practice. Prospects submit a public form
(name, email, resume); the system persists the lead, emails both the prospect and an attorney, and
gives attorneys an authenticated internal queue to work each lead from `PENDING` to `REACHED_OUT`.

The guiding principle throughout: **one source of truth for every rule.** The FastAPI backend owns
persistence, validation, the state machine, authentication, and email. The Next.js frontend is
presentation — it renders and calls the API, and never re-implements a business rule. Every
decision below follows from that seam, and each is written with its trade-off and its production
path made explicit, because the interesting part of a system isn't that it works — it's
knowing exactly where it stops working and what you'd do next.

---

## 1. Architecture

```
Browser
  │  http://localhost:3000  (single origin — the auth cookie needs no CORS ceremony)
  ▼
Next.js 16 · App Router (frontend/)                 FastAPI (backend/)
  ├─ /              public lead form         ┌────► POST /api/leads            create (public)
  ├─ /login         attorney sign-in         │      GET  /api/leads            list  (auth)
  ├─ /admin/leads   internal lead queue      │      PATCH /api/leads/{id}      transition (auth)
  │                                          │      GET  /api/leads/{id}/resume download (auth)
  └─ rewrite: /api/:path*  ──────────────────┤      POST /api/auth/login|logout, GET /api/auth/me
     (proxied to FastAPI, same origin)       │      GET  /api/health
                                             │              │              │
   Server Components fetch server-side,      ▼              ▼              ▼
   forwarding the alma_session cookie   SQLite +        Email service   Structured logs
   directly to BACKEND_URL.             uploads/ on     (Resend API, or  (+ request IDs)
                                        disk            console fallback)
```

Two design choices define the whole system:

- **Single origin.** The Next.js `rewrite` proxies `/api/*` to FastAPI, so the browser only ever
  talks to `localhost:3000`. The `alma_session` cookie is first-party — no CORS negotiation, no
  `SameSite=None`, no third-party-cookie fragility. Server Components bypass the rewrite and call
  `BACKEND_URL` directly, forwarding the cookie header themselves (`cache: "no-store"`).
- **The API is the contract.** A fixed request/response contract was written up front (it's
  literally the Pydantic schema layer). The frontend consumes it through one typed client
  (`src/lib/api.ts`); no page constructs requests ad hoc, and no validation rule is duplicated
  client-side except as a fast-feedback convenience that the server re-checks.

### Repo layout

| Path                 | What                                                                              |
| -------------------- | --------------------------------------------------------------------------------- |
| `frontend/`          | Next.js 16 App Router (React 19, Tailwind v4, shadcn/ui on Base UI, Vitest, Playwright) |
| `backend/`           | FastAPI (SQLAlchemy 2, Alembic, pytest, ruff, pyright), managed with `uv`         |
| `docs/`              | This design doc + the coding-agent usage writeup                                  |
| `docker-compose.yml` | One-command full-stack run; per-app Dockerfiles in `frontend/` and `backend/`     |
| `justfile`           | `install` / `frontend` / `backend` / `seed` / `verify` / `e2e` recipes           |
| `.github/workflows/` | CI (frontend · backend · e2e), CodeQL, OpenSSF Scorecard                          |

**Two apps, one repo.** They ship together, share one issue tracker and one CI pipeline, and a
single `just verify` gates both. At larger scale — separate deploy cadences or teams — they'd split
into workspace-managed packages or separate repos; the `frontend/` + `backend/` boundary is already
the fault line.

---

## 2. Backend structure — thin routers, service-owned logic

The app is assembled by a `create_app()` factory (`app/main.py`). Routers stay thin: they parse and
shape HTTP, then delegate to `app/services/`, where the actual logic lives. Cross-cutting concerns
are middleware, and everything reaches its collaborators through FastAPI's dependency injection
(`app/api/deps.py`), which is also the seam the tests use to swap in fakes.

**Middleware stack (order matters — outermost first):**

| Layer                      | Responsibility                                                                    |
| -------------------------- | --------------------------------------------------------------------------------- |
| `RequestContextMiddleware` | Assigns/echoes an `X-Request-ID`, logs one line per request (method/path/status/duration) |
| `CORSMiddleware`           | Locked to `FRONTEND_ORIGIN` with credentials allowed                              |
| `SecurityHeadersMiddleware`| Base headers everywhere; a strict `default-src 'none'` CSP on the `/api` surface  |
| `MaxBodySizeMiddleware`    | Rejects over-large bodies with `413` *before* they're parsed or buffered          |

**Request correlation.** Every request gets a UUID (or reuses an inbound `X-Request-ID`), stored in
a `ContextVar` so it surfaces on every log line within that request and is echoed back in the
response header — the groundwork for tracing across services. Logging is switchable between a
readable console format (dev) and single-line JSON (prod) via `LOG_FORMAT`, and structured
`extra=` fields flow through both.

---

## 3. Data model & persistence

### SQLite + SQLAlchemy 2 + Alembic

- **Why SQLite:** the primary run target is "clone → run, no external services." SQLite is
  zero-setup — no Docker, no daemon — yet fully relational and honest for this data shape and volume.
- **Why a real ORM + migrations anyway:** the SQLAlchemy 2 models (`Mapped[]` / `mapped_column`),
  session handling, and Alembic migrations are exactly what a Postgres deployment uses. Swapping to
  Postgres is a `DATABASE_URL` change plus a driver — not a rewrite. The engine layer already
  branches on backend (`check_same_thread=False` is applied only for SQLite, so sessions are safe
  across FastAPI's threadpool workers).
- **Trade-off:** SQLite's single-writer model caps write concurrency. Correct for a single-node
  intake app; wrong for a multi-instance deployment. The swap path is deliberate, not accidental.

### The `Lead` model

A UUID string primary key (unguessable, no enumeration), a `LeadState` string-enum, an indexed
`email` column (the dedupe and lookup path), timestamps that are timezone-aware with an `onupdate`
hook, and — importantly — **two** resume columns: `resume_stored_name` (the opaque UUID on disk)
and `resume_original_name` (what the user called it). The public API only ever exposes the latter,
through a `resume_filename` property, so the storage layout never leaks.

### One cross-cutting subtlety: UTC everywhere

SQLite returns *naive* datetimes even for `TIMESTAMP` columns. Rather than let that ambiguity leak,
timestamps are normalized to UTC at every boundary that renders them — the API serializer emits an
explicit `Z` suffix, the attorney email formats an explicit `UTC` label, and the frontend's
`parseUtcDate` re-appends `Z` if the backend omitted it (otherwise `new Date()` would silently parse
as browser-local time). It's a small thing that's wrong in a lot of production systems.

---

## 4. The API contract & input validation

Pydantic v2 schemas (`app/schemas.py`) *are* the contract. Beyond the obvious `EmailStr` and
length bounds, two decisions are worth calling out:

- **Control-character stripping on names.** A `before` validator strips C0/C7 control characters
  (including CR/LF) from names, then trims. A name that was *only* control characters collapses to
  `""` and fails `min_length` — so a hostile name can neither forge a multi-line email `Subject`
  header nor inject into a log line. This is defense the framework won't do for you.
- **One 422 shape for the whole endpoint.** `POST /api/leads` is multipart, so its fields are parsed
  manually rather than as a single Pydantic body. The handler validates them through `LeadCreate`
  and *re-raises* any failure as a `RequestValidationError`, and resume validation errors are
  emitted in the same field-scoped shape (`loc: ["body", "resume"]`). The result: every 422 from the
  endpoint has one contract, and the frontend maps all of them back to the right field with one
  function (`fieldErrorsFromDetail`).

---

## 5. Key domain decisions

### Lead state machine — `PENDING → REACHED_OUT`, enforced server-side

The enum lives in the model; the transition rule lives in the service. Re-asserting the current
state is an **idempotent 200** (so a double-click or a retry is safe); any other transition is a
**409** with a descriptive message. Adding states later (`DISQUALIFIED`, `RETAINED`, …) means
extending one transition check — and the 409 contract already tells clients what happened.

### Idempotent public intake (and an honest race)

The public form is an abuse and double-submit magnet, so a repeat submission with the same email
inside a short window (`LEAD_DEDUPE_WINDOW_SECONDS`, default 60s) returns the *original* lead — no
second file stored, no duplicate emails. The trade-offs are documented in the code rather than
hidden:

- It's **check-then-create, not atomic**, with no unique constraint behind it. Two genuinely
  concurrent identical submits could both pass — though SQLite's single writer makes that unlikely.
- A **deliberate** re-submit within the window (e.g. fixing a wrong resume) returns the original and
  silently drops the new file.

Both are acceptable at intake volume; the production fix is a unique constraint or an idempotency
key, and it's named as such. (Calling out a known TOCTOU is the point — it's the difference between
a bug and a decision.)

### Email — Resend with a zero-config console fallback

`EmailService` is a two-line `Protocol` with two implementations: `ResendEmailService` (real
delivery) and `ConsoleEmailService` (logs the full message). A factory picks by whether
`RESEND_API_KEY` is set, so **a reviewer runs the app with zero external accounts** and still sees
both emails in the backend logs. Two further decisions:

- Sending happens in FastAPI `BackgroundTasks` *after* the lead is persisted, and a send failure is
  **logged but never fails the request** — losing a lead because a mail provider hiccuped is the
  worst possible outcome.
- Consequence, stated plainly: delivery is best-effort, no retry. Production becomes a
  transactional-outbox table drained by a worker (retries, idempotency, provider failover).

### Resume storage — local disk behind an interface

Files are validated (extension allowlist `.pdf/.doc/.docx`, 5 MB cap, over-long filenames rejected),
**streamed** to disk in 1 MB chunks rather than read into memory, and stored under a generated
`uuid4` name — **never** the user-supplied filename, which neutralizes path traversal and
collisions. The cap is enforced mid-stream (a file that grows past 5 MB is abandoned and the partial
deleted), empty files are rejected, and if the subsequent DB insert fails the just-written file is
cleaned up so no orphan is left behind. Downloads restore the original filename through an
authenticated endpoint. The storage service is the **S3 seam**: in production this becomes object
storage with presigned URLs, with the DB holding only keys and metadata.

---

## 6. Authentication & sessions

One attorney user is seeded from the environment (`ADMIN_EMAIL` / `ADMIN_PASSWORD`). Login verifies
credentials in **constant time** (`secrets.compare_digest`, with a bitwise `&` so neither the email
nor password comparison short-circuits and leaks timing) and returns an HS256 JWT in an `alma_session`
cookie that is **`httpOnly`** (no token in JS), `SameSite=Lax`, with an 8-hour TTL. Every guarded
endpoint re-validates it; the frontend's route guard only redirects for UX. **The backend is the
enforcement point — UI guards are convenience, not security.**

Three details that signal production-mindedness:

- **No usable signing key is ever committed.** When `SECRET_KEY` is unset, the app generates a
  strong ephemeral key *per process* — so repository contents can't forge a session — and a
  validator **rejects** any explicitly-configured key that is a known placeholder or under 32 chars,
  failing fast at startup. (An earlier draft shipped a constant `dev-secret-change-me`; that was
  caught in review and removed — see the agent-usage writeup.)
- **The token decoder is a total function.** `decode_access_token` returns `None` for anything
  invalid, expired, or not even UTF-8-encodable (a lone surrogate arriving as a JSON `\uXXXX`
  escape) — a crafted cookie yields a clean 401, never a 500.
- **Why not NextAuth / Clerk / Auth0:** they place identity in the frontend layer or an external
  service, while the brief centers the API in FastAPI. An env-seeded user also keeps the app
  runnable by a reviewer with no third-party signup. Production path: a users table with argon2
  hashes, short-lived access + refresh rotation, RBAC once roles appear, and likely SSO for a firm.

---

## 7. Security posture

Security was treated as a first-class feature within the timebox, with the cuts named rather than
quietly omitted.

**In scope, and implemented:**

| Area              | Control                                                                              |
| ----------------- | ------------------------------------------------------------------------------------ |
| Input             | Server-side validation of every public field; control-character stripping on names   |
| Uploads           | Extension allowlist, 5 MB streamed cap, empty-file rejection, UUID filenames, orphan cleanup |
| AuthN             | `httpOnly` `SameSite=Lax` cookie, constant-time compare, ephemeral/validated signing key |
| AuthZ             | Enforced at the API on every guarded route (UI guards are UX only)                   |
| Transport headers | HSTS, `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`    |
| CSP               | `default-src 'none'` on the API/download surface; a scoped document CSP on the frontend |
| Abuse             | Coarse 10 MB request-body cap (`413`) ahead of parsing; idempotent public submission |

One subtle frontend decision worth noting: the security headers are applied to top-level **document**
responses only (via a `missing: [{ header: "RSC" }]` match), because setting `nosniff` on a React
Server Component navigation payload (`text/x-component`) aborts client-side navigation and
`router.refresh()`. Documents are what a scanner checks anyway.

**Deliberately cut for the timebox — first in line for production:** rate limiting and CAPTCHA on
the public form, content-type/magic-byte validation and virus scanning of uploads (extension checks
only today), the `Secure` cookie flag behind TLS, audit logging of state changes, and a PII
retention policy.

---

## 8. Frontend architecture

- **Server Components by default** (Next 16 App Router, React 19). `"use client"` is added only for
  interactivity — the lead form, login form, and the two mutation buttons. Data is fetched on the
  server; mutations go to the FastAPI `/api/*` routes. The app deliberately uses **no Server
  Actions** — every write crosses the same API boundary, so there's exactly one place rules live.
- **`src/proxy.ts`** (Next 16's renamed middleware) bounces cookie-less visitors off `/admin/*`
  before render — a UX guard in front of the real backend enforcement.
- **One typed API client** (`src/lib/api.ts`) with discriminated-union results
  (`CreateLeadResult`, `MarkReachedOutResult`) so callers handle `ok` / field errors / auth-expiry /
  conflict explicitly rather than juggling raw status codes. Browser calls hit same-origin `/api/*`;
  server helpers hit `BACKEND_URL` and take a forwarded cookie.
- **Resilient UX states:** a `401` on "mark reached out" routes to `/login` instead of looping on a
  dead 8-hour session; a `409` tells the attorney the row moved under them; a down backend on the
  login page renders the form rather than crashing to the framework error page; and there are
  App-Router `error` / `not-found` / `loading` boundaries.
- **Accessible, tokenized UI:** shadcn/ui on Base UI with Tailwind v4 theme tokens (no ad-hoc hex),
  forms wired with `aria-invalid` / `aria-describedby` and inline `FieldError`s, and the queue's
  filter tabs and pagination marked up as real navigation.
- **`output: "standalone"`** so the production Docker image is a minimal self-contained Node server.

---

## 9. Delivery & operations

- **`justfile`** is the single task runner: `install` (deps + first-run `.env`), `frontend`,
  `backend` (runs migrations first), `seed`, `verify`, `e2e`. One obvious verb per task.
- **Docker.** Per-app multi-stage Dockerfiles and a compose file bring up the whole stack with one
  command. The backend image layer-caches dependencies ahead of source; the frontend image ships
  the standalone bundle and runs as a **non-root** user. Compose adds a backend healthcheck that the
  frontend `depends_on`, a named volume for the SQLite DB + uploads, and JSON logging. The one sharp
  edge — the `/api` rewrite destination is baked at **build** time — is handled with a `BACKEND_URL`
  build arg and documented at both call sites.
- **CI** runs the same three gates as local `verify` (frontend, backend, e2e) on every push to
  `main` and every PR. It's hardened per OpenSSF Scorecard: **every action is pinned to a full commit
  SHA**, the default `GITHUB_TOKEN` is `contents: read`, concurrency cancels superseded runs, and
  CodeQL + Scorecard workflows run alongside. The e2e job uploads its Playwright report as an
  artifact.
- **Strict typing on both sides:** `pyright` in strict mode over `app/`, TypeScript `strict` over the
  frontend. The tree is never left red.

---

## 10. Testing strategy

Roughly **120+ tests** across five layers, chosen to test the risky and the pure — not trivia.

- **Backend integration (pytest + ASGI TestClient):** the contract end-to-end — lead creation
  (including "exactly two emails composed"), every validation branch, the full auth flow, the
  state-machine matrix, resume download, the `413`/`401`/`404` edges. Email and storage are injected
  via DI overrides, so tests **capture** emails instead of sending them.
- **Backend unit:** the primitives in isolation — JWT round-trip / expiry / wrong-key / tamper
  rejection, the `SECRET_KEY` validator, storage path-traversal neutralization.
- **Property-based (Hypothesis + fast-check):** invariants asserted over thousands of generated
  adversarial inputs — no filename can escape the upload dir or leave a stray, token decode is total
  over arbitrary text, credential verification matches only the exact pair and never crashes on lone
  surrogates. These found real robustness bugs that example-based tests missed.
- **Frontend component (Vitest + RTL):** the client mutation components and status-mapping logic
  (`next/navigation` mocked).
- **E2E (Playwright):** the money path — submit a lead with a real PDF upload, log in, see it in the
  queue, mark it reached-out, reload to prove it persisted — run against a **production build** with
  a real, **isolated** backend (throwaway DB + upload dir, never the dev data, never a reused dev
  server).

---

## 11. What I'd do next with more time

Rate limiting + spam controls on the public endpoint; a transactional outbox for email; search on
the lead queue and a lead-detail view with notes/activity history; S3 + presigned URLs; Postgres
(the containers make this a `DATABASE_URL` + driver swap); error tracking (Sentry) on top of the
existing structured logs and request IDs; and a deploy pipeline that builds and promotes the images.
