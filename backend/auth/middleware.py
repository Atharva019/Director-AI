"""
FastAPI dependency that extracts and verifies a Firebase Bearer token,
then resolves (or creates) the corresponding database User.
"""

import logging
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.firebase import verify_id_token
from db.database import get_db
from models.user import User

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that:
    1. Extracts the Bearer token from the Authorization header.
    2. Verifies it with Firebase Admin SDK.
    3. Looks up the user in PostgreSQL by ``firebase_uid``.
    4. If the user doesn't exist yet, creates a new row (first-login sync).
    5. Returns the ORM ``User`` object for downstream handlers.

    Raises
    ------
    HTTPException 401
        If no token is provided or the token is invalid / expired.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # ── Verify with Firebase ──────────────────────────────────────────────
    try:
        decoded: Dict[str, Any] = verify_id_token(token)
    except RuntimeError:
        # Firebase SDK not initialised (dev mode) – reject all requests.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is unavailable.",
        )
    except Exception as exc:
        logger.warning("Token verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    firebase_uid: str = decoded["uid"]

    # ── Lookup or create user ─────────────────────────────────────────────
    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            firebase_uid=firebase_uid,
            email=decoded.get("email", f"{firebase_uid}@firebase.local"),
            display_name=decoded.get("name", ""),
            avatar_url=decoded.get("picture"),
        )
        db.add(user)
        await db.flush()
        logger.info("Auto-created user %s for firebase_uid=%s", user.id, firebase_uid)

    return user
