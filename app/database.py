"""
MongoDB database connection and initialization.
Uses Motor for async MongoDB operations with FastAPI.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """
    MongoDB connection manager.
    Handles connection lifecycle and provides database instance.
    """
    
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls):
        """
        Establish connection to MongoDB.
        Called during application startup.
        """
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
            cls.database = cls.client[settings.DATABASE_NAME]
            
            # Test connection
            await cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.DATABASE_NAME}")
            
            # Create indexes for performance and uniqueness
            await cls._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """
        Close MongoDB connection.
        Called during application shutdown.
        """
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    async def _create_indexes(cls):
        """
        Create database indexes for performance and data integrity.
        
        Security Notes:
            - Unique indexes prevent duplicate data
            - Compound indexes optimize common queries
            - Geospatial indexes enable location-based search
        """
        if not cls.database:
            return
        
        # Users collection indexes
        users_collection = cls.database.users
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("phone", unique=True)
        await users_collection.create_index("roles")
        
        # Drives collection indexes
        drives_collection = cls.database.drives
        await drives_collection.create_index("organizer_id")
        await drives_collection.create_index("status")
        await drives_collection.create_index("date_time")
        await drives_collection.create_index("location.district")
        await drives_collection.create_index("type")
        # Geospatial index for location-based queries
        await drives_collection.create_index([("location.geo", "2dsphere")])
        # Compound index for common query patterns
        await drives_collection.create_index([
            ("status", 1),
            ("date_time", 1),
            ("location.district", 1)
        ])
        
        # Registrations collection indexes
        registrations_collection = cls.database.registrations
        await registrations_collection.create_index([
            ("drive_id", 1),
            ("user_id", 1)
        ], unique=True)  # Prevent duplicate registrations
        await registrations_collection.create_index("user_id")
        await registrations_collection.create_index("drive_id")
        await registrations_collection.create_index("status")
        
        # Attendance collection indexes
        attendance_collection = cls.database.attendance
        await attendance_collection.create_index([
            ("drive_id", 1),
            ("user_id", 1)
        ], unique=True)  # One attendance record per user per drive
        await attendance_collection.create_index("drive_id")
        await attendance_collection.create_index("marked_by")
        
        # Messages collection indexes (for in-app messaging)
        messages_collection = cls.database.messages
        await messages_collection.create_index("drive_id")
        await messages_collection.create_index("recipient_id")
        await messages_collection.create_index("sender_id")
        await messages_collection.create_index("created_at")
        
        # Refresh tokens collection indexes
        refresh_tokens_collection = cls.database.refresh_tokens
        await refresh_tokens_collection.create_index("user_id")
        await refresh_tokens_collection.create_index("token", unique=True)
        await refresh_tokens_collection.create_index(
            "expires_at",
            expireAfterSeconds=0  # TTL index - auto-delete expired tokens
        )
        
        logger.info("Database indexes created successfully")
    
    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get database instance.
        
        Returns:
            AsyncIOMotorDatabase: MongoDB database instance
            
        Raises:
            RuntimeError: If database is not connected
        """
        if not cls.database:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls.database


async def get_db() -> AsyncIOMotorDatabase:
    """
    Dependency function to get database instance in route handlers.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(db: AsyncIOMotorDatabase = Depends(get_db)):
            # Use db here
            
    Returns:
        AsyncIOMotorDatabase: Database instance for dependency injection
    """
    return MongoDB.get_database()