from __future__ import annotations

from datetime import datetime
from secrets import token_urlsafe
from typing import List

from fastapi import HTTPException, status
from sqlmodel import Session, select

from ..models import Project, ProjectCreate, ProjectRead, ProjectUpdate


class ProjectService:
    """Service layer encapsulating project related operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _generate_api_key(self) -> str:
        return token_urlsafe(32)

    def create_project(self, payload: ProjectCreate) -> ProjectRead:
        project = Project.from_orm(payload)
        project.api_key = self._generate_api_key()
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return ProjectRead.from_orm(project)

    def list_projects(self) -> List[ProjectRead]:
        statement = select(Project).order_by(Project.created_at.desc())
        results = self.session.exec(statement).all()
        return [ProjectRead.from_orm(project) for project in results]

    def get_project(self, project_id: int) -> Project:
        project = self.session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    def get_project_by_key(self, api_key: str) -> Project:
        statement = select(Project).where(Project.api_key == api_key)
        project = self.session.exec(statement).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid API key")
        return project

    def read_project(self, project_id: int) -> ProjectRead:
        project = self.get_project(project_id)
        return ProjectRead.from_orm(project)

    def update_project(self, project_id: int, payload: ProjectUpdate) -> ProjectRead:
        project = self.get_project(project_id)
        project_data = payload.dict(exclude_unset=True)
        for key, value in project_data.items():
            setattr(project, key, value)
        project.updated_at = datetime.utcnow()
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return ProjectRead.from_orm(project)

    def rotate_api_key(self, project_id: int) -> ProjectRead:
        project = self.get_project(project_id)
        project.api_key = self._generate_api_key()
        project.updated_at = datetime.utcnow()
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return ProjectRead.from_orm(project)

    def delete_project(self, project_id: int) -> None:
        project = self.get_project(project_id)
        self.session.delete(project)
        self.session.commit()
