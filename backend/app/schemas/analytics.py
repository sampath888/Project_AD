"""
Pydantic schemas for Analytics endpoints.
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class AnalyticsResponse(BaseModel):
    """Single analytics record."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ad_id: uuid.UUID
    platform: str
    impressions: int
    clicks: int
    conversions: int
    spend: Decimal
    ctr: Decimal
    cpc: Decimal
    metric_date: date
    synced_at: datetime


class DashboardSummary(BaseModel):
    """Dashboard KPI summary for a user."""
    total_campaigns: int
    active_campaigns: int
    total_ads: int
    live_ads: int
    total_spend: Decimal
    total_impressions: int
    total_clicks: int
    total_conversions: int
    avg_ctr: Decimal
    avg_cpc: Decimal


class PlatformBreakdown(BaseModel):
    """Analytics breakdown by platform."""
    platform: str
    impressions: int
    clicks: int
    conversions: int
    spend: Decimal
    ctr: Decimal


class CampaignAnalytics(BaseModel):
    """Analytics for a single campaign."""
    campaign_id: uuid.UUID
    campaign_name: str
    total_impressions: int
    total_clicks: int
    total_conversions: int
    total_spend: Decimal
    avg_ctr: Decimal
    avg_cpc: Decimal
    platform_breakdown: list[PlatformBreakdown]
    daily_metrics: list[AnalyticsResponse]
