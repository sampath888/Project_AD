"""
Campaign CRUD routes.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.campaign import Campaign, CampaignStatus
from backend.app.schemas.campaign import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    CampaignListResponse, CampaignPublish,
)
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


# ── List Campaigns ───────────────────────────────────────
@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's campaigns with optional status filter."""
    query = select(Campaign).where(Campaign.user_id == current_user.id)

    if status_filter:
        query = query.where(Campaign.status == status_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
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


# ── Create Campaign ─────────────────────────────────────
@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new campaign."""
    campaign = Campaign(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        objective=data.objective,
        daily_budget=data.daily_budget,
        total_budget=data.total_budget,
        start_date=data.start_date,
        end_date=data.end_date,
        targeting=data.targeting,
        status=CampaignStatus.DRAFT,
    )
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)
    return campaign


# ── Get Campaign ─────────────────────────────────────────
@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific campaign by ID."""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id,
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


# ── Update Campaign ──────────────────────────────────────
@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: uuid.UUID,
    data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing campaign."""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id,
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(campaign, field, value)

    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)
    return campaign


# ── Delete Campaign ──────────────────────────────────────
@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a campaign and all its ads."""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id,
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status == CampaignStatus.ACTIVE.value:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete an active campaign. Pause it first.",
        )

    await db.delete(campaign)
    await db.flush()


# ── Pause Campaign ───────────────────────────────────────
@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pause an active campaign."""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id,
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status != CampaignStatus.ACTIVE.value:
        raise HTTPException(status_code=400, detail="Campaign is not active")

    campaign.status = CampaignStatus.PAUSED
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)
    return campaign


# ── Publish Campaign ────────────────────────────────────
@router.post("/{campaign_id}/publish", response_model=CampaignResponse)
async def publish_campaign(
    campaign_id: uuid.UUID,
    data: CampaignPublish,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish a campaign to selected ad platforms."""
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.user_id == current_user.id,
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status not in (CampaignStatus.DRAFT.value, CampaignStatus.PAUSED.value):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot publish campaign with status '{campaign.status}'",
        )

    # TODO: Trigger Celery task to publish ads to selected platforms
    # For now, just change status to pending
    campaign.status = CampaignStatus.PENDING
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)

    return campaign
