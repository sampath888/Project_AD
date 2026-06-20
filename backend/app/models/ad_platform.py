"""
AdPlatform model — tracks where each ad is published.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base
import enum


class PlatformName(str, enum.Enum):
    GOOGLE = "google"
    META = "meta"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"


class PublishStatus(str, enum.Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"
    REMOVED = "removed"


class AdPlatform(Base):
    __tablename__ = "ad_platforms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ad_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ads.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    platform: Mapped[str] = mapped_column(
        SAEnum(PlatformName, name="platform_name", create_constraint=True),
        nullable=False,
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publish_status: Mapped[str] = mapped_column(
        SAEnum(PublishStatus, name="publish_status", create_constraint=True),
        default=PublishStatus.PENDING,
        nullable=False,
    )
    api_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # ── Relationships ────────────────────────────────────
    ad: Mapped["Ad"] = relationship("Ad", back_populates="ad_platforms")

    def __repr__(self) -> str:
        return f"<AdPlatform {self.platform} ({self.publish_status})>"
