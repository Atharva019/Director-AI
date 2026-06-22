"""
Authentication router – Firebase user sync and profile retrieval.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middleware import get_current_user
from db.database import get_db
from models.user import User
from schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/sync", response_model=UserResponse, status_code=200)
async def sync_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Sync the authenticated Firebase user to the database.

    This endpoint is called by the frontend after a successful Firebase
    sign-in.  The ``get_current_user`` dependency already handles
    lookup-or-create, so this simply returns the resulting user.
    """
    return current_user


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return the currently authenticated user's profile."""
    return current_user
