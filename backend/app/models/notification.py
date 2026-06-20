"""
Notification model — in-app notifications for users.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base
import enum


class NotificationType(str, enum.Enum):
    CAMPAIGN_STATUS = "campaign_status"
    BUDGET_ALERT = "budget_alert"
    AD_APPROVAL = "ad_approval"
    AD_REJECTION = "ad_rejection"
    SYSTEM = "system"
    BILLING = "billing"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    type: Mapped[str] = mapped_column(
        SAEnum(NotificationType, name="notification_type", create_constraint=True),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    link: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # ── Relationships ────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification '{self.title}' read={self.is_read}>"
