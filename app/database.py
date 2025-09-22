from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings


def _create_engine():
    settings = get_settings()
    connect_args = {}
    if settings.database_url.startswith("sqlite"):  # pragma: no branch - simple configuration
        connect_args["check_same_thread"] = False
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        connect_args=connect_args,
        poolclass=StaticPool if settings.database_url.startswith("sqlite://") else None,
    )
    return engine


engine = _create_engine()


def init_db() -> None:
    """Create database tables if they do not exist."""

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""

    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope for scripts and background tasks."""

    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover - defensive programming
        session.rollback()
        raise
    finally:
        session.close()
