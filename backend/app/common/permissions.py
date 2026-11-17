from fastapi import HTTPException, status

from app.modules.users.models import User, UserRole


def require_owner(user: User) -> None:
    if user.role != UserRole.owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner permission required")


def require_active(user: User) -> None:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")