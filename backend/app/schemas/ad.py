"""
Pydantic schemas for Ad endpoints.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ── Request Schemas ──────────────────────────────────────

class AdCreate(BaseModel):
    """Create ad request."""
    headline: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    cta_text: str | None = Field(None, max_length=50)
    destination_url: str | None = None
    media_type: str | None = None
    platform_specific_data: dict | None = None


class AdUpdate(BaseModel):
    """Update ad request."""
    headline: str | None = None
    description: str | None = None
    cta_text: str | None = None
    destination_url: str | None = None
    media_type: str | None = None
    platform_specific_data: dict | None = None


# ── Response Schemas ─────────────────────────────────────

class AdResponse(BaseModel):
    """Ad response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    headline: str
    description: str | None
    cta_text: str | None
    destination_url: str | None
    media_url: str | None
    media_type: str | None
    status: str
    rejection_reason: str | None
    platform_specific_data: dict | None
    created_at: datetime
    updated_at: datetime


class AdListResponse(BaseModel):
    """Paginated ad list."""
    ads: list[AdResponse]
    total: int
    page: int
    page_size: int
