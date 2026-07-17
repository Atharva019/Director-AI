"""
Firebase Admin SDK initialisation and token verification.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

from config import get_settings

logger = logging.getLogger(__name__)

_firebase_app: Optional[firebase_admin.App] = None


def _load_credential():
    """Prefer the JSON env var (production); fall back to the file path."""
    settings = get_settings()
    if settings.FIREBASE_SERVICE_ACCOUNT_JSON.strip():
        info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
        return credentials.Certificate(info)
    return credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)


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
    credential_configured = bool(settings.FIREBASE_SERVICE_ACCOUNT_JSON.strip()) or os.path.exists(
        settings.FIREBASE_CREDENTIALS_PATH
    )

    try:
        cred = _load_credential()
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized from configured credential.")
        return
    except Exception:
        if credential_configured:
            # A credential WAS configured but failed to load - this is a real
            # misconfiguration (bad JSON, missing file, invalid cert, etc.),
            # not the "no credential at all" dev case. Surface the real error.
            logger.error(
                "Firebase credential is configured but failed to load.",
                exc_info=True,
            )
            if settings.is_production:
                # Fail fast at startup rather than silently booting with
                # auth disabled.
                raise
        else:
            # In development / CI you may not have a credentials file.
            # Fall back to Application Default Credentials or skip.
            logger.warning(
                "Firebase credentials not found/invalid – "
                "auth verification will be unavailable."
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
