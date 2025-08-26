from fastapi import Depends, HTTPException, status
from typing import Callable
from app.models import User
from app.auth_deps import get_current_user  # було app.auth

def require_superuser(user: User = Depends(get_current_user)) -> User:
    if not user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    return user

def require_min_level(min_level: int) -> Callable:
    def checker(user: User = Depends(get_current_user)) -> User:
        if (user.lvl_user or 0) < min_level and not user.is_superuser:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient level")
        return user
    return checker
