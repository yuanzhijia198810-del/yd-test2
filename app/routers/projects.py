from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlmodel import Session

from ..database import get_session
from ..models import ProjectCreate, ProjectRead, ProjectUpdate
from ..services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_project_service(session: Session = Depends(get_session)) -> ProjectService:
    return ProjectService(session)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, service: ProjectService = Depends(get_project_service)) -> ProjectRead:
    return service.create_project(payload)


@router.get("", response_model=list[ProjectRead])
def list_projects(service: ProjectService = Depends(get_project_service)) -> list[ProjectRead]:
    return service.list_projects()


@router.get("/{project_id}", response_model=ProjectRead)
def read_project(project_id: int, service: ProjectService = Depends(get_project_service)) -> ProjectRead:
    return service.read_project(project_id)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    return service.update_project(project_id, payload)


@router.post("/{project_id}/rotate-key", response_model=ProjectRead)
def rotate_key(project_id: int, service: ProjectService = Depends(get_project_service)) -> ProjectRead:
    return service.rotate_api_key(project_id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, service: ProjectService = Depends(get_project_service)) -> Response:
    service.delete_project(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
