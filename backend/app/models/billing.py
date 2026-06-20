"""
Billing model — user subscription and payment details.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base
import enum


class BillingPlan(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Billing(Base):
    __tablename__ = "billing"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    plan: Mapped[str] = mapped_column(
        SAEnum(BillingPlan, name="billing_plan", create_constraint=True),
        default=BillingPlan.FREE,
        nullable=False,
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    billing_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    next_billing_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="billing")

    def __repr__(self) -> str:
        return f"<Billing {self.plan} balance={self.balance}>"
