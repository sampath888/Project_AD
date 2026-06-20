"""
Pydantic schemas for Campaign endpoints.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


# ── Request Schemas ──────────────────────────────────────

class CampaignCreate(BaseModel):
    """Create campaign request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    objective: str = Field(default="awareness")
    daily_budget: Decimal | None = Field(None, ge=0)
    total_budget: Decimal | None = Field(None, ge=0)
    start_date: datetime | None = None
    end_date: datetime | None = None
    targeting: dict | None = None


class CampaignUpdate(BaseModel):
    """Update campaign request."""
    name: str | None = None
    description: str | None = None
    objective: str | None = None
    status: str | None = None
    daily_budget: Decimal | None = None
    total_budget: Decimal | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    targeting: dict | None = None


class CampaignPublish(BaseModel):
    """Publish campaign to platforms."""
    platforms: list[str] = Field(..., min_length=1)


# ── Response Schemas ─────────────────────────────────────

class CampaignResponse(BaseModel):
    """Campaign response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None
    objective: str
    status: str
    daily_budget: Decimal | None
    total_budget: Decimal | None
    spent_amount: Decimal
    start_date: datetime | None
    end_date: datetime | None
    targeting: dict | None
    created_at: datetime
    updated_at: datetime


class CampaignListResponse(BaseModel):
    """Paginated campaign list."""
    campaigns: list[CampaignResponse]
    total: int
    page: int
    page_size: int
