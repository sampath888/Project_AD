"""
Admin routes — user management, ad moderation, global analytics.
"""

import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from backend.app.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.models.campaign import Campaign, CampaignStatus
from backend.app.models.ad import Ad, AdStatus
from backend.app.models.analytics import Analytics
from backend.app.models.notification import Notification, NotificationType
from backend.app.schemas.user import UserResponse, UserListResponse
from backend.app.schemas.campaign import CampaignResponse, CampaignListResponse
from backend.app.schemas.ad import AdResponse, AdListResponse
from backend.app.schemas.analytics import DashboardSummary
from backend.app.api.deps import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  USER MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role_filter: str | None = Query(None, alias="role"),
    search: str | None = Query(None),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users with optional filters."""
    query = select(User)

    if role_filter:
        query = query.where(User.role == role_filter)

    if search:
        query = query.where(
            User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%")
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: uuid.UUID,
    new_role: str = Query(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Change a user's role (admin/super_admin only)."""
    if new_role not in [r.value for r in UserRole]:
        raise HTTPException(status_code=400, detail=f"Invalid role: {new_role}")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    user.role = new_role
    db.add(user)
    await db.flush()

    return {"message": f"User role changed to {new_role}"}


@router.put("/users/{user_id}/suspend")
async def suspend_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Suspend a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot suspend yourself")

    user.is_active = not user.is_active  # Toggle
    db.add(user)
    await db.flush()

    status_text = "activated" if user.is_active else "suspended"
    return {"message": f"User {status_text}", "is_active": user.is_active}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CAMPAIGN MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/campaigns", response_model=CampaignListResponse)
async def list_all_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all campaigns across all users."""
    query = select(Campaign)

    if status_filter:
        query = query.where(Campaign.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Campaign.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    campaigns = result.scalars().all()

    return CampaignListResponse(
        campaigns=[CampaignResponse.model_validate(c) for c in campaigns],
        total=total,
        page=page,
        page_size=page_size,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AD MODERATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/ads/pending", response_model=AdListResponse)
async def list_pending_ads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List ads pending approval."""
    query = select(Ad).where(Ad.status == AdStatus.PENDING_APPROVAL.value)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Ad.created_at.asc())  # FIFO
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    ads = result.scalars().all()

    return AdListResponse(
        ads=[AdResponse.model_validate(a) for a in ads],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.put("/ads/{ad_id}/approve", response_model=AdResponse)
async def approve_ad(
    ad_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve an ad for publishing."""
    result = await db.execute(select(Ad).where(Ad.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    if ad.status != AdStatus.PENDING_APPROVAL.value:
        raise HTTPException(status_code=400, detail="Ad is not pending approval")

    ad.status = AdStatus.APPROVED
    ad.rejection_reason = None
    db.add(ad)

    # Notify the ad owner
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == ad.campaign_id)
    )
    campaign = campaign_result.scalar_one_or_none()
    if campaign:
        notification = Notification(
            user_id=campaign.user_id,
            type=NotificationType.AD_APPROVAL,
            title="Ad Approved",
            message=f'Your ad "{ad.headline}" has been approved and is ready to go live.',
            link=f"/campaigns/{campaign.id}/ads/{ad.id}",
        )
        db.add(notification)

    await db.flush()
    await db.refresh(ad)
    return ad


@router.put("/ads/{ad_id}/reject", response_model=AdResponse)
async def reject_ad(
    ad_id: uuid.UUID,
    reason: str = Query(..., min_length=1),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reject an ad with a reason."""
    result = await db.execute(select(Ad).where(Ad.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    if ad.status != AdStatus.PENDING_APPROVAL.value:
        raise HTTPException(status_code=400, detail="Ad is not pending approval")

    ad.status = AdStatus.REJECTED
    ad.rejection_reason = reason
    db.add(ad)

    # Notify the ad owner
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == ad.campaign_id)
    )
    campaign = campaign_result.scalar_one_or_none()
    if campaign:
        notification = Notification(
            user_id=campaign.user_id,
            type=NotificationType.AD_REJECTION,
            title="Ad Rejected",
            message=f'Your ad "{ad.headline}" was rejected. Reason: {reason}',
            link=f"/campaigns/{campaign.id}/ads/{ad.id}",
        )
        db.add(notification)

    await db.flush()
    await db.refresh(ad)
    return ad


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GLOBAL ANALYTICS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/analytics/global", response_model=DashboardSummary)
async def global_analytics(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get platform-wide analytics summary."""
    total_campaigns = (await db.execute(
        select(func.count()).select_from(Campaign)
    )).scalar() or 0

    active_campaigns = (await db.execute(
        select(func.count()).where(Campaign.status == CampaignStatus.ACTIVE.value)
    )).scalar() or 0

    total_ads = (await db.execute(
        select(func.count()).select_from(Ad)
    )).scalar() or 0

    live_ads = (await db.execute(
        select(func.count()).where(Ad.status == AdStatus.LIVE.value)
    )).scalar() or 0

    # Aggregate analytics
    analytics_query = select(
        func.coalesce(func.sum(Analytics.spend), 0).label("total_spend"),
        func.coalesce(func.sum(Analytics.impressions), 0).label("total_impressions"),
        func.coalesce(func.sum(Analytics.clicks), 0).label("total_clicks"),
        func.coalesce(func.sum(Analytics.conversions), 0).label("total_conversions"),
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
