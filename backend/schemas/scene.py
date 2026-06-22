"""Pydantic schemas for the Scene model."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from models.scene import LocationType, TimeOfDay


class SceneCreate(BaseModel):
    """Payload for creating a new scene."""

    scene_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    location_type: LocationType
    time_of_day: TimeOfDay
    mood: str = ""
    notes: Optional[str] = None


class SceneUpdate(BaseModel):
    """Payload for updating an existing scene."""

    scene_number: Optional[int] = Field(None, ge=1)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    location_type: Optional[LocationType] = None
    time_of_day: Optional[TimeOfDay] = None
    mood: Optional[str] = None
    notes: Optional[str] = None


class SceneResponse(BaseModel):
    """Public representation of a scene."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    scene_number: int
    title: str
    description: str
    location_type: LocationType
    time_of_day: TimeOfDay
    mood: str
    notes: Optional[str] = None
    created_at: datetime
