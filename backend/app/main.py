"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, health, leads
from app.core.config import get_settings
from app.db import ensure_sqlite_dir

FRONTEND_ORIGIN = "http://localhost:3000"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    ensure_sqlite_dir(settings.database_url)
    yield


def create_app() -> FastAPI:
    # Make app INFO logs (e.g. console emails) visible; no-op if logging is configured.
    logging.basicConfig(level=logging.INFO)
    app = FastAPI(title="Alma Leads API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    api_router = APIRouter(prefix="/api")
    api_router.include_router(health.router)
    api_router.include_router(auth.router)
    api_router.include_router(leads.router)
    app.include_router(api_router)
    return app


app = create_app()
