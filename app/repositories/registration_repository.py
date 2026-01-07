"""
Registration and attendance repository.
Handles volunteer registration and attendance tracking.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

from app.models.registration import (
    RegistrationInDB,
    AttendanceCreate,
    AttendanceInDB
)
from app.core.security import sanitize_mongo_query



class RegistrationRepository:
    """
    Repository for registration and attendance operations.
    """
    DB_NAME = "volunteer_signup"
    
    def __init__(self, db: DB_NAME):
        self.db = db
        self.registrations = db.registrations
        self.attendance = db.attendance
        self.drives = db.drives
    
    async def create_registration(
        self,
        drive_id: str,
        user_id: str
    ) -> RegistrationInDB:
        """
        Create a new registration.
        
        Args:
            drive_id: Drive ID
            user_id: User ID
            
        Returns:
            RegistrationInDB: Created registration
            
        Note:
            Unique index on (drive_id, user_id) prevents duplicates
        """
        registration_dict = {
            "_id": str(ObjectId()),
            "drive_id": drive_id,
            "user_id": user_id,
            "status": "confirmed",
            "created_at": datetime.utcnow()
        }
        
        await self.registrations.insert_one(registration_dict)
        
        return RegistrationInDB(**registration_dict)
    
    async def get_registration(
        self,
        drive_id: str,
        user_id: str
    ) -> Optional[RegistrationInDB]:
        """
        Get registration by drive and user.
        
        Args:
            drive_id: Drive ID
            user_id: User ID
            
        Returns:
            RegistrationInDB or None
        """
        safe_query = sanitize_mongo_query({
            "drive_id": drive_id,
            "user_id": user_id
        })
        
        reg_dict = await self.registrations.find_one(safe_query)
        
        if reg_dict:
            return RegistrationInDB(**reg_dict)
        return None
    
    async def get_registration_by_id(
        self,
        registration_id: str
    ) -> Optional[RegistrationInDB]:
        """
        Get registration by ID.
        
        Args:
            registration_id: Registration ID
            
        Returns:
            RegistrationInDB or None
        """
        safe_id = sanitize_mongo_query({"_id": registration_id})["_id"]
        
        reg_dict = await self.registrations.find_one({"_id": safe_id})
        
        if reg_dict:
            return RegistrationInDB(**reg_dict)
        return None
    
    async def get_user_registrations(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all registrations for a user with drive details.
        
        Args:
            user_id: User ID
            
        Returns:
            List of registration dictionaries with drive info
        """
        safe_id = sanitize_mongo_query({"user_id": user_id})["user_id"]
        
        # Aggregation pipeline to join with drives
        pipeline = [
            {"$match": {"user_id": safe_id}},
            {"$lookup": {
                "from": "drives",
                "localField": "drive_id",
                "foreignField": "_id",
                "as": "drive"
            }},
            {"$unwind": "$drive"},
            {"$sort": {"drive.date_time": -1}}
        ]
        
        results = []
        async for doc in self.registrations.aggregate(pipeline):
            results.append(doc)
        
        return results
    
    async def get_drive_registrations(
        self,
        drive_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get all registrations for a drive with user details.
        Returns minimal user info for privacy.
        
        Args:
            drive_id: Drive ID
            page: Page number
            page_size: Items per page
            
        Returns:
            Tuple of (list of registrations with user info, total count)
        """
        safe_id = sanitize_mongo_query({"drive_id": drive_id})["drive_id"]
        
        # Count total
        total = await self.registrations.count_documents({"drive_id": safe_id})
        
        # Calculate skip
        skip = (page - 1) * page_size
        
        # Aggregation pipeline to join with users and attendance
        pipeline = [
            {"$match": {"drive_id": safe_id}},
            {"$skip": skip},
            {"$limit": page_size},
            {"$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user"
            }},
            {"$unwind": "$user"},
            {"$lookup": {
                "from": "attendance",
                "let": {"reg_drive_id": "$drive_id", "reg_user_id": "$user_id"},
                "pipeline": [
                    {"$match": {
                        "$expr": {
                            "$and": [
                                {"$eq": ["$drive_id", "$$reg_drive_id"]},
                                {"$eq": ["$user_id", "$$reg_user_id"]}
                            ]
                        }
                    }}
                ],
                "as": "attendance"
            }},
            {"$unwind": {
                "path": "$attendance",
                "preserveNullAndEmptyArrays": True
            }},
            {"$project": {
                "registration_id": "$_id",
                "registration_status": "$status",
                "first_name": {"$arrayElemAt": [{"$split": ["$user.name", " "]}, 0]},
                "age_band": "$user.age_band",
                "attendance_status": "$attendance.attended",
                "hours_logged": "$attendance.hours_logged"
            }}
        ]
        
        results = []
        async for doc in self.registrations.aggregate(pipeline):
            results.append(doc)
        
        return results, total
    
    async def cancel_registration(
        self,
        registration_id: str
    ) -> bool:
        """
        Cancel a registration.
        
        Args:
            registration_id: Registration ID
            
        Returns:
            bool: True if successful
        """
        safe_id = sanitize_mongo_query({"_id": registration_id})["_id"]
        
        result = await self.registrations.update_one(
            {"_id": safe_id},
            {"$set": {"status": "cancelled"}}
        )
        
        return result.modified_count > 0
    
    async def delete_registration(
        self,
        registration_id: str
    ) -> bool:
        """
        Delete a registration permanently.
        
        Args:
            registration_id: Registration ID
            
        Returns:
            bool: True if successful
        """
        safe_id = sanitize_mongo_query({"_id": registration_id})["_id"]
        
        result = await self.registrations.delete_one({"_id": safe_id})
        
        return result.deleted_count > 0
    
    async def mark_attendance(
        self,
        drive_id: str,
        attendance_data: AttendanceCreate,
        marked_by: str
    ) -> AttendanceInDB:
        """
        Mark attendance for a volunteer.
        
        Args:
            drive_id: Drive ID
            attendance_data: Attendance data
            marked_by: Organizer ID marking attendance
            
        Returns:
            AttendanceInDB: Created attendance record
            
        Note:
            Uses upsert to handle updates if attendance already marked
        """
        attendance_dict = {
            "drive_id": drive_id,
            "user_id": attendance_data.user_id,
            "attended": attendance_data.attended,
            "hours_logged": attendance_data.hours_logged,
            "marked_by": marked_by,
            "marked_at": datetime.utcnow()
        }
        
        # Upsert: update if exists, insert if not
        result = await self.attendance.find_one_and_update(
            {
                "drive_id": drive_id,
                "user_id": attendance_data.user_id
            },
            {"$set": attendance_dict},
            upsert=True,
            return_document=True
        )
        
        if not result.get("_id"):
            result["_id"] = str(ObjectId())
        
        return AttendanceInDB(**result)
    
    async def get_attendance(
        self,
        drive_id: str,
        user_id: str
    ) -> Optional[AttendanceInDB]:
        """
        Get attendance record.
        
        Args:
            drive_id: Drive ID
            user_id: User ID
            
        Returns:
            AttendanceInDB or None
        """
        safe_query = sanitize_mongo_query({
            "drive_id": drive_id,
            "user_id": user_id
        })
        
        att_dict = await self.attendance.find_one(safe_query)
        
        if att_dict:
            return AttendanceInDB(**att_dict)
        return None
    
    async def get_drive_attendance_stats(
        self,
        drive_id: str
    ) -> Dict[str, int]:
        """
        Get attendance statistics for a drive.
        
        Args:
            drive_id: Drive ID
            
        Returns:
            Dictionary with attendance counts
        """
        safe_id = sanitize_mongo_query({"drive_id": drive_id})["drive_id"]
        
        pipeline = [
            {"$match": {"drive_id": safe_id}},
            {"$group": {
                "_id": "$attended",
                "count": {"$sum": 1}
            }}
        ]
        
        stats = {"attended": 0, "absent": 0}
        async for result in self.attendance.aggregate(pipeline):
            if result["_id"]:
                stats["attended"] = result["count"]
            else:
                stats["absent"] = result["count"]
        
        return stats