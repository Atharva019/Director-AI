"""SceneAnalysis ORM model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class SceneAnalysis(Base):
    """
    Result of an AI-powered analysis of a film still / reference image.
    May optionally be attached to a specific scene.
    """

    __tablename__ = "scene_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scene_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    analysis_result: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    model_used: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────
    scene: Mapped["Scene | None"] = relationship("Scene", back_populates="analyses")  # noqa: F821
    user: Mapped["User"] = relationship("User", back_populates="analyses")  # noqa: F821

    def __repr__(self) -> str:
        return f"<SceneAnalysis {self.id} model={self.model_used}>"
