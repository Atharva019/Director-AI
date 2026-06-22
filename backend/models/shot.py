"""Shot ORM model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Shot(Base):
    """An individual shot within a scene."""

    __tablename__ = "shots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    shot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    shot_type: Mapped[str] = mapped_column(
        String(100), nullable=False, default=""
    )  # e.g. wide, close-up, medium
    camera_angle: Mapped[str] = mapped_column(
        String(100), nullable=False, default=""
    )  # e.g. eye-level, low-angle, high-angle
    camera_movement: Mapped[str] = mapped_column(
        String(100), nullable=False, default=""
    )  # e.g. static, dolly, pan, tilt
    lens_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────
    scene: Mapped["Scene"] = relationship("Scene", back_populates="shots")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Shot {self.shot_number}: {self.shot_type}>"
