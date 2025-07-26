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

# User database operations
class UserDatabase:
    """Database operations for users"""
    
    @staticmethod
    async def create_user(user_data: dict) -> UserInDB:
        """Create a new user"""
        db = get_database()
        user_data["id"] = str(uuid.uuid4())
        user_data["created_at"] = datetime.utcnow()
        
        await db.users.insert_one(user_data)
        return UserInDB(**user_data)
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[UserInDB]:
        """Get user by email"""
        db = get_database()
        user_doc = await db.users.find_one({"email": email})
        return UserInDB(**user_doc) if user_doc else None
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        db = get_database()
        user_doc = await db.users.find_one({"id": user_id})
        return UserInDB(**user_doc) if user_doc else None
    
    @staticmethod
    async def update_user(user_id: str, update_data: dict) -> bool:
        """Update user data"""
        db = get_database()
        update_data["updated_at"] = datetime.utcnow()
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def get_users_by_organization(organization: str, skip: int = 0, limit: int = 50) -> List[UserInDB]:
        """Get users by organization"""
        db = get_database()
        cursor = db.users.find({"organization": organization}).skip(skip).limit(limit)
        users = []
        async for user_doc in cursor:
            users.append(UserInDB(**user_doc))
        return users
    
    @staticmethod
    async def count_users_by_organization(organization: str) -> int:
        """Count users in organization"""
        db = get_database()
        return await db.users.count_documents({"organization": organization})

# Email scan database operations
class EmailScanDatabase:
    """Database operations for email scans"""
    
    @staticmethod
    async def create_email_scan(scan_data: dict) -> EmailScanResult:
        """Create email scan record"""
        db = get_database()
        scan_data["id"] = str(uuid.uuid4())
        scan_data["scanned_at"] = datetime.utcnow()
        
        await db.email_scans.insert_one(scan_data)
        return EmailScanResult(**scan_data)
    
    @staticmethod
    async def get_email_scan(scan_id: str) -> Optional[EmailScanResult]:
        """Get email scan by ID"""
        db = get_database()
        scan_doc = await db.email_scans.find_one({"id": scan_id})
        return EmailScanResult(**scan_doc) if scan_doc else None
    
    @staticmethod
    async def get_user_recent_scans(user_id: str, limit: int = 10) -> List[EmailScanResult]:
        """Get user's recent email scans"""
        db = get_database()
        cursor = db.email_scans.find({"user_id": user_id}).sort("scanned_at", -1).limit(limit)
        scans = []
        async for scan_doc in cursor:
            scans.append(EmailScanResult(**scan_doc))
        return scans
    
    @staticmethod
    async def get_dashboard_stats(user_id: Optional[str] = None, organization: Optional[str] = None) -> dict:
        """Get dashboard statistics"""
        db = get_database()
        
        # Build query based on scope
        query = {}
        if user_id:
            query["user_id"] = user_id
        elif organization:
            # Get all users in organization first
            org_users = await UserDatabase.get_users_by_organization(organization)
            user_ids = [user.id for user in org_users]
            query["user_id"] = {"$in": user_ids}
        
        # Get counts by status
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$scan_result",
                "count": {"$sum": 1}
            }}
        ]
        
        results = {}
        async for result in db.email_scans.aggregate(pipeline):
            results[result["_id"]] = result["count"]
        
        return {
            "phishing_caught": results.get("phishing", 0),
            "safe_emails": results.get("safe", 0),
            "potential_phishing": results.get("potential_phishing", 0),
            "total_scans": sum(results.values())
        }
    
    @staticmethod
    async def get_scans_by_date_range(
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> List[EmailScanResult]:
        """Get scans within date range"""
        db = get_database()
        
        query = {
            "scanned_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        if user_id:
            query["user_id"] = user_id
        
        cursor = db.email_scans.find(query).sort("scanned_at", -1)
        scans = []
        async for scan_doc in cursor:
            scans.append(EmailScanResult(**scan_doc))
        return scans
    
    @staticmethod
    async def get_threat_trends(days: int = 30) -> List[dict]:
        """Get threat trends over time"""
        db = get_database()
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {"$match": {"scanned_at": {"$gte": start_date}}},
            {"$group": {
                "_id": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$scanned_at"}},
                    "status": "$scan_result"
                },
                "count": {"$sum": 1}
            }},
            {"$group": {
                "_id": "$_id.date",
                "data": {
                    "$push": {
                        "status": "$_id.status",
                        "count": "$count"
                    }
                }
            }},
            {"$sort": {"_id": 1}}
        ]
        
        trends = []
        async for trend in db.email_scans.aggregate(pipeline):
            trend_data = {"date": trend["_id"], "safe": 0, "phishing": 0, "potential_phishing": 0}
            for item in trend["data"]:
                trend_data[item["status"]] = item["count"]
            trends.append(trend_data)
        
        return trends

# Threat intelligence database operations
class ThreatDatabase:
    """Database operations for threat intelligence"""
    
    @staticmethod
    async def add_threat_domain(domain_data: dict) -> ThreatLog:
        """Add threat domain to database"""
        db = get_database()
        domain_data["id"] = str(uuid.uuid4())
        domain_data["detected_at"] = datetime.utcnow()
        
        await db.threat_logs.insert_one(domain_data)
        return ThreatLog(**domain_data)
    
    @staticmethod
    async def check_domain_reputation(domain: str) -> Optional[dict]:
        """Check domain reputation"""
        db = get_database()
        threat_doc = await db.threat_domains.find_one({"domain": domain})
        return threat_doc
    
    @staticmethod
    async def update_domain_reputation(domain: str, risk_score: float, threat_type: str):
        """Update domain reputation"""
        db = get_database()
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
    
    @staticmethod
    async def get_recent_threats(limit: int = 50) -> List[ThreatLog]:
        """Get recent threat logs"""
        db = get_database()
        cursor = db.threat_logs.find({"is_active": True}).sort("detected_at", -1).limit(limit)
        threats = []
        async for threat_doc in cursor:
            threats.append(ThreatLog(**threat_doc))
        return threats

# Feedback database operations
class FeedbackDatabase:
    """Database operations for user feedback"""
    
    @staticmethod
    async def create_feedback(feedback_data: dict) -> FeedbackResponse:
        """Create feedback record"""
        db = get_database()
        feedback_data["id"] = str(uuid.uuid4())
        feedback_data["created_at"] = datetime.utcnow()
        
        await db.feedback.insert_one(feedback_data)
        return FeedbackResponse(**feedback_data)
    
    @staticmethod
    async def get_feedback_for_scan(scan_id: str) -> Optional[FeedbackResponse]:
        """Get feedback for specific scan"""
        db = get_database()
        feedback_doc = await db.feedback.find_one({"scan_id": scan_id})
        return FeedbackResponse(**feedback_doc) if feedback_doc else None
    
    @staticmethod
    async def get_user_feedback(user_id: str, skip: int = 0, limit: int = 50) -> List[FeedbackResponse]:
        """Get user's feedback history"""
        db = get_database()
        cursor = db.feedback.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
        feedback_list = []
        async for feedback_doc in cursor:
            feedback_list.append(FeedbackResponse(**feedback_doc))
        return feedback_list

# Organization database operations
class OrganizationDatabase:
    """Database operations for organizations"""
    
    @staticmethod
    async def create_organization(org_data: dict) -> OrganizationResponse:
        """Create organization"""
        db = get_database()
        org_data["id"] = str(uuid.uuid4())
        org_data["created_at"] = datetime.utcnow()
        
        await db.organizations.insert_one(org_data)
        return OrganizationResponse(**org_data)
    
    @staticmethod
    async def get_organization(org_id: str) -> Optional[OrganizationResponse]:
        """Get organization by ID"""
        db = get_database()
        org_doc = await db.organizations.find_one({"id": org_id})
        return OrganizationResponse(**org_doc) if org_doc else None
    
    @staticmethod
    async def get_organization_by_name(name: str) -> Optional[OrganizationResponse]:
        """Get organization by name"""
        db = get_database()
        org_doc = await db.organizations.find_one({"name": name})
        return OrganizationResponse(**org_doc) if org_doc else None

# Settings database operations
class SettingsDatabase:
    """Database operations for settings"""
    
    @staticmethod
    async def get_user_settings(user_id: str) -> dict:
        """Get user settings"""
        db = get_database()
        settings_doc = await db.user_settings.find_one({"user_id": user_id})
        if settings_doc:
            return settings_doc
        
        # Return default settings
        default_settings = {
            "user_id": user_id,
            "email_notifications": True,
            "real_time_scanning": True,
            "block_suspicious_links": False,
            "scan_attachments": True,
            "share_threat_intelligence": True
        }
        await db.user_settings.insert_one(default_settings)
        return default_settings
    
    @staticmethod
    async def update_user_settings(user_id: str, settings: dict) -> bool:
        """Update user settings"""
        db = get_database()
        settings["updated_at"] = datetime.utcnow()
        result = await db.user_settings.update_one(
            {"user_id": user_id},
            {"$set": settings},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None