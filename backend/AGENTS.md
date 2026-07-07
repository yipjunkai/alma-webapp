# Backend agent guide

Golden rule: you are not done until ALL of these are green (run from `backend/`):

```sh
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest
```

`pyright` runs strict on `app/`; `tests/` relax the httpx TestClient "unknown type" noise (see `[tool.pyright]` in `pyproject.toml`).

## Commands

```sh
uv sync                                              # install dependencies
uv run alembic upgrade head                          # create/migrate SQLite db (data/alma.db)
uv run uvicorn app.main:app --reload --port 8000     # dev server (http://127.0.0.1:8000)
uv run python -m app.seed                            # seed ~5 sample leads (idempotent; run after migrations)
uv run pytest                                        # tests
uv run pyright                                       # strict type check
uv run ruff check . && uv run ruff format .          # lint + format
```

Run `just setup` from the repo root (or `cp ../.env.example .env`) to create
`backend/.env`. With `RESEND_API_KEY` empty, emails are logged to the console
instead of sent.

## Structure

```
app/
  main.py            create_app() factory; routers mounted under /api; CORS
  core/config.py     Settings (pydantic-settings, env vars), cached get_settings()
  core/security.py   JWT create/decode (HS256), constant-time credential check
  db.py              engine/session factory/Base, get_db dependency
  models.py          Lead ORM model (uuid pk, state enum, timestamps)
  schemas.py         request/response models (the API contract)
  api/               thin routers: health, auth, leads (+ deps.py for auth/session deps)
  services/          business logic: email (console/Resend), storage (resume files), leads
  seed.py            sample data seeder
alembic/             migrations; alembic owns the schema in dev/prod
tests/               pytest + TestClient; DI overrides in conftest.py
```

## Conventions

- Routers stay thin; business logic lives in `app/services/`.
- Settings come from env via pydantic-settings (`app/core/config.py`); never hardcode.
- SQLAlchemy 2.0 style (`Mapped[]` / `mapped_column`); type-annotate everything.
- Tests use dependency-injection overrides (see `tests/conftest.py`) — never call the
  real Resend API in tests.
- Alembic owns the schema in dev/prod (`uv run alembic upgrade head`); tests use
  `Base.metadata.create_all` against a throwaway SQLite file.
