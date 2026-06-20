"""
Auth routes — registration, login, token refresh, profile.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.models.billing import Billing, BillingPlan
from backend.app.schemas.user import (
    UserRegister, UserLogin, UserUpdate, UserResponse,
    Token, TokenRefresh, ChangePassword,
)
from backend.app.utils.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Register ─────────────────────────────────────────────
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        company_name=data.company_name,
        role=UserRole.USER,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    # Create default billing record
    billing = Billing(
        user_id=user.id,
        plan=BillingPlan.FREE,
    )
    db.add(billing)
    await db.flush()

    return user


# ── Login ────────────────────────────────────────────────
@router.post("/login", response_model=Token)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended. Contact admin.",
        )

    access_token = create_access_token(str(user.id), user.role)
    refresh_token = create_refresh_token(str(user.id), user.role)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ── Refresh Token ────────────────────────────────────────
@router.post("/refresh", response_model=Token)
async def refresh_token(
    data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
):
    """Refresh an expired access token using a valid refresh token."""
    payload = decode_token(data.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    role = payload.get("role")

    access_token = create_access_token(user_id, role)
    new_refresh_token = create_refresh_token(user_id, role)

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


# ── Get Current User Profile ────────────────────────────
@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Get the authenticated user's profile."""
    return current_user


# ── Update Profile ───────────────────────────────────────
@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.add(current_user)
    await db.flush()
    return current_user


# ── Change Password ──────────────────────────────────────
@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the authenticated user's password."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(data.new_password)
    db.add(current_user)
    await db.flush()

    return {"message": "Password changed successfully"}
