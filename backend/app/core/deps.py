from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.core.security import ALGORITHM
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def require_role(allowed_roles: list[str]):
    """
    Factory function to create a dependency that enforces role-based access control.

    Args:
        allowed_roles: List of roles that are allowed to access the endpoint

    Returns:
        A dependency function that validates the user's role

    Example:
        @router.get("/admin/users", dependencies=[Depends(require_role(["ADMIN"]))])
    """
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")

        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Role information missing from token",
            )

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}",
            )

        return current_user

    return role_checker


def require_admin(current_user: dict = Depends(get_current_user)):
    """
    Dependency that enforces admin-only access.
    Convenience wrapper around require_role for the common case of admin-only endpoints.

    Usage:
        @router.get("/admin/dashboard", dependencies=[Depends(require_admin)])
    """
    user_role = current_user.get("role")

    if user_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user
