"""
Users router.
User profile management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.models.user import UserInDB, UserResponse, UserUpdate
from app.repositories.user_repository import UserRepository
from app.core.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])

DB_NAME = "volunteer_signup"

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get current user's profile.
    
    **Authentication:** Required (JWT)
    
    **Returns:**
    - 200: User profile data
    - 401: Unauthorized (invalid or missing token)
    
    **Privacy Note:**
    - Returns user's own data including roles and consent flags
    - Password hash is never exposed
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UserUpdate,
    current_user: UserInDB = Depends(get_current_user),
    db: DB_NAME = Depends(get_db)
):
    """
    Update current user's profile.
    
    **Authentication:** Required (JWT)
    
    **Allowed Updates:**
    - name: Update full name
    - phone: Update phone number (must be unique)
    
    **Cannot Update:**
    - email (contact admin to change)
    - age_band (fixed at registration for compliance)
    - roles (admin only)
    
    **Request Body:**
    All fields optional for partial update
    
    **Returns:**
    - 200: Updated profile
    - 400: Validation error or duplicate phone
    - 401: Unauthorized
    """
    repo = UserRepository(db)
    
    # If phone is being updated, check for duplicates
    if update_data.phone:
        existing_phone = await repo.get_user_by_phone(update_data.phone)
        if existing_phone and existing_phone.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already in use"
            )
    
    # Update user
    updated_user = await repo.update_user(current_user.id, update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    
    logger.info(f"User profile updated: {current_user.id}")
    
    return updated_user