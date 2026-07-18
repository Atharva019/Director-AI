"""API routers package."""

from routers.auth import router as auth_router
from routers.projects import router as projects_router
from routers.scenes import router as scenes_router
from routers.shots import router as shots_router
from routers.analysis import router as analysis_router
from routers.waitlist import router as waitlist_router

__all__ = [
    "auth_router",
    "projects_router",
    "scenes_router",
    "shots_router",
    "analysis_router",
    "waitlist_router",
]
