from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

# Database instance
db_instance = Database()

async def connect_to_mongo():
    """Create database connection"""
    MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_instance.client = AsyncIOMotorClient(MONGO_URL)
    db_instance.database = db_instance.client.aman_db
    
    # Test the connection
    try:
        await db_instance.client.admin.command('ping')
        print("✅ MongoDB connection successful")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

async def close_mongo_connection():
    """Close database connection"""
    if db_instance.client:
        db_instance.client.close()
        print("MongoDB connection closed")

def get_database():
    """Get database instance"""
    return db_instance.database

# Collections
async def init_collections():
    """Initialize database collections with proper indexes"""
    db = get_database()
    
    # Users collection
    await db.users.create_index("email", unique=True)
    await db.users.create_index("organization")
    
    # Email scans collection
    await db.email_scans.create_index("user_id")
    await db.email_scans.create_index("scanned_at")
    await db.email_scans.create_index("scan_result")
    
    # Threat logs collection
    await db.threat_logs.create_index("domain")
    await db.threat_logs.create_index("created_at")
    
    # Organizations collection
    await db.organizations.create_index("name", unique=True)
    
    # Unblock requests collection
    await db.unblock_requests.create_index("user_id")
    await db.unblock_requests.create_index("status")
    
    # Feedback collection
    await db.feedback.create_index("user_id")
    await db.feedback.create_index("created_at")
    
    print("✅ Database collections initialized")