.PHONY: install frontend backend seed verify

install:
	cd frontend && pnpm install && cd ../backend && uv sync

frontend:
	cd frontend && pnpm dev

backend:
	cd backend && uv run alembic upgrade head && uv run uvicorn app.main:app --reload --port 8000

seed:
	cd backend && uv run python -m app.seed

verify:
	cd frontend && pnpm verify && cd ../backend && uv run ruff check . && uv run ruff format --check . && uv run pytest
