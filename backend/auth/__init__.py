"""Auth package – Firebase integration and middleware."""

from auth.firebase import verify_id_token, initialize_firebase
from auth.middleware import get_current_user

__all__ = ["verify_id_token", "initialize_firebase", "get_current_user"]
