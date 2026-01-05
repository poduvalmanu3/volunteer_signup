"""
Drives router.
Cleanup drive management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.user import UserInDB
from app.models.drive import (
    DriveCreate,
    DriveUpdate,
    DriveResponse,
    DriveListResponse,
    DriveSearchFilters
)
from app.repositories.drive_repository import DriveRepository
from app.core.dependencies import get_current_user, require_organizer
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drives", tags=["Drives"])


@router.get("/", response_model=DriveListResponse)
async def search_drives(
    district: Optional[str] = Query(None, description="Filter by district"),
    type: Optional[str] = Query(None, description="Filter by drive type"),
    date_from: Optional[datetime] = Query(None, description="Start date filter"),
    date_to: Optional[datetime] = Query(None, description="End date filter"),
    status: Optional[str] = Query("published", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Search and filter cleanup drives (PUBLIC endpoint).
    
    **Authentication:** Not required for public search
    
    **Query Parameters:**
    - district: Kerala district name
    - type: Drive type (beach_cleanup, river_cleanup, etc.)
    - date_from: Filter drives starting from this date
    - date_to: Filter drives until this date
    - status: Drive status (default: "published")
    - page: Page number for pagination
    - page_size: Items per page (max 100)
    
    **Returns:**
    - 200: Paginated list of drives
    - 400: Invalid filter values
    
    **Privacy Note:**
    - Only published drives visible in public search
    - Organizer contact info not exposed
    """
    # Build filters
    filters = DriveSearchFilters(
        district=district,
        type=type,
        date_from=date_from,
        date_to=date_to,
        status=status,
        page=page,
        page_size=min(page_size, settings.MAX_PAGE_SIZE)
    )
    
    repo = DriveRepository(db)
    drives, total = await repo.search_drives(filters)
    
    # Calculate pagination metadata
    total_pages = (total + filters.page_size - 1) // filters.page_size
    has_next = page < total_pages
    has_prev = page > 1
    
    return DriveListResponse(
        drives=drives,
        total=total,
        page=page,
        page_size=filters.page_size,
        has_next=has_next,
        has_prev=has_prev
    )


@router.post("/", response_model=DriveResponse, status_code=status.HTTP_201_CREATED)
async def create_drive(
    drive_data: DriveCreate,
    current_user: UserInDB = Depends(require_organizer),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Create a new cleanup drive.
    
    **Authentication:** Required (JWT)
    **Authorization:** Organizer or Admin role
    
    **Request Body:**
    - title: Drive title (5-200 chars)
    - description: Detailed description (20-2000 chars)
    - type: Drive type (beach_cleanup, river_cleanup, etc.)
    - date_time: Drive date and time (must be in future)
    - location: Full location with geo coordinates
    - max_volunteers: Maximum participants (1-1000)
    
    **Returns:**
    - 201: Drive created (starts as "draft" status)
    - 400: Validation error
    - 401: Unauthorized
    - 403: Insufficient permissions (not organizer/admin)
    
    **Note:**
    - Drive starts in "draft" status
    - Publish separately to make visible in public search
    """
    repo = DriveRepository(db)
    
    try:
        drive = await repo.create_drive(drive_data, current_user.id)
        logger.info(f"Drive created: {drive.id} by organizer: {current_user.id}")
        return drive
    except Exception as e:
        logger.error(f"Drive creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create drive"
        )


@router.get("/{drive_id}", response_model=DriveResponse)
async def get_drive(
    drive_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get drive details by ID (PUBLIC endpoint).
    
    **Authentication:** Not required
    
    **Path Parameters:**
    - drive_id: Drive ID
    
    **Returns:**
    - 200: Drive details
    - 404: Drive not found
    """
    repo = DriveRepository(db)
    drive = await repo.get_drive_by_id(drive_id)
    
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drive not found"
        )
    
    return drive


@router.patch("/{drive_id}", response_model=DriveResponse)
async def update_drive(
    drive_id: str,
    update_data: DriveUpdate,
    current_user: UserInDB = Depends(require_organizer),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update drive details.
    
    **Authentication:** Required (JWT)
    **Authorization:** Drive organizer or Admin
    
    **Path Parameters:**
    - drive_id: Drive ID
    
    **Request Body:**
    All fields optional for partial update
    
    **Returns:**
    - 200: Updated drive
    - 403: Not authorized (not drive organizer)
    - 404: Drive not found
    
    **Security:**
    - Only drive organizer or admin can update
    - Cannot update past drives
    """
    repo = DriveRepository(db)
    
    # Get existing drive
    drive = await repo.get_drive_by_id(drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drive not found"
        )
    
    # Check authorization (organizer or admin)
    is_admin = "admin" in current_user.roles
    is_organizer = drive.organizer_id == current_user.id
    
    if not (is_admin or is_organizer):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this drive"
        )
    
    # Update drive
    updated_drive = await repo.update_drive(drive_id, update_data)
    
    if not updated_drive:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update drive"
        )
    
    logger.info(f"Drive updated: {drive_id} by user: {current_user.id}")
    
    return updated_drive