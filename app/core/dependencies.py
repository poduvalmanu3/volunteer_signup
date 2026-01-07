"""
FastAPI dependencies for authentication and authorization.
Implements role-based access control (RBAC) with JWT tokens.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import uuid
import logging

from app.core.security import decode_token
from app.database import get_db
from app.models.user import UserInDB

logger = logging.getLogger(__name__)

# OAuth2 scheme for JWT token extraction
# tokenUrl points to the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DB_NAME = "volunteer_signup"

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: DB_NAME = Depends(get_db)
) -> UserInDB:
    """
    Dependency to get currently authenticated user from JWT token.
    
    Args:
        token: JWT access token from Authorization header
        db: Database instance
        
    Returns:
        UserInDB: Current authenticated user
        
    Raises:
        HTTPException 401: If token is invalid or user not found
        
    Security Notes:
        - Validates JWT signature and expiration
        - Checks if user still exists and is active
        - Used on all protected endpoints
    """
    # Decode and validate JWT token
    payload = decode_token(token)
    
    # Extract user_id from token payload
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    user_dict = await db.users.find_one({"_id": user_id})
    if user_dict is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Parse user data
    user = UserInDB(**user_dict)
    
    # Check if user account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Dependency to ensure user is active.
    Alias for get_current_user with explicit active check.
    """
    return current_user


def require_role(allowed_roles: list[str]):
    """
    Dependency factory for role-based access control.
    
    Args:
        allowed_roles: List of roles allowed to access endpoint
        
    Returns:
        Dependency function that checks user role
        
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: UserInDB = Depends(require_role(["admin"]))):
            ...
    
    Security Notes:
        - Implements least privilege principle
        - Roles checked after authentication
        - Returns 403 Forbidden for insufficient permissions
    """
    async def check_role(
        current_user: UserInDB = Depends(get_current_user)
    ) -> UserInDB:
        """Check if user has required role."""
        user_roles = set(current_user.roles)
        allowed = set(allowed_roles)
        
        if not user_roles.intersection(allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}"
            )
        
        return current_user
    
    return check_role


# Convenience dependencies for common role checks
require_organizer = require_role(["organizer", "admin"])
require_admin = require_role(["admin"])


async def add_request_id(request: Request):
    """
    Middleware dependency to add unique request ID for logging.
    
    Args:
        request: FastAPI request object
        
    Note:
        Request ID is used for structured logging and tracing.
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    return request_id


def get_request_id(request: Request) -> str:
    """
    Get request ID from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Request ID for logging
    """
    return getattr(request.state, "request_id", "unknown")