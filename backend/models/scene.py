"""Scene ORM model."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class LocationType(str, enum.Enum):
    """Interior vs. exterior location."""

    INTERIOR = "interior"
    EXTERIOR = "exterior"
    BOTH = "both"


class TimeOfDay(str, enum.Enum):
    """Lighting time classification."""

    DAWN = "dawn"
    MORNING = "morning"
    DAY = "day"
    AFTERNOON = "afternoon"
    GOLDEN_HOUR = "golden_hour"
    DUSK = "dusk"
    NIGHT = "night"
    BLUE_HOUR = "blue_hour"


class Scene(Base):
    """A scene within a filmmaking project."""

    __tablename__ = "scenes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    location_type: Mapped[LocationType] = mapped_column(
        SAEnum(LocationType, name="location_type", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    time_of_day: Mapped[TimeOfDay] = mapped_column(
        SAEnum(TimeOfDay, name="time_of_day", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    mood: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────
    project: Mapped["Project"] = relationship("Project", back_populates="scenes")  # noqa: F821
    shots: Mapped[list["Shot"]] = relationship(  # noqa: F821
        "Shot", back_populates="scene", lazy="selectin", cascade="all, delete-orphan"
    )
    analyses: Mapped[list["SceneAnalysis"]] = relationship(  # noqa: F821
        "SceneAnalysis", back_populates="scene", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Scene {self.scene_number}: {self.title!r}>"
