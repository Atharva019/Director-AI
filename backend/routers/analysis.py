"""
Scene-analysis router – upload an image, run AI analysis, and manage results.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth.middleware import get_current_user
from db.database import get_db
from models.analysis import SceneAnalysis
from models.user import User
from schemas.analysis import SceneAnalysisResponse
from services.image_service import ImageService
from services.scene_analyzer import SceneAnalyzer
from services.project_service import ProjectService
from services import quota_service

router = APIRouter(tags=["Analysis"])

_image_svc = ImageService()
_analyzer = SceneAnalyzer()
_project_svc = ProjectService()


@router.post(
    "/analyze",
    response_model=SceneAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_image(
    file: UploadFile = File(..., description="Film still or reference image (JPEG/PNG/WebP)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SceneAnalysisResponse:
    """
    Upload an image and run an AI-powered cinematography analysis.

    The image is validated, saved, then sent to the configured Ollama
    vision model.  The structured analysis result is persisted and returned.
    """
    # 0. Check quota BEFORE spending an upload or an AI call the user isn't
    #    entitled to.
    await quota_service.enforce_analysis_quota(db, current_user)

    # 1. Save and validate the upload
    try:
        image_path = await _image_svc.save_upload(file)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # 2. Run the analysis
    try:
        result = await _analyzer.analyze(image_path)
    except FileNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=f"AI service error: {exc}")

    # 3. Persist the analysis
    confidence = result.pop("confidence_score", 0.0)
    model_used = result.pop("model_used", "")

    analysis = SceneAnalysis(
        user_id=current_user.id,
        image_path=image_path,
        analysis_result=result,
        model_used=model_used,
        confidence_score=confidence,
    )
    db.add(analysis)
    await db.flush()
    await db.refresh(analysis)

    return SceneAnalysisResponse.model_validate(analysis)


@router.get("/analyses", response_model=List[SceneAnalysisResponse])
async def list_analyses(
    scene_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[SceneAnalysisResponse]:
    """List all analyses created by the current user. Can be filtered by scene."""
    stmt = select(SceneAnalysis).where(SceneAnalysis.user_id == current_user.id).options(selectinload(SceneAnalysis.scene))
    if scene_id:
        stmt = stmt.where(SceneAnalysis.scene_id == scene_id)
    
    stmt = stmt.order_by(SceneAnalysis.created_at.desc())
    result = await db.execute(stmt)
    analyses = result.scalars().all()
    return [SceneAnalysisResponse.model_validate(a) for a in analyses]


@router.get("/analyses/{analysis_id}", response_model=SceneAnalysisResponse)
async def get_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SceneAnalysisResponse:
    """Retrieve a single analysis by ID (must belong to the current user)."""
    result = await db.execute(
        select(SceneAnalysis).where(
            SceneAnalysis.id == analysis_id,
            SceneAnalysis.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found.")
    return SceneAnalysisResponse.model_validate(analysis)


@router.post(
    "/analyses/{analysis_id}/attach/{scene_id}",
    response_model=SceneAnalysisResponse,
)
async def attach_analysis_to_scene(
    analysis_id: uuid.UUID,
    scene_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SceneAnalysisResponse:
    """
    Attach an existing analysis to a scene.

    Verifies that:
    - The analysis belongs to the current user.
    - The target scene belongs to a project owned by the current user.
    """
    # Verify analysis ownership
    result = await db.execute(
        select(SceneAnalysis).where(
            SceneAnalysis.id == analysis_id,
            SceneAnalysis.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found.")

    # Verify scene ownership
    await _project_svc.verify_scene_ownership(db, scene_id, current_user)

    # Attach
    analysis.scene_id = scene_id
    await db.flush()
    await db.refresh(analysis)

    return SceneAnalysisResponse.model_validate(analysis)
