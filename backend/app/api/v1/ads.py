"""
Ad CRUD routes.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.campaign import Campaign
from backend.app.models.ad import Ad, AdStatus
from backend.app.schemas.ad import (
    AdCreate, AdUpdate, AdResponse, AdListResponse,
)
from backend.app.api.deps import get_current_user

router = APIRouter(tags=["Ads"])


# ── Helper: verify campaign ownership ────────────────────
async def _get_user_campaign(
    campaign_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> Campaign:
    """Fetch a campaign and verify it belongs to the user."""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id,
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


# ── List Ads in Campaign ────────────────────────────────
@router.get(
    "/campaigns/{campaign_id}/ads",
    response_model=AdListResponse,
)
async def list_ads(
    campaign_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all ads in a campaign."""
    await _get_user_campaign(campaign_id, current_user, db)

    query = select(Ad).where(Ad.campaign_id == campaign_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Ad.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    ads = result.scalars().all()

    return AdListResponse(
        ads=[AdResponse.model_validate(a) for a in ads],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── Create Ad ───────────────────────────────────────────
@router.post(
    "/campaigns/{campaign_id}/ads",
    response_model=AdResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ad(
    campaign_id: uuid.UUID,
    data: AdCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new ad in a campaign."""
    await _get_user_campaign(campaign_id, current_user, db)

    ad = Ad(
        campaign_id=campaign_id,
        headline=data.headline,
        description=data.description,
        cta_text=data.cta_text,
        destination_url=data.destination_url,
        media_type=data.media_type,
        platform_specific_data=data.platform_specific_data,
        status=AdStatus.DRAFT,
    )
    db.add(ad)
    await db.flush()
    await db.refresh(ad)
    return ad


# ── Get Ad ──────────────────────────────────────────────
@router.get("/ads/{ad_id}", response_model=AdResponse)
async def get_ad(
    ad_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific ad by ID."""
    result = await db.execute(
        select(Ad).join(Campaign).where(
            Ad.id == ad_id,
            Campaign.user_id == current_user.id,
        )
    )
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    return ad


# ── Update Ad ───────────────────────────────────────────
@router.put("/ads/{ad_id}", response_model=AdResponse)
async def update_ad(
    ad_id: uuid.UUID,
    data: AdUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an ad."""
    result = await db.execute(
        select(Ad).join(Campaign).where(
            Ad.id == ad_id,
            Campaign.user_id == current_user.id,
        )
    )
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    if ad.status in (AdStatus.LIVE.value,):
        raise HTTPException(
            status_code=400,
            detail="Cannot edit a live ad. Pause it first.",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ad, field, value)

    db.add(ad)
    await db.flush()
    await db.refresh(ad)
    return ad


# ── Delete Ad ───────────────────────────────────────────
@router.delete("/ads/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ad(
    ad_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an ad."""
    result = await db.execute(
        select(Ad).join(Campaign).where(
            Ad.id == ad_id,
            Campaign.user_id == current_user.id,
        )
    )
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    if ad.status == AdStatus.LIVE.value:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a live ad. Pause or archive it first.",
        )

    await db.delete(ad)
    await db.flush()


# ── Submit Ad for Approval ──────────────────────────────
@router.post("/ads/{ad_id}/submit", response_model=AdResponse)
async def submit_ad_for_approval(
    ad_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a draft ad for admin approval."""
    result = await db.execute(
        select(Ad).join(Campaign).where(
            Ad.id == ad_id,
            Campaign.user_id == current_user.id,
        )
    )
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    if ad.status != AdStatus.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail=f"Ad must be in draft status to submit. Current: {ad.status}",
        )

    ad.status = AdStatus.PENDING_APPROVAL
    db.add(ad)
    await db.flush()
    await db.refresh(ad)
    return ad
