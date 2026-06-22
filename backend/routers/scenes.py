"""
Scenes CRUD router – nested under projects with ownership verification.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middleware import get_current_user
from db.database import get_db
from models.user import User
from schemas.scene import SceneCreate, SceneUpdate, SceneResponse
from services.project_service import ProjectService

router = APIRouter(tags=["Scenes"])
_svc = ProjectService()


@router.post(
    "/projects/{project_id}/scenes",
    response_model=SceneResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scene(
    project_id: uuid.UUID,
    payload: SceneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    """Add a new scene to a project."""
    # Verify project ownership
    await _svc.get_project(db, project_id, current_user)

    scene = await _svc.create_scene(
        db,
        project_id,
        scene_number=payload.scene_number,
        title=payload.title,
        description=payload.description,
        location_type=payload.location_type,
        time_of_day=payload.time_of_day,
        mood=payload.mood,
        notes=payload.notes,
    )
    return SceneResponse.model_validate(scene)


@router.get(
    "/projects/{project_id}/scenes",
    response_model=List[SceneResponse],
)
async def list_scenes(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[SceneResponse]:
    """List all scenes in a project, ordered by scene_number."""
    await _svc.get_project(db, project_id, current_user)
    scenes = await _svc.get_project_scenes(db, project_id)
    return [SceneResponse.model_validate(s) for s in scenes]


@router.get("/scenes/{scene_id}", response_model=SceneResponse)
async def get_scene(
    scene_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    """Get a single scene by ID (verifies project ownership)."""
    scene = await _svc.verify_scene_ownership(db, scene_id, current_user)
    return SceneResponse.model_validate(scene)


@router.put("/scenes/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: uuid.UUID,
    payload: SceneUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SceneResponse:
    """Update a scene's fields."""
    scene = await _svc.verify_scene_ownership(db, scene_id, current_user)
    updated = await _svc.update_scene(
        db, scene, payload.model_dump(exclude_unset=True)
    )
    return SceneResponse.model_validate(updated)


@router.delete("/scenes/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene(
    scene_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a scene and its shots (cascade)."""
    scene = await _svc.verify_scene_ownership(db, scene_id, current_user)
    await _svc.delete_scene(db, scene)
