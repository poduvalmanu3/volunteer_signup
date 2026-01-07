"""
Registrations router.
Volunteer registration for cleanup drives.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import UserInDB
from app.models.registration import (
    RegistrationCreate,
    RegistrationResponse,
    MyRegistrationsResponse
)
from app.repositories.registration_repository import RegistrationRepository
from app.repositories.drive_repository import DriveRepository
from app.core.dependencies import get_current_user
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/registrations", tags=["Registrations"])

DB_NAME = "volunteer_signup"

@router.post("/", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_for_drive(
    registration_data: RegistrationCreate,
    current_user: UserInDB = Depends(get_current_user),
    db: DB_NAME = Depends(get_db)
):
    """
    Register current user for a cleanup drive.
    
    **Authentication:** Required (JWT)
    
    **Request Body:**
    - drive_id: ID of drive to register for
    
    **Returns:**
    - 201: Registration successful
    - 400: Already registered or registration closed
    - 404: Drive not found
    - 409: Drive at capacity
    
    **Business Rules:**
    - Cannot register for same drive twice
    - Registration closes N hours before drive (configurable)
    - Cannot register if drive at max capacity
    - Cannot register for past drives
    - Registration must be for published drives only
    """
    reg_repo = RegistrationRepository(db)
    drive_repo = DriveRepository(db)
    
    # Get drive details
    drive = await drive_repo.get_drive_by_id(registration_data.drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drive not found"
        )
    
    # Check if drive is published
    if drive.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only register for published drives"
        )
    
    # Check if registration is open
    if not drive.registration_open:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration is closed for this drive"
        )
    
    # Check registration deadline
    deadline = drive.date_time - timedelta(hours=settings.REGISTRATION_DEADLINE_HOURS)
    if datetime.utcnow() >= deadline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration closed {settings.REGISTRATION_DEADLINE_HOURS} hours before drive"
        )
    
    # Check if already registered
    existing = await reg_repo.get_registration(
        registration_data.drive_id,
        current_user.id
    )
    if existing and existing.status != "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already registered for this drive"
        )
    
    # Check capacity
    if drive.current_volunteers >= drive.max_volunteers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Drive has reached maximum capacity"
        )
    
    # Create registration
    try:
        registration = await reg_repo.create_registration(
            registration_data.drive_id,
            current_user.id
        )
        
        # Increment volunteer count
        await drive_repo.update_volunteer_count(registration_data.drive_id, 1)
        
        # Auto-close registration if at capacity
        if drive.current_volunteers + 1 >= drive.max_volunteers:
            await drive_repo.close_registration(registration_data.drive_id)
            logger.info(f"Auto-closed registration for drive {registration_data.drive_id} (capacity reached)")
        
        logger.info(f"User {current_user.id} registered for drive {registration_data.drive_id}")
        
        return registration
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create registration"
        )


@router.get("/my", response_model=MyRegistrationsResponse)
async def get_my_registrations(
    current_user: UserInDB = Depends(get_current_user),
    db: DB_NAME = Depends(get_db)
):
    """
    Get all registrations for current user.
    
    **Authentication:** Required (JWT)
    
    **Returns:**
    - 200: List of user's registrations with drive details
    - 401: Unauthorized
    
    **Response includes:**
    - Registration status and dates
    - Drive details (title, date, location)
    - Sorted by drive date (newest first)
    """
    repo = RegistrationRepository(db)
    
    registrations = await repo.get_user_registrations(current_user.id)
    
    return MyRegistrationsResponse(
        registrations=registrations,
        total=len(registrations)
    )


@router.delete("/{registration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_registration(
    registration_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db: DB_NAME = Depends(get_db)
):
    """
    Cancel a registration.
    
    **Authentication:** Required (JWT)
    
    **Path Parameters:**
    - registration_id: Registration ID to cancel
    
    **Returns:**
    - 204: Registration cancelled successfully
    - 403: Not authorized (not your registration)
    - 404: Registration not found
    - 400: Cannot cancel (drive already started)
    
    **Business Rules:**
    - Can only cancel your own registrations
    - Cannot cancel after drive has started
    - Decrements volunteer count
    - Reopens registration if was at capacity
    """
    reg_repo = RegistrationRepository(db)
    drive_repo = DriveRepository(db)
    
    # Get registration
    registration = await reg_repo.get_registration_by_id(registration_id)
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found"
        )
    
    # Check authorization
    if registration.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this registration"
        )
    
    # Get drive to check if it's started
    drive = await drive_repo.get_drive_by_id(registration.drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drive not found"
        )
    
    # Check if drive has started
    if datetime.utcnow() >= drive.date_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel registration after drive has started"
        )
    
    # Delete registration
    deleted = await reg_repo.delete_registration(registration_id)
    
    if deleted:
        # Decrement volunteer count
        await drive_repo.update_volunteer_count(registration.drive_id, -1)
        
        logger.info(f"Registration {registration_id} cancelled by user {current_user.id}")
    
    return None