"""
FastAPI dependencies — current user extraction, admin checks, pagination.
"""

import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.utils.security import decode_token

# ── Bearer Token Scheme ──────────────────────────────────
security = HTTPBearer()


# ── Get Current User ─────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate JWT from Authorization header.
    Returns the authenticated User object.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Use access token.",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing user ID",
        )

    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is suspended",
        )

    return user


# ── Admin-Only Dependency ────────────────────────────────
async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require admin or super_admin role."""
    if current_user.role not in (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# ── Super Admin Dependency ───────────────────────────────
async def get_current_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require super_admin role."""
    if current_user.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return current_user
