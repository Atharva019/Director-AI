"""Pydantic schemas for the User model."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    """Payload received when syncing a Firebase user to the database."""

    firebase_uid: str
    email: str
    display_name: str = ""
    avatar_url: Optional[str] = None


class UserUpdate(BaseModel):
    """Fields that a user may update on their profile."""

    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(BaseModel):
    """Public representation of a user."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    firebase_uid: str
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
