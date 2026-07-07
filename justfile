# Alma — task runner (https://just.systems). Run `just` to see recipes.

# List available recipes
default:
    @just --list

# Install dependencies (also creates backend/.env if missing)
install: setup
    cd frontend && pnpm install
    cd backend && uv sync

# Create backend/.env from .env.example (never overwrites an existing one)
setup:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -f backend/.env ]; then
      echo "backend/.env already exists — leaving it unchanged"
    else
      cp .env.example backend/.env
      echo "Created backend/.env from .env.example"
    fi

# Run the Next.js dev server on http://localhost:3000
frontend:
    cd frontend && pnpm dev

# Run the FastAPI backend on http://127.0.0.1:8000 (applies migrations first)
backend:
    cd backend && uv run alembic upgrade head && uv run uvicorn app.main:app --reload --port 8000

# Seed a few sample leads (idempotent)
seed:
    cd backend && uv run python -m app.seed

# Full gate: frontend typecheck/lint/format/unit + backend ruff/pyright/pytest
verify:
    cd frontend && pnpm verify
    cd backend && uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest

# End-to-end tests (boots an isolated backend + production build)
e2e:
    cd frontend && pnpm exec playwright install chromium && pnpm test:e2e
