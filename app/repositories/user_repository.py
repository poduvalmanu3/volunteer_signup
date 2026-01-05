"""
User repository for database operations.
Implements data access layer with NoSQL injection prevention.
"""

from typing import Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.user import UserCreate, UserInDB, UserUpdate
from app.core.security import get_password_hash, sanitize_mongo_query


class UserRepository:
    """
    Repository for user-related database operations.
    Follows repository pattern to separate data access from business logic.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize repository with database instance.
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.users
    
    async def create_user(self, user_data: UserCreate) -> UserInDB:
        """
        Create a new user in database.
        
        Args:
            user_data: User creation data
            
        Returns:
            UserInDB: Created user with ID
            
        Security Notes:
            - Password is hashed before storage
            - Email and phone uniqueness enforced by index
        """
        # Prepare user document
        user_dict = {
            "_id": str(ObjectId()),
            "name": user_data.name,
            "email": user_data.email.lower(),  # Normalize email
            "phone": user_data.phone,
            "age_band": user_data.age_band,
            "hashed_password": get_password_hash(user_data.password),
            "roles": ["volunteer"],  # Default role
            "consent_flags": user_data.consent_flags.model_dump(),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert into database
        await self.collection.insert_one(user_dict)
        
        return UserInDB(**user_dict)
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            UserInDB or None if not found
            
        Security Note:
            - Sanitizes user_id to prevent injection
        """
        # Sanitize input
        safe_id = sanitize_mongo_query({"_id": user_id})["_id"]
        
        user_dict = await self.collection.find_one({"_id": safe_id})
        
        if user_dict:
            return UserInDB(**user_dict)
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Get user by email address.
        
        Args:
            email: Email address
            
        Returns:
            UserInDB or None if not found
        """
        # Normalize and sanitize email
        safe_email = sanitize_mongo_query({"email": email.lower()})["email"]
        
        user_dict = await self.collection.find_one({"email": safe_email})
        
        if user_dict:
            return UserInDB(**user_dict)
        return None
    
    async def get_user_by_phone(self, phone: str) -> Optional[UserInDB]:
        """
        Get user by phone number.
        
        Args:
            phone: Phone number
            
        Returns:
            UserInDB or None if not found
        """
        safe_phone = sanitize_mongo_query({"phone": phone})["phone"]
        
        user_dict = await self.collection.find_one({"phone": safe_phone})
        
        if user_dict:
            return UserInDB(**user_dict)
        return None
    
    async def update_user(self, user_id: str, update_data: UserUpdate) -> Optional[UserInDB]:
        """
        Update user profile.
        
        Args:
            user_id: User ID
            update_data: Fields to update
            
        Returns:
            Updated UserInDB or None if not found
            
        Security Note:
            - Only updates provided fields (partial update)
            - Sanitizes all inputs
        """
        # Build update document with only provided fields
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if not update_dict:
            # No fields to update
            return await self.get_user_by_id(user_id)
        
        # Sanitize update data
        update_dict = sanitize_mongo_query(update_dict)
        
        # Add updated timestamp
        update_dict["updated_at"] = datetime.utcnow()
        
        # Normalize email if provided
        if "email" in update_dict:
            update_dict["email"] = update_dict["email"].lower()
        
        # Sanitize user_id
        safe_id = sanitize_mongo_query({"_id": user_id})["_id"]
        
        # Perform update
        result = await self.collection.find_one_and_update(
            {"_id": safe_id},
            {"$set": update_dict},
            return_document=True
        )
        
        if result:
            return UserInDB(**result)
        return None
    
    async def add_role(self, user_id: str, role: str) -> Optional[UserInDB]:
        """
        Add a role to user.
        
        Args:
            user_id: User ID
            role: Role to add (organizer, admin)
            
        Returns:
            Updated UserInDB or None if not found
        """
        safe_id = sanitize_mongo_query({"_id": user_id})["_id"]
        safe_role = sanitize_mongo_query({"role": role})["role"]
        
        result = await self.collection.find_one_and_update(
            {"_id": safe_id},
            {
                "$addToSet": {"roles": safe_role},  # addToSet prevents duplicates
                "$set": {"updated_at": datetime.utcnow()}
            },
            return_document=True
        )
        
        if result:
            return UserInDB(**result)
        return None
    
    async def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate user account.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if successful
        """
        safe_id = sanitize_mongo_query({"_id": user_id})["_id"]
        
        result = await self.collection.update_one(
            {"_id": safe_id},
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0