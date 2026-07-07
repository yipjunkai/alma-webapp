"""FastAPI application factory."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api import auth, health, leads
from app.core.config import get_settings
from app.db import ensure_sqlite_dir

# Coarse abuse guard rejecting over-large bodies before they are parsed/buffered.
# The precise 5 MB resume cap is enforced (as a 422) while streaming in storage.py.
MAX_REQUEST_BYTES = 10 * 1024 * 1024


class MaxBodySizeMiddleware:
    """Reject requests whose Content-Length exceeds the limit with 413, pre-parse."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            for name, value in scope["headers"]:
                if name == b"content-length":
                    try:
                        too_large = int(value) > self.max_bytes
                    except ValueError:
                        too_large = False
                    if too_large:
                        response = JSONResponse(
                            {"detail": "Request body too large."}, status_code=413
                        )
                        await response(scope, receive, send)
                        return
                    break
        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    ensure_sqlite_dir(settings.database_url)
    yield


def create_app() -> FastAPI:
    # Make app INFO logs (e.g. console emails) visible; no-op if logging is configured.
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    app = FastAPI(title="Alma Leads API", lifespan=lifespan)
    app.add_middleware(MaxBodySizeMiddleware, max_bytes=MAX_REQUEST_BYTES)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
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
