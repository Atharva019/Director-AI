"""
Projects CRUD router – all operations scoped to the authenticated user.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middleware import get_current_user
from db.database import get_db
from models.user import User
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from services import quota_service
from services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])
_svc = ProjectService()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Create a new filmmaking project."""
    await quota_service.enforce_project_quota(db, current_user)
    project = await _svc.create_project(
        db,
        current_user,
        title=payload.title,
        description=payload.description,
        genre=payload.genre,
        status=payload.status,
    )
    return ProjectResponse.model_validate(project)


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ProjectResponse]:
    """List all projects owned by the current user."""
    projects = await _svc.get_user_projects(db, current_user)
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Get a single project by ID (must be owned by the current user)."""
    project = await _svc.get_project(db, project_id, current_user)
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Update a project's fields."""
    project = await _svc.get_project(db, project_id, current_user)
    updated = await _svc.update_project(
        db, project, payload.model_dump(exclude_unset=True)
    )
    return ProjectResponse.model_validate(updated)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a project and all its scenes/shots (cascade)."""
    project = await _svc.get_project(db, project_id, current_user)
    await _svc.delete_project(db, project)
