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
[uv](https://docs.astral.sh/uv/getting-started/installation/) (manages Python 3.12 automatically).

```bash
make install                          # pnpm install (frontend) + uv sync (backend)
cp backend/.env.example backend/.env  # defaults work out of the box

make backend                          # terminal 1 — API on http://127.0.0.1:8000
make frontend                         # terminal 2 — web app on http://localhost:3000
```

Then:

| URL | What | Credentials |
| --- | --- | --- |
| http://localhost:3000 | Public lead form | none |
| http://localhost:3000/admin/leads | Attorney lead queue | `attorney@example.com` / `changeme` (from `backend/.env`) |
| http://127.0.0.1:8000/docs | API reference (OpenAPI) | — |

Optional: `make seed` inserts a handful of sample leads so the queue isn't empty.

### Emails

With no configuration, both emails (prospect confirmation + attorney notification) are printed to
the backend console on every submission — nothing to sign up for.

To send real email, set `RESEND_API_KEY` in `backend/.env` ([free key](https://resend.com)).
Heads-up: without a verified domain, Resend's free tier only delivers to the account owner's own
address, so use your own email (or `+alias`es) when demoing.

## Tests

```bash
make verify              # frontend typecheck/lint/format/unit + backend ruff/pytest
cd frontend && pnpm test:e2e   # Playwright end-to-end (boots API + prod build)
```

CI runs the same gates on every push (`.github/workflows/ci.yml`).

## Repo map

```
frontend/   Next.js app — public form, login, /admin/leads queue
backend/    FastAPI app — leads API, auth, email, storage, migrations
docs/       DESIGN.md (architecture & trade-offs), AGENT_USAGE.md
Makefile    install / frontend / backend / seed / verify
```
