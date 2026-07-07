"""Database engine, session factory, and declarative base."""

from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def ensure_sqlite_dir(database_url: str) -> None:
    """Create the parent directory for a file-based SQLite database if needed."""
    url = make_url(database_url)
    if url.get_backend_name() == "sqlite" and url.database and url.database != ":memory:":
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    ensure_sqlite_dir(settings.database_url)
    connect_args = {}
    if make_url(settings.database_url).get_backend_name() == "sqlite":
        # Allow sessions to be used from FastAPI's threadpool workers.
        connect_args["check_same_thread"] = False
    return create_engine(settings.database_url, connect_args=connect_args)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a database session."""
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()
