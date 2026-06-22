"""
Business-logic layer for Projects, Scenes, and Shots.

Provides ownership verification and common query patterns so that
routers stay thin and focused on HTTP concerns.
"""

import uuid
import logging
from typing import List, Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.project import Project
from models.scene import Scene
from models.shot import Shot
from models.user import User

logger = logging.getLogger(__name__)


class ProjectService:
    """Encapsulates project / scene / shot business logic."""

    # ── Projects ──────────────────────────────────────────────────────────

    @staticmethod
    async def get_user_projects(db: AsyncSession, user: User) -> Sequence[Project]:
        """Return all projects owned by *user*."""
        result = await db.execute(
            select(Project)
            .where(Project.user_id == user.id)
            .order_by(Project.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_project(
        db: AsyncSession, project_id: uuid.UUID, user: User
    ) -> Project:
        """
        Fetch a single project by ID, verifying ownership.

        Raises HTTPException 404 if not found, 403 if not owned.
        """
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if project is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")
        if project.user_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your project.")
        return project

    @staticmethod
    async def create_project(db: AsyncSession, user: User, **kwargs) -> Project:
        """Create a new project for the given user."""
        project = Project(user_id=user.id, **kwargs)
        db.add(project)
        await db.flush()
        await db.refresh(project)
        return project

    @staticmethod
    async def update_project(
        db: AsyncSession, project: Project, data: dict
    ) -> Project:
        """Apply partial updates to a project."""
        for key, value in data.items():
            if value is not None:
                setattr(project, key, value)
        await db.flush()
        await db.refresh(project)
        return project

    @staticmethod
    async def delete_project(db: AsyncSession, project: Project) -> None:
        """Delete a project (cascades to scenes/shots)."""
        await db.delete(project)
        await db.flush()

    # ── Scenes ────────────────────────────────────────────────────────────

    @staticmethod
    async def get_project_scenes(
        db: AsyncSession, project_id: uuid.UUID
    ) -> Sequence[Scene]:
        """Return scenes for a project, ordered by scene_number."""
        result = await db.execute(
            select(Scene)
            .where(Scene.project_id == project_id)
            .order_by(Scene.scene_number)
        )
        return result.scalars().all()

    @staticmethod
    async def get_scene(db: AsyncSession, scene_id: uuid.UUID) -> Scene:
        """Fetch a single scene by ID."""
        result = await db.execute(select(Scene).where(Scene.id == scene_id))
        scene = result.scalar_one_or_none()
        if scene is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Scene not found.")
        return scene

    @staticmethod
    async def create_scene(
        db: AsyncSession, project_id: uuid.UUID, **kwargs
    ) -> Scene:
        """Create a new scene under a project."""
        scene = Scene(project_id=project_id, **kwargs)
        db.add(scene)
        await db.flush()
        await db.refresh(scene)
        return scene

    @staticmethod
    async def update_scene(db: AsyncSession, scene: Scene, data: dict) -> Scene:
        """Apply partial updates to a scene."""
        for key, value in data.items():
            if value is not None:
                setattr(scene, key, value)
        await db.flush()
        await db.refresh(scene)
        return scene

    @staticmethod
    async def delete_scene(db: AsyncSession, scene: Scene) -> None:
        """Delete a scene (cascades to shots)."""
        await db.delete(scene)
        await db.flush()

    # ── Shots ─────────────────────────────────────────────────────────────

    @staticmethod
    async def get_scene_shots(
        db: AsyncSession, scene_id: uuid.UUID
    ) -> Sequence[Shot]:
        """Return shots for a scene, ordered by shot_number."""
        result = await db.execute(
            select(Shot)
            .where(Shot.scene_id == scene_id)
            .order_by(Shot.shot_number)
        )
        return result.scalars().all()

    @staticmethod
    async def get_shot(db: AsyncSession, shot_id: uuid.UUID) -> Shot:
        """Fetch a single shot by ID."""
        result = await db.execute(select(Shot).where(Shot.id == shot_id))
        shot = result.scalar_one_or_none()
        if shot is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Shot not found.")
        return shot

    @staticmethod
    async def create_shot(
        db: AsyncSession, scene_id: uuid.UUID, **kwargs
    ) -> Shot:
        """Create a new shot under a scene."""
        shot = Shot(scene_id=scene_id, **kwargs)
        db.add(shot)
        await db.flush()
        await db.refresh(shot)
        return shot

    @staticmethod
    async def update_shot(db: AsyncSession, shot: Shot, data: dict) -> Shot:
        """Apply partial updates to a shot."""
        for key, value in data.items():
            if value is not None:
                setattr(shot, key, value)
        await db.flush()
        await db.refresh(shot)
        return shot

    @staticmethod
    async def delete_shot(db: AsyncSession, shot: Shot) -> None:
        """Delete a shot."""
        await db.delete(shot)
        await db.flush()

    # ── Ownership verification helpers ────────────────────────────────────

    @staticmethod
    async def verify_scene_ownership(
        db: AsyncSession, scene_id: uuid.UUID, user: User
    ) -> Scene:
        """
        Fetch a scene and verify that the parent project is owned by *user*.

        Returns the Scene on success; raises 403/404 otherwise.
        """
        result = await db.execute(select(Scene).where(Scene.id == scene_id))
        scene = result.scalar_one_or_none()
        if scene is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Scene not found.")

        project_result = await db.execute(
            select(Project).where(Project.id == scene.project_id)
        )
        project = project_result.scalar_one_or_none()
        if project is None or project.user_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied.")
        return scene

    @staticmethod
    async def verify_shot_ownership(
        db: AsyncSession, shot_id: uuid.UUID, user: User
    ) -> Shot:
        """
        Fetch a shot and walk up the ownership chain (shot → scene → project → user).

        Returns the Shot on success; raises 403/404 otherwise.
        """
        result = await db.execute(select(Shot).where(Shot.id == shot_id))
        shot = result.scalar_one_or_none()
        if shot is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Shot not found.")

        scene_result = await db.execute(
            select(Scene).where(Scene.id == shot.scene_id)
        )
        scene = scene_result.scalar_one_or_none()
        if scene is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent scene not found.")

        project_result = await db.execute(
            select(Project).where(Project.id == scene.project_id)
        )
        project = project_result.scalar_one_or_none()
        if project is None or project.user_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied.")
        return shot
