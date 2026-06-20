"""
Analytics model — per-ad, per-platform performance metrics.
"""

import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import (
    String, DateTime, Date, Integer, Numeric, ForeignKey,
    Enum as SAEnum, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base
from backend.app.models.ad_platform import PlatformName


class Analytics(Base):
    __tablename__ = "analytics"
    __table_args__ = (
        UniqueConstraint("ad_id", "platform", "metric_date", name="uq_analytics_ad_platform_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ad_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ads.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    platform: Mapped[str] = mapped_column(
        SAEnum(PlatformName, name="platform_name", create_constraint=False),
        nullable=False,
    )
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spend: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    ctr: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), default=Decimal("0.0000"), nullable=False
    )
    cpc: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("0.0000"), nullable=False
    )
    metric_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # ── Relationships ────────────────────────────────────
    ad: Mapped["Ad"] = relationship("Ad", back_populates="analytics")

    def __repr__(self) -> str:
        return f"<Analytics ad={self.ad_id} {self.platform} {self.metric_date}>"
