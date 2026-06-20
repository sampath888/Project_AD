"""
Analytics routes — dashboard summary, campaign analytics.
"""

import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.campaign import Campaign, CampaignStatus
from backend.app.models.ad import Ad, AdStatus
from backend.app.models.analytics import Analytics
from backend.app.schemas.analytics import (
    DashboardSummary, CampaignAnalytics, PlatformBreakdown, AnalyticsResponse,
)
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ── Dashboard Summary ───────────────────────────────────
@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get KPI summary for the current user's dashboard."""
    # Campaign counts
    total_campaigns = (await db.execute(
        select(func.count()).where(Campaign.user_id == current_user.id)
    )).scalar() or 0

    active_campaigns = (await db.execute(
        select(func.count()).where(
            Campaign.user_id == current_user.id,
            Campaign.status == CampaignStatus.ACTIVE.value,
        )
    )).scalar() or 0

    # Ad counts
    total_ads = (await db.execute(
        select(func.count()).select_from(Ad).join(Campaign).where(
            Campaign.user_id == current_user.id,
        )
    )).scalar() or 0

    live_ads = (await db.execute(
        select(func.count()).select_from(Ad).join(Campaign).where(
            Campaign.user_id == current_user.id,
            Ad.status == AdStatus.LIVE.value,
        )
    )).scalar() or 0

    # Aggregate analytics
    analytics_query = (
        select(
            func.coalesce(func.sum(Analytics.spend), 0).label("total_spend"),
            func.coalesce(func.sum(Analytics.impressions), 0).label("total_impressions"),
            func.coalesce(func.sum(Analytics.clicks), 0).label("total_clicks"),
            func.coalesce(func.sum(Analytics.conversions), 0).label("total_conversions"),
        )
        .select_from(Analytics)
        .join(Ad)
        .join(Campaign)
        .where(Campaign.user_id == current_user.id)
    )
    row = (await db.execute(analytics_query)).one_or_none()

    total_spend = row.total_spend if row else Decimal("0.00")
    total_impressions = row.total_impressions if row else 0
    total_clicks = row.total_clicks if row else 0
    total_conversions = row.total_conversions if row else 0

    avg_ctr = Decimal(str(total_clicks / total_impressions * 100)) if total_impressions > 0 else Decimal("0.0000")
    avg_cpc = Decimal(str(total_spend / total_clicks)) if total_clicks > 0 else Decimal("0.0000")

    return DashboardSummary(
        total_campaigns=total_campaigns,
        active_campaigns=active_campaigns,
        total_ads=total_ads,
        live_ads=live_ads,
        total_spend=total_spend,
        total_impressions=total_impressions,
        total_clicks=total_clicks,
        total_conversions=total_conversions,
        avg_ctr=round(avg_ctr, 4),
        avg_cpc=round(avg_cpc, 4),
    )


# ── Campaign Analytics ──────────────────────────────────
@router.get("/campaign/{campaign_id}", response_model=CampaignAnalytics)
async def get_campaign_analytics(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics for a specific campaign."""
    # Verify ownership
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id,
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get all analytics for this campaign's ads
    analytics_result = await db.execute(
        select(Analytics)
        .join(Ad)
        .where(Ad.campaign_id == campaign_id)
        .order_by(Analytics.metric_date.desc())
    )
    all_metrics = analytics_result.scalars().all()

    # Aggregate totals
    total_impressions = sum(m.impressions for m in all_metrics)
    total_clicks = sum(m.clicks for m in all_metrics)
    total_conversions = sum(m.conversions for m in all_metrics)
    total_spend = sum(m.spend for m in all_metrics)

    avg_ctr = Decimal(str(total_clicks / total_impressions * 100)) if total_impressions > 0 else Decimal("0.0000")
    avg_cpc = Decimal(str(total_spend / total_clicks)) if total_clicks > 0 else Decimal("0.0000")

    # Platform breakdown
    platform_data = {}
    for m in all_metrics:
        if m.platform not in platform_data:
            platform_data[m.platform] = {
                "impressions": 0, "clicks": 0, "conversions": 0,
                "spend": Decimal("0.00"),
            }
        pd = platform_data[m.platform]
        pd["impressions"] += m.impressions
        pd["clicks"] += m.clicks
        pd["conversions"] += m.conversions
        pd["spend"] += m.spend

    platform_breakdown = [
        PlatformBreakdown(
            platform=platform,
            impressions=data["impressions"],
            clicks=data["clicks"],
            conversions=data["conversions"],
            spend=data["spend"],
            ctr=Decimal(str(data["clicks"] / data["impressions"] * 100)) if data["impressions"] > 0 else Decimal("0.0000"),
        )
        for platform, data in platform_data.items()
    ]

    return CampaignAnalytics(
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        total_impressions=total_impressions,
        total_clicks=total_clicks,
        total_conversions=total_conversions,
        total_spend=total_spend,
        avg_ctr=round(avg_ctr, 4),
        avg_cpc=round(avg_cpc, 4),
        platform_breakdown=platform_breakdown,
        daily_metrics=[AnalyticsResponse.model_validate(m) for m in all_metrics],
    )
