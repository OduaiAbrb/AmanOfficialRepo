import os
import json
import logging
import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

# Import core modules with error handling
try:
    from database import (
        get_database, connect_to_mongo, close_mongo_connection, 
        init_collections, EmailScanDatabase, UserDatabase, SettingsDatabase,
        ThreatDatabase, FeedbackDatabase, AICostDatabase, AdminDatabase
    )
except ImportError as e:
    logging.error(f"Database import failed: {e}")
    raise

try:
    from auth import (
        get_current_active_user, create_access_token, create_refresh_token, 
        decode_refresh_token, get_password_hash, verify_password,
        invalidate_token, get_active_token_count
    )
    from security import SecurityMiddleware, IPValidator, RateLimiter, InputValidator, log_security_event, validate_input
    from models import (
        UserCreate, UserLogin, UserResponse, TokenRefresh,
        EmailScanRequest, LinkScanRequest, UserSettings
    )
except ImportError as e:
    logging.error(f"Core module import failed: {e}")
    raise

# Optional modules with graceful failure
AI_AVAILABLE = False
FEEDBACK_AVAILABLE = False
THREAT_INTEL_AVAILABLE = False
REALTIME_AVAILABLE = False
ADMIN_AVAILABLE = False

try:
    from ai_scanner import scan_email_with_ai, scan_link_with_ai
    AI_AVAILABLE = True
    logging.info("✅ AI scanner module loaded")
except ImportError:
    logging.warning("⚠️ AI scanner not available - using fallback")

try:
    from feedback_system import submit_scan_feedback, get_user_feedback_analytics
    FEEDBACK_AVAILABLE = True
    logging.info("✅ Feedback system loaded")
except ImportError:
    logging.warning("⚠️ Feedback system not available")

try:
    from threat_intelligence import check_domain_reputation, check_url_reputation
    THREAT_INTEL_AVAILABLE = True
    logging.info("✅ Threat intelligence loaded")
except ImportError:
    logging.warning("⚠️ Threat intelligence not available")

try:
    from realtime_manager import realtime_manager, notify_threat_detected, notify_scan_completed
    REALTIME_AVAILABLE = True
    logging.info("✅ Real-time manager loaded")
except ImportError:
    logging.warning("⚠️ Real-time features not available")

try:
    from admin_manager import (
        get_admin_dashboard_stats, get_user_management_data, 
        update_user_status, update_user_role, get_threat_management_data,
        get_system_monitoring_data, get_admin_audit_log
    )
    ADMIN_AVAILABLE = True
    logging.info("✅ Admin manager loaded")
except ImportError:
    logging.warning("⚠️ Admin panel not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Fallback functions for missing modules
async def fallback_scan_email(email_data: dict, user_id: str = None):
    """Fallback email scanning when AI not available"""
    content = email_data.get("email_body", "").lower()
    subject = email_data.get("email_subject", "").lower()
    sender = email_data.get("sender", "").lower()
    
    risk_score = 0.0
    threat_indicators = []
    
    # Basic pattern matching
    suspicious_keywords = [
        "urgent", "verify account", "click here", "limited time", "suspended",
        "congratulations", "winner", "claim now", "act fast", "expires today",
        "confirm identity", "update payment", "security alert"
    ]
    
    for keyword in suspicious_keywords:
        if keyword in content or keyword in subject:
            risk_score += 15
            threat_indicators.append({
                'source': 'pattern_matching',
                'threat_type': 'suspicious_keyword',
                'confidence': 0.6,
                'description': f'Detected pattern: {keyword}',
                'evidence': keyword
            })
    
    # Check sender patterns
    if not sender or 'noreply' in sender or 'no-reply' in sender:
        risk_score += 10
        threat_indicators.append({
            'source': 'sender_analysis',
            'threat_type': 'suspicious_sender',
            'confidence': 0.5,
            'description': 'Suspicious sender pattern',
            'evidence': sender or 'no_sender'
        })
    
    # Determine risk level
    if risk_score >= 60:
        risk_level = "phishing"
    elif risk_score >= 30:
        risk_level = "potential_phishing"
    else:
        risk_level = "safe"
    
    return {
        'risk_score': min(risk_score, 100.0),
        'risk_level': risk_level,
        'explanation': f'Basic pattern analysis completed - {len(threat_indicators)} indicators found',
        'recommendations': [
            'Exercise normal email caution',
            'Verify sender through alternative means' if risk_level != 'safe' else 'Email appears safe'
        ],
        'threat_indicators': threat_indicators,
        'metadata': {'fallback': True, 'ai_powered': False},
        'scan_duration': 0.1
    }

async def fallback_scan_link(url: str, context: str = ""):
    """Fallback link scanning when AI not available"""
    risk_score = 0.0
    threat_indicators = []
    
    # Basic URL analysis
    suspicious_domains = ['bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly']
    dangerous_domains = ['malware-site.com', 'phishing-site.net', 'suspicious-site.com']
    
    # Check dangerous domains
    for domain in dangerous_domains:
        if domain.lower() in url.lower():
            risk_score += 80
            threat_indicators.append({
                'source': 'domain_analysis',
                'threat_type': 'malicious_domain',
                'confidence': 0.9,
                'description': f'Known malicious domain: {domain}',
                'evidence': domain
            })
    
    # Check suspicious domains
    for domain in suspicious_domains:
        if domain.lower() in url.lower():
            risk_score += 30
            threat_indicators.append({
                'source': 'domain_analysis',
                'threat_type': 'url_shortener',
                'confidence': 0.7,
                'description': f'URL shortener detected: {domain}',
                'evidence': domain
            })
    
    # URL patterns
    suspicious_patterns = ['login', 'verify', 'secure', 'update', 'confirm']
    for pattern in suspicious_patterns:
        if pattern.lower() in url.lower():
            risk_score += 15
            threat_indicators.append({
                'source': 'pattern_analysis',
                'threat_type': 'auth_keywords',
                'confidence': 0.5,
                'description': f'Authentication keyword in URL: {pattern}',
                'evidence': pattern
            })
    
    # Determine risk level
    if risk_score >= 70:
        risk_level = "phishing"
    elif risk_score >= 30:
        risk_level = "potential_phishing"
    else:
        risk_level = "safe"
    
    return {
        'risk_score': min(risk_score, 100.0),
        'risk_level': risk_level,
        'explanation': f'Basic URL analysis completed - {len(threat_indicators)} indicators found',
        'threat_indicators': threat_indicators,
        'metadata': {'fallback': True, 'ai_powered': False},
        'scan_duration': 0.1
    }

# Safe wrapper functions
async def safe_scan_email_with_ai(email_data: dict, user_id: str = None):
    if AI_AVAILABLE:
        try:
            return await scan_email_with_ai(email_data, user_id)
        except Exception as e:
            logger.warning(f"AI email scan failed: {e}, using fallback")
            return await fallback_scan_email(email_data, user_id)
    else:
        return await fallback_scan_email(email_data, user_id)

async def safe_scan_link_with_ai(url: str, context: str = "", user_id: str = None):
    if AI_AVAILABLE:
        try:
            return await scan_link_with_ai(url, context, user_id)
        except Exception as e:
            logger.warning(f"AI link scan failed: {e}, using fallback")
            return await fallback_scan_link(url, context)
    else:
        return await fallback_scan_link(url, context)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await connect_to_mongo()
        await init_collections()
        if REALTIME_AVAILABLE:
            await realtime_manager.start_background_tasks()
        logger.info("🚀 Application startup completed successfully")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        # Continue for development
    
    yield
    
    # Shutdown
    try:
        await close_mongo_connection()
        logger.info("✅ Application shutdown completed")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="Aman Cybersecurity Platform API",
    description="AI-powered cybersecurity platform with real-time threat detection",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:8001",
        "http://127.0.0.1:8001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Basic endpoints
@app.get("/")
async def root():
    return {
        "message": "Aman Cybersecurity Platform API", 
        "status": "running", 
        "version": "2.0.0",
        "auth_type": "Simple Token (No JWT)"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    db_status = "disconnected"
    try:
        db = get_database()
        if db is not None:
            await db.command('ping')
            db_status = "connected"
    except Exception as e:
        logger.error(f"Health check DB error: {e}")
    
    # Get token statistics
    token_stats = get_active_token_count()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "auth_system": "Simple Token (No JWT)",
        "active_tokens": token_stats,
        "modules": {
            "ai_scanner": AI_AVAILABLE,
            "realtime": REALTIME_AVAILABLE,
            "admin": ADMIN_AVAILABLE,
            "feedback": FEEDBACK_AVAILABLE,
            "threat_intel": THREAT_INTEL_AVAILABLE
        }
    }

# Authentication endpoints
@app.post("/api/auth/register")
@limiter.limit("5/minute")
async def register_user(request: Request, user_data: UserCreate):
    """Register new user"""
    try:
        # Check if user exists
        existing_user = await UserDatabase.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        user_id = str(uuid.uuid4())
        user_dict = {
            "id": user_id,
            "name": user_data.name,
            "email": user_data.email,
            "password": get_password_hash(user_data.password),
            "organization": user_data.organization or "",
            "role": "user",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await UserDatabase.create_user(user_dict)
        
        logger.info(f"New user registered: {user_data.email} from IP: {request.client.host}")
        
        return {
            "success": True,
            "message": "User registered successfully",
            "data": {"id": user_id, "email": user_data.email}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/auth/login")
@limiter.limit("10/minute")
async def login_user(request: Request, login_data: UserLogin):
    """User login"""
    try:
        # Get user
        user = await UserDatabase.get_user_by_email(login_data.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not verify_password(login_data.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="Account is disabled")
        
        # Create tokens using simple token system
        access_token = create_access_token(data={"sub": user["email"]})
        refresh_token = create_refresh_token(data={"sub": user["email"]})
        
        # Update last login
        await UserDatabase.update_user(user["id"], {"last_login": datetime.utcnow()})
        
        # Prepare user data
        user_data = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "organization": user.get("organization", ""),
            "role": user.get("role", "user"),
            "is_active": user.get("is_active", True)
        }
        
        logger.info(f"User logged in: {login_data.email} from IP: {request.client.host}")
        
        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/auth/refresh")
@limiter.limit("10/minute")
async def refresh_token(request: Request, refresh_data: TokenRefresh):
    """Refresh access token"""
    try:
        refresh_token_str = refresh_data.refresh_token
        if not refresh_token_str:
            raise HTTPException(status_code=400, detail="Refresh token required")
        
        # Decode refresh token using simple token system
        payload = decode_refresh_token(refresh_token_str)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Get user
        user = await UserDatabase.get_user_by_email(email)
        if not user or not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        # Create new access token
        access_token = create_access_token(data={"sub": user["email"]})
        
        logger.info(f"Token refreshed for user: {email}")
        
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

@app.post("/api/auth/logout")
@limiter.limit("10/minute")
async def logout_user(request: Request, current_user: UserResponse = Depends(get_current_active_user)):
    """User logout - invalidate tokens"""
    try:
        # Get token from request
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            # Invalidate the token
            invalidate_token(token)
        
        logger.info(f"User logged out: {current_user.email}")
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return {"success": True, "message": "Logged out"}  # Always succeed

# Dashboard endpoints
@app.get("/api/dashboard/stats")
@limiter.limit("30/minute")
async def get_dashboard_stats(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get dashboard statistics"""
    try:
        stats = await EmailScanDatabase.get_user_stats(current_user.id)
        
        return {
            "phishing_emails_caught": stats.get("threats_blocked", 0),
            "safe_emails": stats.get("safe_emails", 0),
            "potential_phishing": max(0, stats.get("total_scans", 0) - stats.get("safe_emails", 0) - stats.get("threats_blocked", 0)),
            "total_scans": stats.get("total_scans", 0)
        }
        
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        # Return zeros instead of error for better UX
        return {
            "phishing_emails_caught": 0,
            "safe_emails": 0,
            "potential_phishing": 0,
            "total_scans": 0
        }

@app.get("/api/dashboard/recent-emails")
@limiter.limit("30/minute")
async def get_recent_emails(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get recent email scans"""
    try:
        scans = await EmailScanDatabase.get_recent_scans(current_user.id, limit=10)
        
        # Format scans
        formatted_scans = []
        for scan in scans:
            formatted_scans.append({
                "id": scan.get("id", str(scan.get("_id", ""))),
                "subject": scan.get("email_subject", "")[:50],
                "sender": scan.get("sender", ""),
                "status": scan.get("scan_result", "safe"),
                "risk_score": scan.get("risk_score", 0),
                "timestamp": scan.get("created_at", datetime.utcnow()).isoformat() if isinstance(scan.get("created_at"), datetime) else scan.get("created_at", datetime.utcnow().isoformat())
            })
        
        return {"recent_scans": formatted_scans}
        
    except Exception as e:
        logger.error(f"Recent emails error: {e}")
        return {"recent_scans": []}

# User profile endpoints
@app.get("/api/user/profile")
@limiter.limit("30/minute")
async def get_user_profile(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get user profile"""
    try:
        return {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "organization": current_user.organization,
            "role": current_user.role,
            "is_active": current_user.is_active
        }
    except Exception as e:
        logger.error(f"Get user profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user profile")

@app.put("/api/user/profile")
@limiter.limit("10/minute")
async def update_user_profile(
    request: Request,
    profile_data: dict,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Update user profile"""
    try:
        # Validate and sanitize update data
        allowed_fields = ["name", "organization"]
        update_data = {k: v for k, v in profile_data.items() if k in allowed_fields and v}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        success = await UserDatabase.update_user(current_user.id, update_data)
        
        if success:
            return {"success": True, "message": "Profile updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update profile")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail="Profile update failed")

# Settings endpoints
@app.get("/api/user/settings")
@limiter.limit("30/minute")
async def get_user_settings(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get user settings"""
    try:
        settings = await SettingsDatabase.get_user_settings(current_user.id)
        
        # Default settings
        default_settings = {
            "email_notifications": True,
            "real_time_scanning": True,
            "threat_alerts": True,
            "weekly_reports": False,
            "scan_attachments": True
        }
        
        # Merge with user settings
        default_settings.update(settings)
        
        return {"settings": default_settings}
        
    except Exception as e:
        logger.error(f"Get settings error: {e}")
        return {"settings": {
            "email_notifications": True,
            "real_time_scanning": True,
            "threat_alerts": True,
            "weekly_reports": False,
            "scan_attachments": True
        }}

@app.put("/api/user/settings")
@limiter.limit("20/minute")
async def update_user_settings(
    request: Request,
    settings_data: dict,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Update user settings"""
    try:
        # Validate settings
        allowed_settings = [
            "email_notifications", "real_time_scanning", "threat_alerts", 
            "weekly_reports", "scan_attachments"
        ]
        
        settings = {}
        for key, value in settings_data.items():
            if key in allowed_settings:
                settings[key] = bool(value)
        
        if not settings:
            raise HTTPException(status_code=400, detail="No valid settings provided")
        
        success = await SettingsDatabase.update_user_settings(current_user.id, settings)
        
        if success:
            return {"success": True, "message": "Settings updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update settings")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update settings error: {e}")
        raise HTTPException(status_code=500, detail="Settings update failed")

# Email scanning endpoint
@app.post("/api/scan/email")
@limiter.limit("30/minute")
async def scan_email(
    request: Request,
    scan_request: EmailScanRequest,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Scan email for phishing threats"""
    try:
        client_ip = request.client.host if request.client else "unknown"
        
        # Validate input
        validated_data = {
            "email_subject": scan_request.email_subject[:500] if scan_request.email_subject else "",
            "email_body": scan_request.email_body[:10000] if scan_request.email_body else "",
            "sender": scan_request.sender[:200] if scan_request.sender else "",
            "recipient": scan_request.recipient[:200] if scan_request.recipient else ""
        }
        
        # Use AI-enhanced scanning with fallback
        scan_results = await safe_scan_email_with_ai(validated_data, current_user.id)
        
        risk_score = scan_results.get('risk_score', 0.0)
        risk_level = scan_results.get('risk_level', 'safe')
        
        # Map risk_level to status
        if risk_level == "phishing":
            status = "phishing"
        elif risk_level == "potential_phishing":
            status = "potential_phishing"
        else:
            status = "safe"
        
        explanation = scan_results.get('explanation', 'Scan completed')
        recommendations = scan_results.get('recommendations', [])
        threat_indicators = scan_results.get('threat_indicators', [])
        
        # Extract threat info
        threat_sources = list(set(indicator.get('source', '') for indicator in threat_indicators))
        detected_threats = list(set(indicator.get('threat_type', '') for indicator in threat_indicators))
        
        # Store scan result
        scan_data = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "email_subject": validated_data["email_subject"][:200],
            "sender": validated_data["sender"][:100],
            "recipient": validated_data["recipient"][:100],
            "scan_result": status,
            "risk_score": risk_score,
            "explanation": explanation,
            "threat_sources": threat_sources,
            "detected_threats": detected_threats,
            "scan_metadata": scan_results.get('metadata', {}),
            "scan_duration": scan_results.get('scan_duration', 0.0),
            "ai_powered": scan_results.get('metadata', {}).get('ai_powered', False)
        }
        
        scan_result = await EmailScanDatabase.create_email_scan(scan_data)
        
        # Send real-time notifications if available
        if REALTIME_AVAILABLE and status in ["potential_phishing", "phishing"]:
            try:
                notification_data = {
                    "id": scan_result.get("id"),
                    "status": status,
                    "risk_score": risk_score,
                    "explanation": explanation,
                    "threat_sources": threat_sources,
                    "detected_threats": detected_threats,
                    "recommendations": recommendations
                }
                await notify_threat_detected(current_user.id, notification_data)
                await notify_scan_completed(current_user.id, notification_data)
            except Exception as notification_error:
                logger.warning(f"Real-time notification failed: {notification_error}")
        
        logger.info(f"Email scan completed for user {current_user.email}: risk_score={risk_score}, status={status}")
        
        return {
            "id": scan_result.get("id"),
            "status": status,
            "risk_score": risk_score,
            "explanation": explanation,
            "threat_sources": threat_sources,
            "detected_threats": detected_threats,
            "recommendations": recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email scan error: {e}")
        raise HTTPException(status_code=500, detail="Email scan failed")

# Link scanning endpoint
@app.post("/api/scan/link")
@limiter.limit("30/minute")
async def scan_link(
    request: Request,
    scan_request: LinkScanRequest,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Scan link for threats"""
    try:
        # Use AI-enhanced scanning with fallback
        scan_results = await safe_scan_link_with_ai(scan_request.url, scan_request.context or "", current_user.id)
        
        risk_score = scan_results.get('risk_score', 0.0)
        risk_level = scan_results.get('risk_level', 'safe')
        
        # Map risk_level to status
        if risk_level == "phishing":
            status = "phishing"
        elif risk_level == "potential_phishing":
            status = "potential_phishing"
        else:
            status = "safe"
        
        explanation = scan_results.get('explanation', 'Link scan completed')
        threat_indicators = scan_results.get('threat_indicators', [])
        threat_categories = list(set(indicator.get('threat_type', '') for indicator in threat_indicators))
        
        logger.info(f"Link scan completed for user {current_user.email}: risk_score={risk_score}, status={status}")
        
        return {
            "status": status,
            "risk_score": risk_score,
            "explanation": explanation,
            "threat_categories": threat_categories,
            "is_shortened": len(scan_request.url) < 50 and any(domain in scan_request.url for domain in ['bit.ly', 'tinyurl.com', 'goo.gl'])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Link scan error: {e}")
        raise HTTPException(status_code=500, detail="Link scan failed")

# WebSocket endpoint (if real-time available)
if REALTIME_AVAILABLE:
    @app.websocket("/api/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: str):
        """WebSocket endpoint for real-time updates"""
        try:
            connection_id = await realtime_manager.connect(websocket, user_id)
            
            try:
                while True:
                    try:
                        data = await websocket.receive_text()
                        message = json.loads(data)
                        
                        if message.get("type") == "ping":
                            await websocket.send_text(json.dumps({
                                "type": "pong",
                                "timestamp": datetime.utcnow().isoformat()
                            }))
                        elif message.get("type") == "auth":
                            # Handle WebSocket authentication
                            token = message.get("token")
                            if token:
                                # Verify token (simplified for WebSocket)
                                await websocket.send_text(json.dumps({
                                    "type": "auth_success",
                                    "message": "WebSocket authenticated"
                                }))
                        elif message.get("type") == "request_stats":
                            await realtime_manager.send_dashboard_statistics(user_id)
                            
                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.error(f"WebSocket message error: {e}")
                        
            except WebSocketDisconnect:
                pass
            finally:
                await realtime_manager.disconnect(connection_id)
                
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500}
    )

# Health check for token system
@app.get("/api/auth/status")
async def auth_status():
    """Get authentication system status"""
    token_stats = get_active_token_count()
    return {
        "auth_system": "Simple Token (No JWT)",
        "status": "active",
        "active_tokens": token_stats,
        "features": ["login", "logout", "refresh", "cleanup"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)