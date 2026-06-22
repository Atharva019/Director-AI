"""Pydantic schemas for the Shot model."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ShotCreate(BaseModel):
    """Payload for creating a new shot."""

    shot_number: Optional[int] = Field(None, ge=1)
    shot_type: str = Field(default="", max_length=100)
    camera_angle: str = Field(default="", max_length=100)
    camera_movement: str = Field(default="", max_length=100)
    lens_mm: Optional[int] = Field(None, ge=1, le=2000)
    description: str = ""
    notes: Optional[str] = None


class ShotUpdate(BaseModel):
    """Payload for updating an existing shot."""

    shot_number: Optional[int] = Field(None, ge=1)
    shot_type: Optional[str] = Field(None, max_length=100)
    camera_angle: Optional[str] = Field(None, max_length=100)
    camera_movement: Optional[str] = Field(None, max_length=100)
    lens_mm: Optional[int] = Field(None, ge=1, le=2000)
    description: Optional[str] = None
    notes: Optional[str] = None


class ShotResponse(BaseModel):
    """Public representation of a shot."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scene_id: uuid.UUID
    shot_number: int
    shot_type: str
    camera_angle: str
    camera_movement: str
    lens_mm: Optional[int] = None
    description: str
    notes: Optional[str] = None
    created_at: datetime
