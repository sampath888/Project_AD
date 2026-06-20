"""
Pydantic schemas for User endpoints.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ── Request Schemas ──────────────────────────────────────

class UserRegister(BaseModel):
    """Registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    company_name: str | None = None


class UserLogin(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Profile update request."""
    full_name: str | None = None
    company_name: str | None = None
    avatar_url: str | None = None
    profile_data: dict | None = None


class ChangePassword(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ── Response Schemas ─────────────────────────────────────

class UserResponse(BaseModel):
    """Public user profile response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    company_name: str | None
    role: str
    is_active: bool
    is_verified: bool
    avatar_url: str | None
    created_at: datetime


class UserListResponse(BaseModel):
    """Paginated user list."""
    users: list[UserResponse]
    total: int
    page: int
    page_size: int


# ── Auth Schemas ─────────────────────────────────────────

class Token(BaseModel):
    """JWT token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Refresh token request."""
    refresh_token: str


class TokenPayload(BaseModel):
    """Decoded JWT payload."""
    sub: str  # user id
    role: str
    exp: int
