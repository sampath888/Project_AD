"""
Models package — exports all models so Alembic can auto-detect them.
"""

from backend.app.models.user import User
from backend.app.models.campaign import Campaign
from backend.app.models.ad import Ad
from backend.app.models.ad_platform import AdPlatform
from backend.app.models.analytics import Analytics
from backend.app.models.billing import Billing
from backend.app.models.notification import Notification

__all__ = [
    "User",
    "Campaign",
    "Ad",
    "AdPlatform",
    "Analytics",
    "Billing",
    "Notification",
]
