"""
Shots CRUD router – nested under scenes with full ownership-chain verification.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middleware import get_current_user
from db.database import get_db
from models.user import User
from schemas.shot import ShotCreate, ShotUpdate, ShotResponse
from services.project_service import ProjectService

router = APIRouter(tags=["Shots"])
_svc = ProjectService()


@router.post(
    "/scenes/{scene_id}/shots",
    response_model=ShotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_shot(
    scene_id: uuid.UUID,
    payload: ShotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShotResponse:
    """Add a new shot to a scene."""
    # Verify ownership: scene → project → user
    await _svc.verify_scene_ownership(db, scene_id, current_user)

    shot = await _svc.create_shot(
        db,
        scene_id,
        shot_number=payload.shot_number,
        shot_type=payload.shot_type,
        camera_angle=payload.camera_angle,
        camera_movement=payload.camera_movement,
        lens_mm=payload.lens_mm,
        description=payload.description,
        notes=payload.notes,
    )
    return ShotResponse.model_validate(shot)


@router.get(
    "/scenes/{scene_id}/shots",
    response_model=List[ShotResponse],
)
async def list_shots(
    scene_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ShotResponse]:
    """List all shots in a scene, ordered by shot_number."""
    await _svc.verify_scene_ownership(db, scene_id, current_user)
    shots = await _svc.get_scene_shots(db, scene_id)
    return [ShotResponse.model_validate(s) for s in shots]


@router.put("/shots/{shot_id}", response_model=ShotResponse)
async def update_shot(
    shot_id: uuid.UUID,
    payload: ShotUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShotResponse:
    """Update a shot's fields."""
    shot = await _svc.verify_shot_ownership(db, shot_id, current_user)
    updated = await _svc.update_shot(
        db, shot, payload.model_dump(exclude_unset=True)
    )
    return ShotResponse.model_validate(updated)


@router.delete("/shots/{shot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shot(
    shot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a shot."""
    shot = await _svc.verify_shot_ownership(db, shot_id, current_user)
    await _svc.delete_shot(db, shot)
