"""
RBAC permission decorators and helpers.
"""

from functools import wraps
from fastapi import HTTPException, status
from backend.app.models.user import UserRole


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory that restricts access to specific roles.

    Usage in a route:
        @router.get("/admin-only")
        async def admin_view(user = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN))):
            ...

    Note: This is used as a composable check, not a direct dependency.
    See deps.py for how it integrates with get_current_user.
    """
    def checker(current_user):
        if current_user.role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(r.value for r in allowed_roles)}",
            )
        return current_user
    return checker


def is_admin(user) -> bool:
    """Check if a user has admin or super_admin role."""
    return user.role in (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value)


def is_super_admin(user) -> bool:
    """Check if a user has super_admin role."""
    return user.role == UserRole.SUPER_ADMIN.value


def is_owner_or_admin(user, resource_user_id) -> bool:
    """Check if the user owns the resource or is an admin."""
    return str(user.id) == str(resource_user_id) or is_admin(user)
