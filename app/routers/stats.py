from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from ..database import get_session
from ..services.event_service import EventService
from ..services.project_service import ProjectService

router = APIRouter(prefix="/api/stats", tags=["stats"])


def get_services(session: Session = Depends(get_session)) -> tuple[EventService, ProjectService]:
    return EventService(session), ProjectService(session)


@router.get("/project/{project_id}/summary")
def project_summary(
    project_id: int,
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    services: tuple[EventService, ProjectService] = Depends(get_services),
) -> dict:
    event_service, project_service = services
    project_service.read_project(project_id)
    return event_service.summary(project_id, start, end)


@router.get("/project/{project_id}/timeseries")
def project_timeseries(
    project_id: int,
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    granularity: str = Query(default="day"),
    services: tuple[EventService, ProjectService] = Depends(get_services),
) -> list[dict]:
    event_service, project_service = services
    project_service.read_project(project_id)
    return event_service.timeseries(project_id, start, end, granularity)
