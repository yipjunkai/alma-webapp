# Alma — Lead Management

Prospects submit a public form (name, email, resume). The app stores the lead, emails both the
prospect and an attorney, and gives attorneys an auth-guarded queue to work leads from `PENDING`
to `REACHED_OUT`.

- **Frontend:** Next.js 16 (App Router, React 19, Tailwind v4, shadcn/ui) — `frontend/`
- **API:** FastAPI (SQLAlchemy 2, Alembic, SQLite) — `backend/`
- **Email:** Resend, with a console fallback that needs no account
- **Docs:** [design decisions](docs/DESIGN.md) · [coding-agent usage](docs/AGENT_USAGE.md)

## Run locally

Prerequisites: [Node 24+](https://nodejs.org), [pnpm](https://pnpm.io/installation),
[uv](https://docs.astral.sh/uv/getting-started/installation/) (manages Python 3.12 automatically),
and [just](https://just.systems/man/en/packages.html) (task runner).

```bash
just install    # installs deps and creates backend/.env from .env.example (defaults work as-is)

just backend    # terminal 1 — API on http://127.0.0.1:8000
just frontend   # terminal 2 — web app on http://localhost:3000
```

Then:

| URL | What | Credentials |
| --- | --- | --- |
| http://localhost:3000 | Public lead form | none |
| http://localhost:3000/admin/leads | Attorney lead queue | `attorney@example.com` / `changeme` (from `backend/.env`) |
| http://127.0.0.1:8000/docs | API reference (OpenAPI) | — |

Optional: `just seed` inserts a handful of sample leads so the queue isn't empty.

### With Docker

Prefer containers? This runs the whole stack — frontend, API, and a persistent
data volume — with one command (no local Node/Python/uv needed):

```bash
docker compose up --build   # → http://localhost:3000
```

### Emails

With no configuration, both emails (prospect confirmation + attorney notification) are printed to
the backend console on every submission — nothing to sign up for.

To send real email, set `RESEND_API_KEY` in `backend/.env` ([free key](https://resend.com)).
Heads-up: without a verified domain, Resend's free tier only delivers to the account owner's own
address, so use your own email (or `+alias`es) when demoing.

## Tests

```bash
just verify   # frontend typecheck/lint/format/unit + backend ruff/pytest
```

End-to-end (Playwright drives the real UI against a production build and an isolated backend):

```bash
just e2e   # installs the browser, boots an isolated backend + prod build, runs the suite
           # ports 3000 and 8000 must be free — stop `just frontend` / `just backend` first
```

CI runs the same gates on every push to `main` and every pull request
(`.github/workflows/ci.yml`).

## Repo map

```
frontend/     Next.js app — public form, login, /admin/leads queue
backend/      FastAPI app — leads API, auth, email, storage, migrations
docs/         DESIGN.md (architecture & trade-offs), AGENT_USAGE.md
.env.example  backend config template (copied to backend/.env by `just setup`)
justfile      setup / install / frontend / backend / seed / verify / e2e
```
