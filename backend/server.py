import os
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv

# Simple imports
from database import connect_to_mongo, close_mongo_connection, UserDatabase, EmailScanDatabase, SettingsDatabase
from auth import get_password_hash, verify_password, create_access_token, create_refresh_token, verify_token

# Load environment
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple models
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    organization: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class TokenRefresh(BaseModel):
    refresh_token: str

class EmailScanRequest(BaseModel):
    email_subject: str
    email_body: str
    sender: str
    recipient: Optional[str] = None

class LinkScanRequest(BaseModel):
    url: str
    context: Optional[str] = None

# Simple app
app = FastAPI(title="Aman Cybersecurity API", version="1.0.0")

# Simple CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple auth
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    token_data = verify_token(token, "access")
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await UserDatabase.get_user_by_email(token_data["email"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Simple scanning functions
def simple_email_scan(email_data):
    content = email_data.get("email_body", "").lower()
    subject = email_data.get("email_subject", "").lower()
    
    risk_score = 0
    threats = []
    
    # Simple pattern matching
    bad_words = ["urgent", "verify", "suspended", "click here", "act now", "winner"]
    for word in bad_words:
        if word in content or word in subject:
            risk_score += 20
            threats.append(word)
    
    if risk_score >= 60:
        status = "phishing"
    elif risk_score >= 30:
        status = "potential_phishing"
    else:
        status = "safe"
    
    return {
        "status": status,
        "risk_score": min(risk_score, 100),
        "explanation": f"Found {len(threats)} suspicious patterns" if threats else "No threats detected",
        "threats": threats
    }

def simple_link_scan(url):
    risk_score = 0
    threats = []
    
    # Simple URL checks
    bad_domains = ["bit.ly", "tinyurl.com", "suspicious-site.com"]
    for domain in bad_domains:
        if domain in url:
            risk_score += 40
            threats.append(f"suspicious_domain: {domain}")
    
    if risk_score >= 60:
        status = "phishing"
    elif risk_score >= 30:
        status = "potential_phishing"
    else:
        status = "safe"
    
    return {
        "status": status,
        "risk_score": min(risk_score, 100),
        "explanation": f"URL analysis complete" if threats else "URL appears safe",
        "threats": threats,
        "is_shortened": any(x in url for x in ["bit.ly", "tinyurl", "goo.gl"])
    }

# Startup/shutdown
@app.on_event("startup")
async def startup():
    try:
        await connect_to_mongo()
        logger.info("✅ Connected to database")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")

@app.on_event("shutdown")
async def shutdown():
    try:
        await close_mongo_connection()
        logger.info("✅ Database disconnected")
    except Exception as e:
        logger.error(f"❌ Database disconnect failed: {e}")

# Basic endpoints
@app.get("/")
async def root():
    return {"message": "Aman Cybersecurity API", "status": "running"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Auth endpoints
@app.post("/api/auth/register")
async def register(user_data: UserCreate):
    try:
        # Check if user exists
        existing = await UserDatabase.get_user_by_email(user_data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        user_dict = {
            "id": str(uuid.uuid4()),
            "name": user_data.name,
            "email": user_data.email,
            "password": get_password_hash(user_data.password),
            "organization": user_data.organization or "",
            "role": "user",
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        await UserDatabase.create_user(user_dict)
        return {"success": True, "message": "User registered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/auth/login")
async def login(login_data: UserLogin):
    try:
        # Get user
        user = await UserDatabase.get_user_by_email(login_data.email)
        if not user or not verify_password(login_data.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create tokens
        access_token = create_access_token(data={"sub": user["id"], "email": user["email"]})
        refresh_token = create_refresh_token(data={"sub": user["id"], "email": user["email"]})
        
        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "organization": user.get("organization", ""),
                "role": user.get("role", "user")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/auth/refresh")
async def refresh_token_endpoint(refresh_data: TokenRefresh):
    try:
        from auth import decode_refresh_token
        
        payload = decode_refresh_token(refresh_data.refresh_token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user = await UserDatabase.get_user_by_id(payload["sub"])
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        access_token = create_access_token(data={"sub": user["id"], "email": user["email"]})
        
        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

# Scan endpoints
@app.post("/api/scan/email")
async def scan_email(scan_request: EmailScanRequest, current_user = Depends(get_current_user)):
    try:
        # Simple email scan
        scan_result = simple_email_scan(scan_request.dict())
        
        # Store scan result
        scan_data = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "email_subject": scan_request.email_subject,
            "sender": scan_request.sender,
            "recipient": scan_request.recipient,
            "scan_result": scan_result["status"],
            "risk_score": scan_result["risk_score"],
            "explanation": scan_result["explanation"],
            "threats": scan_result["threats"],
            "created_at": datetime.utcnow()
        }
        
        await EmailScanDatabase.create_email_scan(scan_data)
        
        return {
            "id": scan_data["id"],
            "status": scan_result["status"],
            "risk_score": scan_result["risk_score"],
            "explanation": scan_result["explanation"],
            "threats": scan_result["threats"]
        }
    except Exception as e:
        logger.error(f"Email scan error: {e}")
        raise HTTPException(status_code=500, detail="Email scan failed")

@app.post("/api/scan/link")
async def scan_link(scan_request: LinkScanRequest, current_user = Depends(get_current_user)):
    try:
        # Simple link scan
        scan_result = simple_link_scan(scan_request.url)
        
        return {
            "url": scan_request.url,
            "status": scan_result["status"],
            "risk_score": scan_result["risk_score"],
            "explanation": scan_result["explanation"],
            "threats": scan_result["threats"],
            "is_shortened": scan_result["is_shortened"]
        }
    except Exception as e:
        logger.error(f"Link scan error: {e}")
        raise HTTPException(status_code=500, detail="Link scan failed")

# Dashboard endpoints
@app.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user = Depends(get_current_user)):
    try:
        # Get user stats
        stats = await EmailScanDatabase.get_user_stats(current_user["id"])
        
        return {
            "total_scans": stats.get("total_scans", 0),
            "phishing_caught": stats.get("phishing_caught", 0),
            "safe_emails": stats.get("safe_emails", 0),
            "potential_phishing": stats.get("potential_phishing", 0),
            "accuracy_rate": 95.5,
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard stats")

@app.get("/api/dashboard/recent-emails")
async def get_recent_emails(current_user = Depends(get_current_user), limit: int = 10):
    try:
        # Get recent scans
        recent_scans = await EmailScanDatabase.get_recent_scans(current_user["id"], limit)
        
        emails = []
        for scan in recent_scans:
            emails.append({
                "id": scan.get("id", ""),
                "subject": scan.get("email_subject", ""),
                "sender": scan.get("sender", ""),
                "time": "Just now",  # Simplified
                "status": scan.get("scan_result", ""),
                "risk_score": scan.get("risk_score", 0)
            })
        
        return {"emails": emails}
    except Exception as e:
        logger.error(f"Recent emails error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent emails")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server_simple:app", host="0.0.0.0", port=8001, reload=True)