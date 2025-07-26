"""
Database connection module for Aman Cybersecurity Platform
"""
import os
import logging
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv
from models import (
    UserInDB, EmailScanResult, ThreatLog, FeedbackResponse, 
    UnblockRequestResponse, OrganizationResponse, ScanStatus
)

load_dotenv()
logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

# Database instance
db_instance = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        
        # Create client
        db_instance.client = AsyncIOMotorClient(mongo_url)
        
        # Test connection
        await db_instance.client.admin.command('ping')
        
        # Set database
        db_instance.database = db_instance.client.aman_cybersecurity
        
        logger.info(f"✅ Connected to MongoDB: {mongo_url}")
        logger.info(f"✅ Using database: aman_cybersecurity")
        
    except ConnectionFailure as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if db_instance.client:
        db_instance.client.close()
        logger.info("Database connection closed")

def get_database() -> Optional[AsyncIOMotorDatabase]:
    """Get database instance"""
    return db_instance.database

# Initialize collections function
async def init_collections():
    """Initialize database collections and indexes"""
    try:
        db = get_database()
        if db is None:
            logger.warning("Database not connected, skipping collection initialization")
            return
        
        # Create indexes for better performance
        await db.users.create_index("email", unique=True, background=True)
        await db.users.create_index("id", unique=True, background=True)
        await db.email_scans.create_index("user_id", background=True)
        await db.email_scans.create_index("created_at", background=True)
        await db.user_settings.create_index("user_id", unique=True, background=True)
        
        # Create collections if they don't exist
        collections = await db.list_collection_names()
        
        if "users" not in collections:
            await db.create_collection("users")
        if "email_scans" not in collections:
            await db.create_collection("email_scans")
        if "user_settings" not in collections:
            await db.create_collection("user_settings")
        if "ai_usage" not in collections:
            await db.create_collection("ai_usage")
        if "ai_cache" not in collections:
            await db.create_collection("ai_cache")
        
        logger.info("✅ Database collections initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize collections: {e}")
        # Don't raise, just log the error for development

# Collection helper classes
class UserDatabase:
    @staticmethod
    async def create_user(user_data: dict):
        db = get_database()
        if db is None:
            raise Exception("Database not connected")
        
        result = await db.users.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        return user_data
    
    @staticmethod
    async def get_user_by_email(email: str):
        db = get_database()
        if db is None:
            return None
        
        return await db.users.find_one({"email": email})
    
    @staticmethod
    async def get_user_by_id(user_id: str):
        db = get_database()
        if db is None:
            return None
        
        return await db.users.find_one({"id": user_id})
    
    @staticmethod
    async def update_user(user_id: str, update_data: dict):
        db = get_database()
        if db is None:
            return None
        
        update_data["updated_at"] = datetime.utcnow()
        result = await db.users.update_one({"id": user_id}, {"$set": update_data})
        return result.modified_count > 0

class EmailScanDatabase:
    @staticmethod
    async def create_email_scan(scan_data: dict):
        db = get_database()
        if db is None:
            raise Exception("Database not connected")
        
        scan_data["created_at"] = datetime.utcnow()
        result = await db.email_scans.insert_one(scan_data)
        scan_data["_id"] = result.inserted_id
        return scan_data
    
    @staticmethod
    async def get_recent_scans(user_id: str, limit: int = 10):
        db = get_database()
        if db is None:
            return []
        
        cursor = db.email_scans.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(limit)
    
    @staticmethod
    async def get_user_stats(user_id: str):
        db = get_database()
        if db is None:
            return {"total_scans": 0, "threats_blocked": 0, "safe_emails": 0}
        
        # Get today's date
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Aggregate stats
        pipeline = [
            {"$match": {"user_id": user_id, "created_at": {"$gte": today}}},
            {
                "$group": {
                    "_id": None,
                    "total_scans": {"$sum": 1},
                    "threats_blocked": {
                        "$sum": {"$cond": [{"$in": ["$scan_result", ["potential_phishing", "phishing"]]}, 1, 0]}
                    },
                    "safe_emails": {
                        "$sum": {"$cond": [{"$eq": ["$scan_result", "safe"]}, 1, 0]}
                    }
                }
            }
        ]
        
        result = await db.email_scans.aggregate(pipeline).to_list(1)
        if result:
            return result[0]
        else:
            return {"total_scans": 0, "threats_blocked": 0, "safe_emails": 0}

class SettingsDatabase:
    @staticmethod
    async def get_user_settings(user_id: str):
        db = get_database()
        if db is None:
            return {}
        
        settings = await db.user_settings.find_one({"user_id": user_id})
        return settings.get("settings", {}) if settings else {}
    
    @staticmethod
    async def update_user_settings(user_id: str, settings: dict):
        db = get_database()
        if db is None:
            return False
        
        await db.user_settings.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "settings": settings,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        return True