"""
Campaign model — ad campaigns with budgets, schedules, and targeting.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    String, DateTime, Numeric, ForeignKey, Text,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base
import enum


class CampaignObjective(str, enum.Enum):
    AWARENESS = "awareness"
    TRAFFIC = "traffic"
    CONVERSIONS = "conversions"
    ENGAGEMENT = "engagement"
    LEADS = "leads"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str] = mapped_column(
        SAEnum(CampaignObjective, name="campaign_objective", create_constraint=True),
        default=CampaignObjective.AWARENESS,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(CampaignStatus, name="campaign_status", create_constraint=True),
        default=CampaignStatus.DRAFT,
        nullable=False,
        index=True,
    )
    daily_budget: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    total_budget: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    spent_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    start_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    targeting: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="campaigns")
    ads: Mapped[list["Ad"]] = relationship(
        "Ad", back_populates="campaign", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Campaign {self.name} ({self.status})>"
