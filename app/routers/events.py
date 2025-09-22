from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlmodel import Session

from ..database import get_session
from ..models import EventCreate, EventQueryParams, EventRead, EventType
from ..services.event_service import EventService
from ..services.project_service import ProjectService

router = APIRouter(prefix="/api/events", tags=["events"])


def get_services(session: Session = Depends(get_session)) -> tuple[EventService, ProjectService]:
    return EventService(session), ProjectService(session)


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def ingest_event(
    payload: EventCreate,
    api_key: str = Header(..., alias="X-API-Key"),
    services: tuple[EventService, ProjectService] = Depends(get_services),
) -> EventRead:
    event_service, project_service = services
    project = project_service.get_project_by_key(api_key)
    return event_service.record_event(project, payload)


@router.get("/project/{project_id}")
def list_events(
    project_id: int,
    event_type: Optional[EventType] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    environment: Optional[str] = Query(default=None),
    release: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    occurred_from: Optional[datetime] = Query(default=None),
    occurred_to: Optional[datetime] = Query(default=None),
    services: tuple[EventService, ProjectService] = Depends(get_services),
) -> dict:
    event_service, project_service = services
    project_service.read_project(project_id)  # ensure project exists
    params = EventQueryParams(
        event_type=event_type,
        user_id=user_id,
        session_id=session_id,
        environment=environment,
        release=release,
        search=search,
        page=page,
        page_size=page_size,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
    )
    return event_service.list_events(project_id, params)
