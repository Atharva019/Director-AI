"""
Firebase Admin SDK initialisation and token verification.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

from config import get_settings

logger = logging.getLogger(__name__)

_firebase_app: Optional[firebase_admin.App] = None


def initialize_firebase() -> None:
    """
    Initialize the Firebase Admin SDK using the service-account JSON
    specified in settings.  Safe to call multiple times – only the first
    call actually creates the app.
    """
    global _firebase_app
    if _firebase_app is not None:
        return

    settings = get_settings()
    cred_path = Path(settings.FIREBASE_CREDENTIALS_PATH)

    if cred_path.exists():
        cred = credentials.Certificate(str(cred_path))
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized from %s", cred_path)
    else:
        # In development / CI you may not have a credentials file.
        # Fall back to Application Default Credentials or skip.
        logger.warning(
            "Firebase credentials file not found at %s – "
            "auth verification will be unavailable.",
            cred_path,
        )
        try:
            _firebase_app = firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK initialized with default credentials.")
        except Exception:
            logger.warning("Firebase Admin SDK could not be initialized. Auth disabled.")


def verify_id_token(token: str) -> Dict[str, Any]:
    """
    Verify a Firebase ID token and return the decoded claims.

    Raises
    ------
    firebase_admin.auth.InvalidIdTokenError
        If the token is invalid or expired.
    RuntimeError
        If Firebase has not been initialised.
    """
    if _firebase_app is None:
        raise RuntimeError("Firebase Admin SDK is not initialized.")

    decoded = firebase_auth.verify_id_token(token, app=_firebase_app)
    return decoded
