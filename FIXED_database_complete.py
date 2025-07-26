"""
Database connection module for Aman Cybersecurity Platform - COMPLETE VERSION
"""
import os
import logging
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
from datetime import datetime, timedelta

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

    @staticmethod
    async def get_all_users(skip: int = 0, limit: int = 50):
        db = get_database()
        if db is None:
            return []
        
        cursor = db.users.find({}).skip(skip).limit(limit)
        return await cursor.to_list(limit)

    @staticmethod
    async def get_users_count():
        db = get_database()
        if db is None:
            return 0
        
        return await db.users.count_documents({})

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

    @staticmethod
    async def get_all_scans(skip: int = 0, limit: int = 50):
        db = get_database()
        if db is None:
            return []
        
        cursor = db.email_scans.find({}).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(limit)

    @staticmethod
    async def get_scans_count():
        db = get_database()
        if db is None:
            return 0
        
        return await db.email_scans.count_documents({})

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

class ThreatDatabase:
    """Database operations for threat management"""
    
    @staticmethod
    async def create_threat_log(threat_data: dict):
        db = get_database()
        if db is None:
            raise Exception("Database not connected")
        
        threat_data["created_at"] = datetime.utcnow()
        result = await db.threat_logs.insert_one(threat_data)
        threat_data["_id"] = result.inserted_id
        return threat_data
    
    @staticmethod
    async def get_threat_logs(limit: int = 100):
        db = get_database()
        if db is None:
            return []
        
        cursor = db.threat_logs.find({}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(limit)
    
    @staticmethod
    async def get_threat_stats():
        db = get_database()
        if db is None:
            return {"total_threats": 0, "today_threats": 0}
        
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_threats = await db.threat_logs.count_documents({})
        today_threats = await db.threat_logs.count_documents({"created_at": {"$gte": today}})
        
        return {"total_threats": total_threats, "today_threats": today_threats}

    @staticmethod
    async def store_domain_reputation(domain: str, reputation_data: dict):
        db = get_database()
        if db is None:
            return False
        
        reputation_data.update({
            "domain": domain,
            "updated_at": datetime.utcnow()
        })
        
        await db.domain_reputation.update_one(
            {"domain": domain},
            {"$set": reputation_data},
            upsert=True
        )
        return True

    @staticmethod
    async def get_domain_reputation(domain: str):
        db = get_database()
        if db is None:
            return None
        
        return await db.domain_reputation.find_one({"domain": domain})

class FeedbackDatabase:
    """Database operations for user feedback"""
    
    @staticmethod
    async def create_feedback(feedback_data: dict):
        db = get_database()
        if db is None:
            raise Exception("Database not connected")
        
        feedback_data["created_at"] = datetime.utcnow()
        result = await db.feedback.insert_one(feedback_data)
        feedback_data["_id"] = result.inserted_id
        return feedback_data
    
    @staticmethod
    async def get_user_feedback(user_id: str, limit: int = 50):
        db = get_database()
        if db is None:
            return []
        
        cursor = db.feedback.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(limit)
    
    @staticmethod
    async def get_feedback_analytics():
        db = get_database()
        if db is None:
            return {"total_feedback": 0, "positive_feedback": 0, "negative_feedback": 0}
        
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_feedback": {"$sum": 1},
                    "positive_feedback": {
                        "$sum": {"$cond": [{"$gte": ["$rating", 4]}, 1, 0]}
                    },
                    "negative_feedback": {
                        "$sum": {"$cond": [{"$lte": ["$rating", 2]}, 1, 0]}
                    }
                }
            }
        ]
        
        result = await db.feedback.aggregate(pipeline).to_list(1)
        if result:
            return result[0]
        else:
            return {"total_feedback": 0, "positive_feedback": 0, "negative_feedback": 0}

class AICostDatabase:
    """Database operations for AI cost management"""
    
    @staticmethod
    async def record_ai_usage(usage_data: dict):
        db = get_database()
        if db is None:
            raise Exception("Database not connected")
        
        usage_data["created_at"] = datetime.utcnow()
        result = await db.ai_usage.insert_one(usage_data)
        usage_data["_id"] = result.inserted_id
        return usage_data
    
    @staticmethod
    async def get_ai_usage_stats(start_date: datetime = None, end_date: datetime = None):
        db = get_database()
        if db is None:
            return {"total_requests": 0, "total_cost": 0.0, "total_tokens": 0}
        
        match_filter = {}
        if start_date and end_date:
            match_filter["created_at"] = {"$gte": start_date, "$lte": end_date}
        
        pipeline = [
            {"$match": match_filter},
            {
                "$group": {
                    "_id": None,
                    "total_requests": {"$sum": 1},
                    "total_cost": {"$sum": "$cost"},
                    "total_tokens": {"$sum": "$tokens_used"}
                }
            }
        ]
        
        result = await db.ai_usage.aggregate(pipeline).to_list(1)
        if result:
            return result[0]
        else:
            return {"total_requests": 0, "total_cost": 0.0, "total_tokens": 0}
    
    @staticmethod
    async def get_user_ai_usage(user_id: str):
        db = get_database()
        if db is None:
            return {"total_requests": 0, "total_cost": 0.0, "total_tokens": 0}
        
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": None,
                    "total_requests": {"$sum": 1},
                    "total_cost": {"$sum": "$cost"},
                    "total_tokens": {"$sum": "$tokens_used"}
                }
            }
        ]
        
        result = await db.ai_usage.aggregate(pipeline).to_list(1)
        if result:
            return result[0]
        else:
            return {"total_requests": 0, "total_cost": 0.0, "total_tokens": 0}

class AdminDatabase:
    """Database operations for admin functionality"""
    
    @staticmethod
    async def create_admin_action(action_data: dict):
        db = get_database()
        if db is None:
            raise Exception("Database not connected")
        
        action_data["created_at"] = datetime.utcnow()
        result = await db.admin_actions.insert_one(action_data)
        action_data["_id"] = result.inserted_id
        return action_data
    
    @staticmethod
    async def get_admin_actions(limit: int = 50):
        db = get_database()
        if db is None:
            return []
        
        cursor = db.admin_actions.find({}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(limit)
    
    @staticmethod
    async def get_system_stats():
        db = get_database()
        if db is None:
            return {
                "total_users": 0,
                "total_scans": 0,
                "total_threats": 0,
                "active_users": 0
            }
        
        # Get basic counts
        total_users = await db.users.count_documents({})
        total_scans = await db.email_scans.count_documents({})
        total_threats = await db.threat_logs.count_documents({})
        
        # Get active users (logged in last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users = await db.users.count_documents({
            "last_login": {"$gte": thirty_days_ago}
        })
        
        return {
            "total_users": total_users,
            "total_scans": total_scans,
            "total_threats": total_threats,
            "active_users": active_users
        }

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
        await db.threat_logs.create_index("created_at", background=True)
        await db.feedback.create_index("user_id", background=True)
        await db.ai_usage.create_index("user_id", background=True)
        await db.ai_usage.create_index("created_at", background=True)
        await db.admin_actions.create_index("created_at", background=True)
        await db.domain_reputation.create_index("domain", unique=True, background=True)
        
        # Create collections if they don't exist
        collections = await db.list_collection_names()
        
        required_collections = [
            "users", "email_scans", "user_settings", "threat_logs",
            "feedback", "ai_usage", "admin_actions", "domain_reputation",
            "ai_cache", "organizations"
        ]
        
        for collection_name in required_collections:
            if collection_name not in collections:
                await db.create_collection(collection_name)
        
        logger.info("✅ Database collections initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize collections: {e}")
        # Don't raise, just log the error for development