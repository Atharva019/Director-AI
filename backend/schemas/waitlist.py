"""Pydantic schemas for the Pro-tier waitlist."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class WaitlistCreate(BaseModel):
    email: EmailStr
    source: str = "app"


class WaitlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    created_at: datetime
