from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlmodel import Session

from ..models import Event, EventCreate, EventQueryParams, EventRead, EventType, Project


class EventService:
    """Encapsulates all event persistence and analytics logic."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def record_event(self, project: Project, payload: EventCreate) -> EventRead:
        event = Event.from_orm(payload)
        event.project_id = project.id
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return EventRead.from_orm(event)

    def _build_filters(self, project_id: int, params: EventQueryParams):
        filters = [Event.project_id == project_id]
        if params.event_type:
            filters.append(Event.event_type == params.event_type)
        if params.user_id:
            filters.append(Event.user_id == params.user_id)
        if params.session_id:
            filters.append(Event.session_id == params.session_id)
        if params.environment:
            filters.append(Event.environment == params.environment)
        if params.release:
            filters.append(Event.release == params.release)
        if params.occurred_from:
            filters.append(Event.occurred_at >= params.occurred_from)
        if params.occurred_to:
            filters.append(Event.occurred_at <= params.occurred_to)
        if params.search:
            like_pattern = f"%{params.search}%"
            filters.append(
                or_(
                    Event.name.ilike(like_pattern),
                    Event.message.ilike(like_pattern),
                    Event.page_url.ilike(like_pattern),
                )
            )
        return filters

    def list_events(self, project_id: int, params: EventQueryParams) -> Dict[str, object]:
        filters = self._build_filters(project_id, params)
        base_query = select(Event).where(*filters).order_by(Event.occurred_at.desc())
        count_statement = select(func.count(Event.id)).where(*filters)
        total = self.session.exec(count_statement).one()
        page_size = max(1, min(params.page_size, 200))
        page = max(1, params.page)
        events = (
            self.session.exec(base_query.offset((page - 1) * page_size).limit(page_size)).all()
        )
        items = [EventRead.from_orm(event) for event in events]
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def _aggregate_counts(
        self, project_id: int, start: Optional[datetime], end: Optional[datetime]
    ) -> Dict[str, int]:
        filters = [Event.project_id == project_id]
        if start:
            filters.append(Event.occurred_at >= start)
        if end:
            filters.append(Event.occurred_at <= end)
        statement = (
            select(Event.event_type, func.count(Event.id))
            .where(*filters)
            .group_by(Event.event_type)
        )
        rows = self.session.exec(statement).all()
        return {
            (event_type.value if isinstance(event_type, EventType) else str(event_type)): count
            for event_type, count in rows
        }

    def summary(self, project_id: int, start: Optional[datetime], end: Optional[datetime]) -> Dict[str, object]:
        filters = [Event.project_id == project_id]
        if start:
            filters.append(Event.occurred_at >= start)
        if end:
            filters.append(Event.occurred_at <= end)

        total_statement = select(func.count(Event.id)).where(*filters)
        total_events = self.session.exec(total_statement).one()

        unique_users_statement = (
            select(func.count(func.distinct(Event.user_id))).where(*filters, Event.user_id.isnot(None))
        )
        unique_users = self.session.exec(unique_users_statement).one()

        latest_event_statement = select(func.max(Event.occurred_at)).where(*filters)
        latest_event = self.session.exec(latest_event_statement).one()

        counts = self._aggregate_counts(project_id, start, end)

        return {
            "total_events": total_events,
            "unique_users": unique_users,
            "latest_event": latest_event,
            "counts_by_type": counts,
        }

    def timeseries(
        self,
        project_id: int,
        start: Optional[datetime],
        end: Optional[datetime],
        granularity: str = "day",
    ) -> List[Dict[str, object]]:
        if granularity not in {"hour", "day"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid granularity")

        if granularity == "hour":
            bucket = func.strftime("%Y-%m-%d %H:00:00", Event.occurred_at)
        else:
            bucket = func.strftime("%Y-%m-%d", Event.occurred_at)

        filters = [Event.project_id == project_id]
        if start:
            filters.append(Event.occurred_at >= start)
        if end:
            filters.append(Event.occurred_at <= end)

        statement = (
            select(bucket.label("bucket"), Event.event_type, func.count(Event.id).label("count"))
            .where(*filters)
            .group_by("bucket", Event.event_type)
            .order_by("bucket")
        )

        rows = self.session.exec(statement).all()
        aggregated: Dict[str, Dict[str, int]] = {}
        for bucket_value, event_type, count in rows:
            bucket_counts = aggregated.setdefault(
                bucket_value,
                {et.value: 0 for et in EventType},
            )
            key = event_type.value if isinstance(event_type, EventType) else str(event_type)
            bucket_counts[key] = count

        output: List[Dict[str, object]] = []
        for bucket_value, counts in aggregated.items():
            total = sum(counts.values())
            output.append({"bucket": bucket_value, "counts": counts, "total": total})
        return output
