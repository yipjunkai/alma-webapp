# Alma — agent guide (monorepo)

## Layout

| Directory   | What it is                                            |
| ----------- | ----------------------------------------------------- |
| `frontend/` | Next.js 16 web app — see `frontend/AGENTS.md`         |
| `backend/`  | FastAPI API — see `backend/AGENTS.md`                 |

## Golden rule

Run `just verify` before considering any change done. Never leave the tree red.

## Commands

| Command         | Purpose                                                       |
| --------------- | ------------------------------------------------------------- |
| `just install`  | deps (`pnpm install` + `uv sync`) and create `backend/.env`   |
| `just frontend` | Next dev server :3000                                         |
| `just backend`  | `alembic upgrade head` + uvicorn :8000                        |
| `just seed`     | Seed sample leads                                             |
| `just verify`   | frontend typecheck/lint/format/unit + backend ruff/pytest     |
| `just e2e`      | Playwright end-to-end (isolated backend + prod build)         |
