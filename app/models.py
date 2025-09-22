from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class EventType(str, Enum):
    ERROR = "error"
    PERFORMANCE = "performance"
    INTERACTION = "interaction"
    CUSTOM = "custom"


class ProjectBase(SQLModel):
    name: str = Field(index=True, description="Human friendly project name.")
    description: Optional[str] = Field(default=None, description="Optional description of the project.")


class Project(ProjectBase, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    api_key: str = Field(index=True, unique=True, description="API key used by client SDKs.")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class ProjectRead(ProjectBase):
    id: int
    api_key: str
    created_at: datetime
    updated_at: datetime


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None


class EventBase(SQLModel):
    event_type: EventType = Field(sa_column_kwargs={"nullable": False})
    name: str = Field(description="Name of the event or error.")
    message: Optional[str] = Field(default=None, description="Detailed error message, if any.")
    payload: Dict[str, Any] = Field(
        sa_column=Column(JSON),
        default_factory=dict,
        description="Structured payload captured by the client.",
    )
    user_id: Optional[str] = Field(default=None, description="Identifier of the affected user.")
    session_id: Optional[str] = Field(default=None, description="Identifier of the browser session.")
    page_url: Optional[str] = Field(default=None, description="Page URL where the event occurred.")
    user_agent: Optional[str] = Field(default=None, description="User agent string reported by the client.")
    environment: Optional[str] = Field(default=None, description="Application environment (prod, staging, etc.).")
    release: Optional[str] = Field(default=None, description="Application release version.")
    occurred_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp at which the event occurred on the client side.",
    )


class Event(EventBase, table=True):
    __tablename__ = "events"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True, nullable=False)
    received_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class EventRead(EventBase):
    id: int
    project_id: int
    received_at: datetime


class EventCreate(EventBase):
    pass


class EventQueryParams(SQLModel):
    event_type: Optional[EventType] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    environment: Optional[str] = None
    release: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 50
    occurred_from: Optional[datetime] = None
    occurred_to: Optional[datetime] = None
