from __future__ import annotations

from fastapi import FastAPI

from .config import get_settings
from .database import init_db
from .routers import events, projects, stats


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    @app.on_event("startup")
    def _startup() -> None:  # pragma: no cover - minimal boot hook
        init_db()

    app.include_router(projects.router)
    app.include_router(events.router)
    app.include_router(stats.router)

    return app


app = create_app()
