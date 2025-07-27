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

# Profile endpoints
@app.get("/api/user/profile")
async def get_profile(current_user = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "organization": current_user.get("organization", ""),
        "role": current_user.get("role", "user")
    }

@app.put("/api/user/profile")
async def update_profile(profile_data: dict, current_user = Depends(get_current_user)):
    try:
        allowed_fields = ["name", "organization"]
        update_data = {k: v for k, v in profile_data.items() if k in allowed_fields}
        
        if update_data:
            await UserDatabase.update_user(current_user["id"], update_data)
            return {"success": True, "message": "Profile updated"}
        else:
            raise HTTPException(status_code=400, detail="No valid fields to update")
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail="Profile update failed")

# Scanning endpoints
@app.post("/api/scan/email")
async def scan_email(scan_request: EmailScanRequest, current_user = Depends(get_current_user)):
    try:
        # Simple validation
        email_data = {
            "email_subject": scan_request.email_subject[:500],
            "email_body": scan_request.email_body[:5000],
            "sender": scan_request.sender[:200],
            "recipient": scan_request.recipient[:200] if scan_request.recipient else ""
        }
        
        # Scan email
        result = simple_email_scan(email_data)
        
        # Store result
        scan_data = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "email_subject": email_data["email_subject"],
            "sender": email_data["sender"],
            "scan_result": result["status"],
            "risk_score": result["risk_score"],
            "explanation": result["explanation"],
            "created_at": datetime.utcnow()
        }
        
        await EmailScanDatabase.create_email_scan(scan_data)
        
        return {
            "id": scan_data["id"],
            "status": result["status"],
            "risk_score": result["risk_score"],
            "explanation": result["explanation"],
            "threat_sources": result["threats"],
            "detected_threats": result["threats"],
            "recommendations": ["Be cautious with this email"] if result["threats"] else ["Email appears safe"]
        }
        
    except Exception as e:
        logger.error(f"Email scan error: {e}")
        raise HTTPException(status_code=500, detail="Email scan failed")

@app.post("/api/scan/link")
async def scan_link(scan_request: LinkScanRequest, current_user = Depends(get_current_user)):
    try:
        result = simple_link_scan(scan_request.url)
        
        return {
            "url": scan_request.url,
            "status": result["status"],
            "risk_score": result["risk_score"],
            "explanation": result["explanation"],
            "threat_categories": result["threats"],
            "is_shortened": result["is_shortened"]
        }
        
    except Exception as e:
        logger.error(f"Link scan error: {e}")
        raise HTTPException(status_code=500, detail="Link scan failed")

# Dashboard endpoints
@app.get("/api/dashboard/stats")
async def get_stats(current_user = Depends(get_current_user)):
    try:
        stats = await EmailScanDatabase.get_user_stats(current_user["id"])
        return {
            "phishing_emails_caught": stats.get("threats_blocked", 0),
            "safe_emails": stats.get("safe_emails", 0),
            "potential_phishing": stats.get("potential_threats", 0),
            "total_scans": stats.get("total_scans", 0)
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {"phishing_emails_caught": 0, "safe_emails": 0, "potential_phishing": 0, "total_scans": 0}

@app.get("/api/dashboard/recent-emails")
async def get_recent_emails(current_user = Depends(get_current_user)):
    try:
        scans = await EmailScanDatabase.get_recent_scans(current_user["id"], limit=10)
        recent_scans = []
        for scan in scans:
            recent_scans.append({
                "id": str(scan.get("_id", "")),
                "subject": scan.get("email_subject", "")[:50],
                "sender": scan.get("sender", ""),
                "status": scan.get("scan_result", "safe"),
                "risk_score": scan.get("risk_score", 0),
                "timestamp": str(scan.get("created_at", datetime.utcnow()))
            })
        return {"recent_scans": recent_scans}
    except Exception as e:
        logger.error(f"Recent emails error: {e}")
        return {"recent_scans": []}

# Settings endpoints
@app.get("/api/user/settings")
async def get_settings(current_user = Depends(get_current_user)):
    try:
        settings = await SettingsDatabase.get_user_settings(current_user["id"])
        default_settings = {
            "email_notifications": True,
            "real_time_scanning": True,
            "threat_alerts": True,
            "weekly_reports": False,
            "scan_attachments": True
        }
        default_settings.update(settings or {})
        return {"settings": default_settings}
    except Exception as e:
        logger.error(f"Settings error: {e}")
        return {"settings": {"email_notifications": True, "real_time_scanning": True, "threat_alerts": True}}

@app.put("/api/user/settings")
async def update_settings(settings_data: dict, current_user = Depends(get_current_user)):
    try:
        allowed = ["email_notifications", "real_time_scanning", "threat_alerts", "weekly_reports", "scan_attachments"]
        settings = {k: bool(v) for k, v in settings_data.items() if k in allowed}
        
        if settings:
            await SettingsDatabase.update_user_settings(current_user["id"], settings)
            return {"success": True, "message": "Settings updated"}
        else:
            raise HTTPException(status_code=400, detail="No valid settings")
    except Exception as e:
        logger.error(f"Settings update error: {e}")
        raise HTTPException(status_code=500, detail="Settings update failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)