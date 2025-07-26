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
    if db_instance.database is None:
        print("⚠️ Database not connected")
        return None
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
        
        # Ensure user has required fields
        user_data["id"] = str(uuid.uuid4())
        user_data["role"] = user_data.get("role", "user")
        user_data["is_active"] = user_data.get("is_active", True)
        user_data["created_at"] = datetime.utcnow()
        
        result = await db.users.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        return user_data
    
    @staticmethod
    async def get_user_by_email(email: str):
        db = get_database()
        if db is None:
            return None
        
        user = await db.users.find_one({"email": email})
        if user and "role" not in user:
            user["role"] = "user"  # Default role
        return user
    
    @staticmethod
    async def get_user_by_id(user_id: str):
        db = get_database()
        if db is None:
            return None
        
        user = await db.users.find_one({"id": user_id})
        if user and "role" not in user:
            user["role"] = "user"  # Default role
        return user
    
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
        
        # Generate ID and set timestamps
        scan_data["id"] = str(uuid.uuid4())
        scan_data["created_at"] = datetime.utcnow()
        scan_data["scanned_at"] = datetime.utcnow()
        
        result = await db.email_scans.insert_one(scan_data)
        
        # Return an object-like structure with id attribute
        class ScanResult:
            def __init__(self, data):
                self.id = data["id"]
                self.__dict__.update(data)
        
        return ScanResult(scan_data)
    
    @staticmethod
    async def get_recent_scans(user_id: str, limit: int = 10):
        db = get_database()
        if db is None:
            return []
        
        cursor = db.email_scans.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(limit)
    
    @staticmethod
    async def get_user_recent_scans(user_id: str, limit: int = 10):
        """Get recent scans for user with proper structure"""
        db = get_database()
        if db is None:
            return []
        
        cursor = db.email_scans.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        scans = await cursor.to_list(limit)
        
        # Convert to proper structure
        result_scans = []
        for scan in scans:
            class ScanResult:
                def __init__(self, data):
                    self.id = data.get("id", str(data.get("_id", "")))
                    self.email_subject = data.get("email_subject", "")
                    self.sender = data.get("sender", "")
                    self.scan_result = data.get("scan_result", "safe")
                    self.risk_score = data.get("risk_score", 0.0)
                    self.scanned_at = data.get("scanned_at", data.get("created_at", datetime.utcnow()))
            
            result_scans.append(ScanResult(scan))
        
        return result_scans
    
    @staticmethod
    async def get_dashboard_stats(user_id: str):
        """Get dashboard statistics for user"""
        db = get_database()
        if db is None:
            return {"total_scans": 0, "phishing_caught": 0, "safe_emails": 0, "potential_phishing": 0}
        
        # Aggregate all-time stats for user
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": None,
                    "total_scans": {"$sum": 1},
                    "phishing_caught": {
                        "$sum": {"$cond": [{"$eq": ["$scan_result", "phishing"]}, 1, 0]}
                    },
                    "potential_phishing": {
                        "$sum": {"$cond": [{"$eq": ["$scan_result", "potential_phishing"]}, 1, 0]}
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
            return {"total_scans": 0, "phishing_caught": 0, "safe_emails": 0, "potential_phishing": 0}
    
    @staticmethod
    async def get_user_stats(user_id: str):
        """Get user statistics (legacy method)"""
        return await EmailScanDatabase.get_dashboard_stats(user_id)

class ThreatDatabase:
    @staticmethod
    async def add_threat_domain(domain_data: dict):
        db = get_database()
        if db is None:
            raise Exception("Database not connected")
        
        domain_data["id"] = str(uuid.uuid4())
        domain_data["detected_at"] = datetime.utcnow()
        result = await db.threat_logs.insert_one(domain_data)
        domain_data["_id"] = result.inserted_id
        return domain_data
    
    @staticmethod
    async def check_domain_reputation(domain: str):
        db = get_database()
        if db is None:
            return None
        
        return await db.threat_domains.find_one({"domain": domain})
    
    @staticmethod
    async def update_domain_reputation(domain: str, risk_score: float, threat_type: str):
        db = get_database()
        if db is None:
            return False
        
        await db.threat_domains.update_one(
            {"domain": domain},
            {
                "$set": {
                    "risk_score": risk_score,
                    "threat_type": threat_type,
                    "last_seen": datetime.utcnow()
                }
            },
            upsert=True
        )
        return True

class FeedbackDatabase:
    @staticmethod
    async def create_feedback(feedback_data: dict):
        db = get_database()
        if db is None:
            raise Exception("Database not connected")
        
        feedback_data["id"] = str(uuid.uuid4())
        feedback_data["created_at"] = datetime.utcnow()
        result = await db.feedback.insert_one(feedback_data)
        feedback_data["_id"] = result.inserted_id
        return feedback_data
    
    @staticmethod
    async def get_feedback_for_scan(scan_id: str):
        db = get_database()
        if db is None:
            return None
        
        return await db.feedback.find_one({"scan_id": scan_id})

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