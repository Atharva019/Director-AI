"""Pydantic schemas for the Project model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from pydantic import BaseModel, ConfigDict, Field

from models.project import ProjectStatus

if TYPE_CHECKING:
    from schemas.scene import SceneResponse


class ProjectCreate(BaseModel):
    """Payload for creating a new project."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    genre: str = Field(default="", max_length=100)
    status: ProjectStatus = ProjectStatus.DRAFT


class ProjectUpdate(BaseModel):
    """Payload for updating an existing project."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    genre: Optional[str] = Field(None, max_length=100)
    status: Optional[ProjectStatus] = None


class ProjectResponse(BaseModel):
    """Public representation of a project."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str] = None
    genre: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(ProjectResponse):
    """Project with nested scenes (used for detail endpoints)."""

    scenes: List[SceneResponse] = []


def _rebuild_forward_refs() -> None:
    """Rebuild forward references once all schemas are loaded."""
    from schemas.scene import SceneResponse  # noqa: F811

    # Make SceneResponse available in this module's namespace so
    # Pydantic can resolve the forward reference string.
    globals()["SceneResponse"] = SceneResponse
    ProjectDetailResponse.model_rebuild()


_rebuild_forward_refs()


