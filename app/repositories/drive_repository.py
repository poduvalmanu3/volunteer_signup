"""
Drive repository for cleanup drive database operations.
Supports geospatial queries and complex filtering.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.drive import DriveCreate, DriveInDB, DriveUpdate, DriveSearchFilters
from app.core.security import sanitize_mongo_query
from app.core.config import settings


class DriveRepository:
    """
    Repository for drive-related database operations.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.drives
    
    async def create_drive(self, drive_data: DriveCreate, organizer_id: str) -> DriveInDB:
        """
        Create a new cleanup drive.
        
        Args:
            drive_data: Drive creation data
            organizer_id: ID of organizer creating the drive
            
        Returns:
            DriveInDB: Created drive with ID
        """
        # Prepare drive document
        drive_dict = {
            "_id": str(ObjectId()),
            "title": drive_data.title,
            "description": drive_data.description,
            "type": drive_data.type,
            "date_time": drive_data.date_time,
            "location": drive_data.location.model_dump(),
            "max_volunteers": drive_data.max_volunteers,
            "organizer_id": organizer_id,
            "status": "draft",  # Start as draft
            "current_volunteers": 0,
            "registration_open": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await self.collection.insert_one(drive_dict)
        
        return DriveInDB(**drive_dict)
    
    async def get_drive_by_id(self, drive_id: str) -> Optional[DriveInDB]:
        """
        Get drive by ID.
        
        Args:
            drive_id: Drive ID
            
        Returns:
            DriveInDB or None if not found
        """
        safe_id = sanitize_mongo_query({"_id": drive_id})["_id"]
        
        drive_dict = await self.collection.find_one({"_id": safe_id})
        
        if drive_dict:
            return DriveInDB(**drive_dict)
        return None
    
    async def update_drive(
        self,
        drive_id: str,
        update_data: DriveUpdate
    ) -> Optional[DriveInDB]:
        """
        Update drive details.
        
        Args:
            drive_id: Drive ID
            update_data: Fields to update
            
        Returns:
            Updated DriveInDB or None if not found
        """
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if not update_dict:
            return await self.get_drive_by_id(drive_id)
        
        # Sanitize update data
        update_dict = sanitize_mongo_query(update_dict)
        update_dict["updated_at"] = datetime.utcnow()
        
        safe_id = sanitize_mongo_query({"_id": drive_id})["_id"]
        
        result = await self.collection.find_one_and_update(
            {"_id": safe_id},
            {"$set": update_dict},
            return_document=True
        )
        
        if result:
            return DriveInDB(**result)
        return None
    
    async def search_drives(
        self,
        filters: DriveSearchFilters
    ) -> tuple[List[DriveInDB], int]:
        """
        Search drives with filters and pagination.
        
        Args:
            filters: Search filters
            
        Returns:
            Tuple of (list of drives, total count)
            
        Security Note:
            - All filter values are sanitized
            - Prevents NoSQL injection through user input
        """
        # Build query
        query: Dict[str, Any] = {}
        
        # Status filter (default to published for public search)
        if filters.status:
            query["status"] = sanitize_mongo_query({"status": filters.status})["status"]
        
        # District filter
        if filters.district:
            query["location.district"] = sanitize_mongo_query(
                {"district": filters.district}
            )["district"]
        
        # Type filter
        if filters.type:
            query["type"] = sanitize_mongo_query({"type": filters.type})["type"]
        
        # Date range filters
        if filters.date_from or filters.date_to:
            date_query = {}
            if filters.date_from:
                date_query["$gte"] = filters.date_from
            if filters.date_to:
                date_query["$lte"] = filters.date_to
            if date_query:
                query["date_time"] = date_query
        
        # Get total count
        total = await self.collection.count_documents(query)
        
        # Calculate pagination
        skip = (filters.page - 1) * filters.page_size
        
        # Fetch drives with pagination
        cursor = self.collection.find(query).sort("date_time", 1).skip(skip).limit(filters.page_size)
        
        drives = []
        async for drive_dict in cursor:
            drives.append(DriveInDB(**drive_dict))
        
        return drives, total
    
    async def get_organizer_drives(
        self,
        organizer_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[DriveInDB], int]:
        """
        Get all drives created by an organizer.
        
        Args:
            organizer_id: Organizer user ID
            page: Page number
            page_size: Items per page
            
        Returns:
            Tuple of (list of drives, total count)
        """
        safe_id = sanitize_mongo_query({"organizer_id": organizer_id})["organizer_id"]
        
        query = {"organizer_id": safe_id}
        total = await self.collection.count_documents(query)
        
        skip = (page - 1) * page_size
        cursor = self.collection.find(query).sort("date_time", -1).skip(skip).limit(page_size)
        
        drives = []
        async for drive_dict in cursor:
            drives.append(DriveInDB(**drive_dict))
        
        return drives, total
    
    async def update_volunteer_count(self, drive_id: str, increment: int) -> bool:
        """
        Update current volunteer count for a drive.
        
        Args:
            drive_id: Drive ID
            increment: Number to add (positive) or subtract (negative)
            
        Returns:
            bool: True if successful
        """
        safe_id = sanitize_mongo_query({"_id": drive_id})["_id"]
        
        result = await self.collection.update_one(
            {"_id": safe_id},
            {
                "$inc": {"current_volunteers": increment},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
    
    async def update_status(self, drive_id: str, status: str) -> bool:
        """
        Update drive status.
        
        Args:
            drive_id: Drive ID
            status: New status (draft, published, ongoing, completed, cancelled)
            
        Returns:
            bool: True if successful
        """
        safe_id = sanitize_mongo_query({"_id": drive_id})["_id"]
        safe_status = sanitize_mongo_query({"status": status})["status"]
        
        result = await self.collection.update_one(
            {"_id": safe_id},
            {
                "$set": {
                    "status": safe_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    async def close_registration(self, drive_id: str) -> bool:
        """
        Close registration for a drive.
        
        Args:
            drive_id: Drive ID
            
        Returns:
            bool: True if successful
        """
        safe_id = sanitize_mongo_query({"_id": drive_id})["_id"]
        
        result = await self.collection.update_one(
            {"_id": safe_id},
            {
                "$set": {
                    "registration_open": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    async def auto_close_registrations(self) -> int:
        """
        Auto-close registrations for drives that are about to start.
        Called by scheduled task.
        
        Returns:
            int: Number of drives updated
        """
        cutoff_time = datetime.utcnow() + timedelta(
            hours=settings.REGISTRATION_DEADLINE_HOURS
        )
        
        result = await self.collection.update_many(
            {
                "date_time": {"$lte": cutoff_time},
                "registration_open": True,
                "status": "published"
            },
            {
                "$set": {
                    "registration_open": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count