"""
Ad model — individual advertisements within a campaign.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base
import enum


class AdStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    LIVE = "live"
    PAUSED = "paused"
    ARCHIVED = "archived"


class MediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    TEXT_ONLY = "text_only"


class Ad(Base):
    __tablename__ = "ads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cta_text: Mapped[str | None] = mapped_column(String(50), nullable=True)
    destination_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    media_type: Mapped[str | None] = mapped_column(
        SAEnum(MediaType, name="media_type", create_constraint=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(AdStatus, name="ad_status", create_constraint=True),
        default=AdStatus.DRAFT,
        nullable=False,
        index=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    platform_specific_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="ads")
    ad_platforms: Mapped[list["AdPlatform"]] = relationship(
        "AdPlatform", back_populates="ad", cascade="all, delete-orphan"
    )
    analytics: Mapped[list["Analytics"]] = relationship(
        "Analytics", back_populates="ad", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Ad '{self.headline}' ({self.status})>"
