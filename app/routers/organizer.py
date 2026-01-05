"""
Organizer router.
Endpoints for drive organizers to manage their drives and participants.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_db
from app.models.user import UserInDB
from app.models.drive import DriveListResponse
from app.models.registration import (
    AttendanceCreate,
    AttendanceResponse,
    ParticipantsListResponse,
    ParticipantResponse
)
from app.repositories.drive_repository import DriveRepository
from app.repositories.registration_repository import RegistrationRepository
from app.core.dependencies import require_organizer
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organizer", tags=["Organizer"])


@router.get("/drives", response_model=DriveListResponse)
async def get_my_drives(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: UserInDB = Depends(require_organizer),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all drives created by current organizer.
    
    **Authentication:** Required (JWT)
    **Authorization:** Organizer or Admin role
    
    **Query Parameters:**
    - page: Page number
    - page_size: Items per page (max 100)
    
    **Returns:**
    - 200: Paginated list of organizer's drives
    - 401: Unauthorized
    - 403: Insufficient permissions
    
    **Includes all statuses:**
    - draft, published, ongoing, completed, cancelled
    """
    repo = DriveRepository(db)
    
    drives, total = await repo.get_organizer_drives(
        current_user.id,
        page,
        min(page_size, settings.MAX_PAGE_SIZE)
    )
    
    # Calculate pagination metadata
    total_pages = (total + page_size - 1) // page_size
    has_next = page < total_pages
    has_prev = page > 1
    
    return DriveListResponse(
        drives=drives,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_prev=has_prev
    )


@router.get("/{drive_id}/participants", response_model=ParticipantsListResponse)
async def get_drive_participants(
    drive_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: UserInDB = Depends(require_organizer),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get participants for a drive (PRIVACY-FIRST).
    
    **Authentication:** Required (JWT)
    **Authorization:** Drive organizer or Admin
    
    **Path Parameters:**
    - drive_id: Drive ID
    
    **Query Parameters:**
    - page: Page number
    - page_size: Items per page (max 100)
    
    **Returns:**
    - 200: Paginated list of participants
    - 403: Not authorized (not drive organizer)
    - 404: Drive not found
    
    **Privacy Protection:**
    - Only shows: first_name, age_band, registration status
    - NO email, NO phone, NO full names
    - Organizers cannot export CSV (prevent data harvesting)
    - In-app messaging proxy for communication
    
    **Data Includes:**
    - registration_id: For reference
    - first_name: First name only
    - age_band: Age category
    - registration_status: confirmed/cancelled/waitlist
    - attendance_status: If attendance marked
    - hours_logged: Volunteer hours if marked
    """
    drive_repo = DriveRepository(db)
    reg_repo = RegistrationRepository(db)
    
    # Get drive
    drive = await drive_repo.get_drive_by_id(drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drive not found"
        )
    
    # Check authorization
    is_admin = "admin" in current_user.roles
    is_organizer = drive.organizer_id == current_user.id
    
    if not (is_admin or is_organizer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view participants"
        )
    
    # Get participants with minimal info
    participants_data, total = await reg_repo.get_drive_registrations(
        drive_id,
        page,
        min(page_size, settings.MAX_PAGE_SIZE)
    )
    
    # Convert to response models
    participants = []
    for p in participants_data:
        participant = ParticipantResponse(
            registration_id=str(p["registration_id"]),
            first_name=p["first_name"],
            age_band=p["age_band"],
            registration_status=p["registration_status"],
            attendance_status="attended" if p.get("attendance_status") else None,
            hours_logged=p.get("hours_logged")
        )
        participants.append(participant)
    
    # Calculate pagination metadata
    total_pages = (total + page_size - 1) // page_size
    has_next = page < total_pages
    has_prev = page > 1
    
    return ParticipantsListResponse(
        participants=participants,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_prev=has_prev
    )


@router.post("/attendance/{drive_id}/mark", response_model=AttendanceResponse)
async def mark_attendance(
    drive_id: str,
    attendance_data: AttendanceCreate,
    current_user: UserInDB = Depends(require_organizer),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Mark attendance for a volunteer.
    
    **Authentication:** Required (JWT)
    **Authorization:** Drive organizer or Admin
    
    **Path Parameters:**
    - drive_id: Drive ID
    
    **Request Body:**
    - user_id: User ID to mark attendance for
    - attended: True/False attendance status
    - hours_logged: Optional volunteer hours (0-24)
    
    **Returns:**
    - 200: Attendance marked successfully
    - 403: Not authorized (not drive organizer)
    - 404: Drive or user not found
    - 400: User not registered for this drive
    
    **Business Rules:**
    - Only organizer of the drive can mark attendance
    - Can mark/update attendance multiple times
    - Attendance can be marked on or after drive date
    """
    drive_repo = DriveRepository(db)
    reg_repo = RegistrationRepository(db)
    
    # Get drive
    drive = await drive_repo.get_drive_by_id(drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drive not found"
        )
    
    # Check authorization
    is_admin = "admin" in current_user.roles
    is_organizer = drive.organizer_id == current_user.id
    
    if not (is_admin or is_organizer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to mark attendance"
        )
    
    # Check if user is registered
    registration = await reg_repo.get_registration(drive_id, attendance_data.user_id)
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not registered for this drive"
        )
    
    # Mark attendance
    try:
        attendance = await reg_repo.mark_attendance(
            drive_id,
            attendance_data,
            current_user.id
        )
        
        logger.info(
            f"Attendance marked for user {attendance_data.user_id} "
            f"in drive {drive_id} by organizer {current_user.id}"
        )
        
        return attendance
        
    except Exception as e:
        logger.error(f"Attendance marking error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark attendance"
        )