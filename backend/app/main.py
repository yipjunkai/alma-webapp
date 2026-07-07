"""FastAPI application factory."""

import logging
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api import auth, health, leads
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_ctx
from app.db import ensure_sqlite_dir

_access_logger = logging.getLogger("app.access")

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


class RequestContextMiddleware:
    """Assign a request id, echo it in X-Request-ID, and log one line per request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        header_map = dict(scope["headers"])
        incoming = header_map.get(b"x-request-id")
        request_id: str = incoming.decode("latin-1") if incoming else str(uuid.uuid4())
        token = request_id_ctx.set(request_id)
        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                message.setdefault("headers", []).append(
                    (b"x-request-id", request_id.encode("latin-1"))
                )
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            _access_logger.info(
                "request",
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status": status_code,
                    "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                },
            )
            request_id_ctx.reset(token)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    ensure_sqlite_dir(settings.database_url)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)
    app = FastAPI(title="Alma Leads API", lifespan=lifespan)
    app.add_middleware(MaxBodySizeMiddleware, max_bytes=MAX_REQUEST_BYTES)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Outermost middleware: assigns the request id and times the whole request.
    app.add_middleware(RequestContextMiddleware)
    api_router = APIRouter(prefix="/api")
    api_router.include_router(health.router)
    api_router.include_router(auth.router)
    api_router.include_router(leads.router)
    app.include_router(api_router)
    return app


app = create_app()
