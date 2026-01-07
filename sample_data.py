"""
Sample data generation script for testing.
Creates realistic users, drives, and registrations.

Usage:
    python scripts/sample_data.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import AsyncMongoClient
from app.core.config import settings
from app.core.security import get_password_hash


async def create_sample_data():
    """Create sample data in MongoDB."""
    
    # Connect to MongoDB
    client = AsyncMongoClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    print("Creating sample data...")
    
    # Sample Users
    users = [
        {
            "_id": "user_volunteer_1",
            "name": "Arjun Menon",
            "email": "arjun@example.com",
            "phone": "+919876543210",
            "age_band": "18+",
            "hashed_password": get_password_hash("P"),
            "roles": ["volunteer"],
            "consent_flags": {
                "terms_accepted": True,
                "privacy_accepted": True,
                "guardian_consent": None
            },
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": "user_organizer_1",
            "name": "Priya Nair",
            "email": "priya@example.com",
            "phone": "+919876543211",
            "age_band": "18+",
            "hashed_password": get_password_hash("P"),
            "roles": ["volunteer", "organizer"],
            "consent_flags": {
                "terms_accepted": True,
                "privacy_accepted": True,
                "guardian_consent": None
            },
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": "user_minor_1",
            "name": "Ananya Raj",
            "email": "ananya@example.com",
            "phone": "+919876543212",
            "age_band": "13-17",
            "hashed_password": get_password_hash("P"),
            "roles": ["volunteer"],
            "consent_flags": {
                "terms_accepted": True,
                "privacy_accepted": True,
                "guardian_consent": True
            },
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "_id": "user_admin_1",
            "name": "Admin User",
            "email": "admin@example.com",
            "phone": "+919876543213",
            "age_band": "18+",
            "hashed_password": get_password_hash("A"),
            "roles": ["volunteer", "organizer", "admin"],
            "consent_flags": {
                "terms_accepted": True,
                "privacy_accepted": True,
                "guardian_consent": None
            },
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Clear existing users (for testing only!)
    await db.users.delete_many({})
    await db.users.insert_many(users)
    print(f"✓ Created {len(users)} users")
    print("  Credentials:")
    print("    - Volunteer: arjun@example.com / P")
    print("    - Organizer: priya@example.com / P")
    print("    - Admin: admin@example.com / A")
    
    # Sample Drives
    now = datetime.utcnow()
    drives = [
        {
            "_id": "drive_1",
            "title": "Varkala Beach Cleanup Drive",
            "description": "Join us for a morning beach cleanup at Varkala. We'll provide gloves, bags, and refreshments. Let's make our beaches clean!",
            "type": "beach_cleanup",
            "date_time": now + timedelta(days=7),
            "location": {
                "geo": {
                    "type": "Point",
                    "coordinates": [76.7174, 8.7379]
                },
                "address": "Varkala Beach, Near Cliff Side",
                "district": "Thiruvananthapuram",
                "state": "Kerala"
            },
            "max_volunteers": 50,
            "organizer_id": "user_organizer_1",
            "status": "published",
            "current_volunteers": 2,
            "registration_open": True,
            "created_at": now - timedelta(days=3),
            "updated_at": now - timedelta(days=3)
        },
        {
            "_id": "drive_2",
            "title": "Periyar River Cleanup Initiative",
            "description": "Help us clean the banks of Periyar River. This is a crucial initiative to protect our water sources. Bring your energy and enthusiasm!",
            "type": "river_cleanup",
            "date_time": now + timedelta(days=14),
            "location": {
                "geo": {
                    "type": "Point",
                    "coordinates": [76.2673, 9.9312]
                },
                "address": "Periyar River Bank, Aluva",
                "district": "Ernakulam",
                "state": "Kerala"
            },
            "max_volunteers": 100,
            "organizer_id": "user_organizer_1",
            "status": "published",
            "current_volunteers": 1,
            "registration_open": True,
            "created_at": now - timedelta(days=5),
            "updated_at": now - timedelta(days=5)
        },
        {
            "_id": "drive_3",
            "title": "Marine Drive Park Cleanup",
            "description": "Community cleanup drive at Marine Drive Park. Family-friendly event with activities for children. Snacks provided.",
            "type": "park_cleanup",
            "date_time": now + timedelta(days=3),
            "location": {
                "geo": {
                    "type": "Point",
                    "coordinates": [76.2673, 9.9312]
                },
                "address": "Marine Drive, Kochi",
                "district": "Ernakulam",
                "state": "Kerala"
            },
            "max_volunteers": 30,
            "organizer_id": "user_organizer_1",
            "status": "published",
            "current_volunteers": 0,
            "registration_open": True,
            "created_at": now - timedelta(days=2),
            "updated_at": now - timedelta(days=2)
        },
        {
            "_id": "drive_4",
            "title": "Kozhikode Beach Sunrise Cleanup",
            "description": "Early morning beach cleanup followed by breakfast. Perfect way to start your weekend!",
            "type": "beach_cleanup",
            "date_time": now + timedelta(days=21),
            "location": {
                "geo": {
                    "type": "Point",
                    "coordinates": [75.7704, 11.2588]
                },
                "address": "Kozhikode Beach",
                "district": "Kozhikode",
                "state": "Kerala"
            },
            "max_volunteers": 40,
            "organizer_id": "user_organizer_1",
            "status": "published",
            "current_volunteers": 0,
            "registration_open": True,
            "created_at": now - timedelta(days=1),
            "updated_at": now - timedelta(days=1)
        },
        {
            "_id": "drive_5",
            "title": "Draft Drive - Planning Phase",
            "description": "This drive is still in planning phase.",
            "type": "street_cleanup",
            "date_time": now + timedelta(days=30),
            "location": {
                "geo": {
                    "type": "Point",
                    "coordinates": [76.9366, 8.5241]
                },
                "address": "MG Road, Trivandrum",
                "district": "Thiruvananthapuram",
                "state": "Kerala"
            },
            "max_volunteers": 25,
            "organizer_id": "user_organizer_1",
            "status": "draft",
            "current_volunteers": 0,
            "registration_open": False,
            "created_at": now,
            "updated_at": now
        }
    ]
    
    await db.drives.delete_many({})
    await db.drives.insert_many(drives)
    print(f"✓ Created {len(drives)} drives")
    
    # Sample Registrations
    registrations = [
        {
            "_id": "reg_1",
            "drive_id": "drive_1",
            "user_id": "user_volunteer_1",
            "status": "confirmed",
            "created_at": now - timedelta(days=2)
        },
        {
            "_id": "reg_2",
            "drive_id": "drive_1",
            "user_id": "user_minor_1",
            "status": "confirmed",
            "created_at": now - timedelta(days=1)
        },
        {
            "_id": "reg_3",
            "drive_id": "drive_2",
            "user_id": "user_volunteer_1",
            "status": "confirmed",
            "created_at": now - timedelta(days=3)
        }
    ]
    
    await db.registrations.delete_many({})
    await db.registrations.insert_many(registrations)
    print(f"✓ Created {len(registrations)} registrations")
    
    # Sample Attendance (for completed drive example)
    # Note: Would typically only be for past drives
    attendance = [
        {
            "_id": "att_1",
            "drive_id": "drive_1",
            "user_id": "user_volunteer_1",
            "attended": True,
            "hours_logged": 3.5,
            "marked_by": "user_organizer_1",
            "marked_at": now
        }
    ]
    
    await db.attendance.delete_many({})
    # Uncomment to add attendance records
    # await db.attendance.insert_many(attendance)
    # print(f"✓ Created {len(attendance)} attendance records")
    
    print("\n✅ Sample data created successfully!")
    print("\nQuick test commands:")
    print("curl http://localhost:8000/api/v1/drives/")
    print("curl -X POST http://localhost:8000/api/v1/auth/login \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"email\":\"arjun@example.com\",\"password\":\"Password123\"}'")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(create_sample_data())