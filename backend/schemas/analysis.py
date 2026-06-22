"""Pydantic schemas for the SceneAnalysis model."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AnalysisResultSchema(BaseModel):
    """Structured cinematography analysis returned by the AI."""

    # ── Lighting ──────────────────────────────────────────────────────────
    lighting_setup: str = ""
    color_temperature: str = ""
    lighting_style: str = ""
    lighting_ratio: str = ""

    # ── Camera / Lens ─────────────────────────────────────────────────────
    estimated_focal_length: str = ""
    estimated_aperture: str = ""
    depth_of_field: str = ""
    camera_height: str = ""
    camera_angle: str = ""

    # ── Composition ───────────────────────────────────────────────────────
    composition_rules: List[str] = Field(default_factory=list)
    framing: str = ""
    aspect_ratio: str = ""

    # ── Color / Mood ──────────────────────────────────────────────────────
    dominant_colors: List[str] = Field(default_factory=list)
    color_palette_mood: str = ""
    overall_mood: str = ""

    # ── Recommendations ───────────────────────────────────────────────────
    recommended_equipment: List[str] = Field(default_factory=list)
    setup_instructions: List[str] = Field(default_factory=list)
    tips: List[str] = Field(default_factory=list)

    # ── Meta ──────────────────────────────────────────────────────────────
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    model_used: str = ""

class AnalysisSceneRef(BaseModel):
    """Minimal representation of a scene for an analysis."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    scene_number: int
    title: str


class SceneAnalysisCreate(BaseModel):
    """Internal schema used when persisting an analysis (not user-facing)."""

    scene_id: Optional[uuid.UUID] = None
    image_path: str
    analysis_result: Dict[str, Any]
    model_used: str
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class SceneAnalysisResponse(BaseModel):
    """Public representation of a scene analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scene_id: Optional[uuid.UUID] = None
    scene: Optional[AnalysisSceneRef] = None
    user_id: uuid.UUID
    image_path: str
    analysis_result: Dict[str, Any]
    model_used: str
    confidence_score: float
    created_at: datetime
