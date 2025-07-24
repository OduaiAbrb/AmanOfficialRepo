from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

load_dotenv()

app = FastAPI(title="Aman Cybersecurity Platform", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.aman_db

# Pydantic models
class User(BaseModel):
    id: str
    email: EmailStr
    name: str
    organization: Optional[str] = None
    created_at: datetime

class EmailScan(BaseModel):
    id: str
    user_id: str
    email_subject: str
    sender: str
    scan_result: str  # "safe", "phishing", "potential_phishing"
    threat_source: Optional[str] = None  # "body", "link", "image", "file"
    scanned_at: datetime

class DashboardStats(BaseModel):
    phishing_caught: int
    safe_emails: int
    potential_phishing: int

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Aman Cybersecurity Platform"}

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    # Mock data for now - will be replaced with real database queries
    return DashboardStats(
        phishing_caught=12,
        safe_emails=485,
        potential_phishing=7
    )

@app.get("/api/dashboard/recent-emails")
async def get_recent_emails():
    # Mock data for now
    recent_emails = [
        {
            "id": str(uuid.uuid4()),
            "subject": "Important Security Update Required",
            "sender": "security@bank-notification.com",
            "time": "2 hours ago",
            "status": "phishing"
        },
        {
            "id": str(uuid.uuid4()),
            "subject": "Weekly Team Meeting Reminder",
            "sender": "team@company.com",
            "time": "3 hours ago",
            "status": "safe"
        },
        {
            "id": str(uuid.uuid4()),
            "subject": "Verify Your Account Information",
            "sender": "noreply@suspicious-domain.net",
            "time": "5 hours ago",
            "status": "potential_phishing"
        },
        {
            "id": str(uuid.uuid4()),
            "subject": "Project Update - Q4 Report",
            "sender": "manager@company.com",
            "time": "1 day ago",
            "status": "safe"
        },
        {
            "id": str(uuid.uuid4()),
            "subject": "Urgent: Claim Your Prize Now!",
            "sender": "prizes@win-now.fake",
            "time": "2 days ago",
            "status": "phishing"
        }
    ]
    return {"emails": recent_emails}

@app.get("/api/user/profile")
async def get_user_profile():
    # Mock user profile data
    return {
        "id": str(uuid.uuid4()),
        "name": "John Doe",
        "email": "john.doe@company.com",
        "organization": "TechCorp Inc.",
        "joined": "2024-01-15",
        "role": "Security Analyst"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)