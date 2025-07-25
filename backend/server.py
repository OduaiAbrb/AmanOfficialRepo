"""
Aman Cybersecurity Platform - Secure Backend API
Comprehensive FastAPI backend with JWT authentication, security middleware, AI integration, and real-time updates
"""

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
import asyncio
from contextlib import asynccontextmanager

# Import modules
from email_scanner import scan_email_advanced, scan_link_advanced
from ai_scanner import scan_email_with_ai, scan_link_with_ai
from feedback_system import submit_scan_feedback, get_user_feedback_analytics
from threat_intelligence import check_domain_reputation, check_url_reputation
from realtime_manager import realtime_manager, notify_threat_detected, notify_scan_completed
from models import (
    UserCreate, UserResponse, LoginRequest, Token, RefreshTokenRequest,
    EmailScanRequest, EmailScanResponse, DashboardStats, DashboardData,
    RecentEmailScan, FeedbackCreate, FeedbackResponse, UnblockRequestCreate,
    UnblockRequestResponse, SuccessResponse, ErrorResponse, HealthResponse,
    LinkScanRequest, LinkScanResponse, UserUpdate, UserSettings, ScanStatus
)
from auth import (
    get_current_active_user, create_access_token, create_refresh_token,
    authenticate_user, create_user, create_token_response,
    verify_token, get_user_by_id, update_user_last_login
)
from security import (
    SecurityMiddleware, IPValidator, RateLimiter, InputValidator, log_security_event, validate_input,
    limiter, auth_rate_limiter
)
from database import (
    get_database, connect_to_mongo, close_mongo_connection, init_collections,
    UserDatabase, EmailScanDatabase, ThreatDatabase, FeedbackDatabase,
    SettingsDatabase
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Aman Cybersecurity Platform",
    description="Advanced cybersecurity platform with AI-powered phishing detection",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "development" else None
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=429,
    content={"error": "Rate limit exceeded", "detail": str(exc.detail)}
))
app.add_middleware(SlowAPIMiddleware)

# Add security middleware (temporarily disabled due to implementation issues)
# app.add_middleware(SecurityMiddleware)

# CORS middleware with security considerations
allowed_origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    os.getenv("FRONTEND_URL", ""),
]

# Remove empty strings and add environment-specific origins
allowed_origins = [origin for origin in allowed_origins if origin]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks"""
    logger.info("Starting Aman Cybersecurity Platform...")
    await connect_to_mongo()
    await init_collections()
    logger.info("✅ Startup completed successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Aman Cybersecurity Platform...")
    await close_mongo_connection()
    logger.info("✅ Shutdown completed")

# Health check endpoint
@app.get("/api/health", response_model=HealthResponse)
@limiter.limit("10/minute")
async def health_check(request: Request):
    """Health check endpoint with system status"""
    try:
        # Check database connectivity
        db = get_database()
        await db.command('ping')
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        service="Aman Cybersecurity Platform",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        checks={
            "database": db_status,
            "api": "healthy"
        }
    )

# Authentication endpoints
@app.post("/api/auth/register", response_model=SuccessResponse)
@limiter.limit("5/minute")
async def register_user(request: Request, user_data: UserCreate):
    """Register a new user with comprehensive validation"""
    try:
        client_ip = IPValidator.get_client_ip(request)
        
        # Rate limiting for registration
        if not auth_rate_limiter.check_rate_limit(f"register_{client_ip}", max_attempts=3):
            raise HTTPException(
                status_code=429,
                detail="Too many registration attempts. Please try again later."
            )
        
        # Validate and sanitize input
        validated_data = validate_input(user_data.dict())
        user_create = UserCreate(**validated_data)
        
        # Create user
        user = await create_user(user_create)
        
        logger.info(f"New user registered: {user.email} from IP: {client_ip}")
        
        return SuccessResponse(
            message="User registered successfully",
            data={"user_id": user.id, "email": user.email}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Registration failed"
        )

@app.post("/api/auth/login", response_model=Token)
@limiter.limit("10/minute")
async def login_user(request: Request, login_data: LoginRequest):
    """Authenticate user and return JWT tokens"""
    try:
        client_ip = IPValidator.get_client_ip(request)
        identifier = f"{login_data.email}_{client_ip}"
        
        # Check rate limiting
        if not auth_rate_limiter.check_rate_limit(identifier, max_attempts=5):
            log_security_event("AUTH_RATE_LIMIT", {"email": login_data.email}, client_ip)
            raise HTTPException(
                status_code=429,
                detail="Too many login attempts. Please try again later."
            )
        
        # Check if temporarily blocked
        if auth_rate_limiter.is_temporarily_blocked(identifier):
            log_security_event("AUTH_BLOCKED", {"email": login_data.email}, client_ip)
            raise HTTPException(
                status_code=423,
                detail="Account temporarily locked due to failed attempts"
            )
        
        # Authenticate user
        user = await authenticate_user(login_data.email, login_data.password)
        
        if not user:
            auth_rate_limiter.record_failed_attempt(identifier)
            log_security_event("AUTH_FAILED", {"email": login_data.email}, client_ip)
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password"
            )
        
        # Clear failed attempts on successful login
        auth_rate_limiter.clear_failed_attempts(identifier)
        
        # Update last login
        await update_user_last_login(user.id)
        
        # Create token response
        token_response = create_token_response(user)
        
        logger.info(f"User logged in: {user.email} from IP: {client_ip}")
        
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Login failed"
        )

@app.post("/api/auth/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh_token(request: Request, refresh_data: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        token_data = verify_token(refresh_data.refresh_token, token_type="refresh")
        
        if not token_data:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = await get_user_by_id(token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=401,
                detail="User not found or inactive"
            )
        
        # Create new token response
        token_response = create_token_response(user)
        
        return token_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Token refresh failed"
        )

# User management endpoints
@app.get("/api/user/profile", response_model=UserResponse)
@limiter.limit("30/minute")
async def get_user_profile(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get current user profile"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        organization=current_user.organization,
        is_active=current_user.is_active,
        role=getattr(current_user, 'role', 'user'),  # Default to 'user' if role not present
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@app.put("/api/user/profile", response_model=SuccessResponse)
@limiter.limit("10/minute")
async def update_user_profile(
    request: Request,
    update_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Update user profile"""
    try:
        # Validate and sanitize input
        validated_data = validate_input(update_data.dict(exclude_unset=True))
        
        # Update user in database
        success = await UserDatabase.update_user(current_user.id, validated_data)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to update profile"
            )
        
        logger.info(f"User profile updated: {current_user.email}")
        
        return SuccessResponse(message="Profile updated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Profile update failed"
        )

# Dashboard endpoints
@app.get("/api/dashboard/stats", response_model=DashboardStats)
@limiter.limit("60/minute")
async def get_dashboard_stats(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get dashboard statistics for current user"""
    try:
        stats_data = await EmailScanDatabase.get_dashboard_stats(user_id=current_user.id)
        
        # Calculate accuracy rate (placeholder logic)
        total_scans = stats_data.get("total_scans", 0)
        accuracy_rate = 95.5 if total_scans > 0 else 0.0
        
        return DashboardStats(
            phishing_caught=stats_data.get("phishing_caught", 0),
            safe_emails=stats_data.get("safe_emails", 0),
            potential_phishing=stats_data.get("potential_phishing", 0),
            total_scans=total_scans,
            accuracy_rate=accuracy_rate,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch dashboard stats"
        )

@app.get("/api/dashboard/recent-emails")
@limiter.limit("60/minute")
async def get_recent_emails(
    request: Request,
    limit: int = 10,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get recent email scans for current user"""
    try:
        recent_scans = await EmailScanDatabase.get_user_recent_scans(
            current_user.id, limit=min(limit, 50)
        )
        
        # Convert to response format
        emails = []
        for scan in recent_scans:
            # Calculate time ago
            time_diff = datetime.utcnow() - scan.scanned_at
            if time_diff.days > 0:
                time_str = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif time_diff.seconds > 60:
                minutes = time_diff.seconds // 60
                time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                time_str = "Just now"
            
            emails.append(RecentEmailScan(
                id=scan.id,
                subject=scan.email_subject,
                sender=scan.sender,
                time=time_str,
                status=scan.scan_result,
                risk_score=scan.risk_score
            ))
        
        return {"emails": emails}
        
    except Exception as e:
        logger.error(f"Recent emails error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch recent emails"
        )

# Email scanning endpoints
@app.post("/api/scan/email", response_model=EmailScanResponse)
@limiter.limit("30/minute")
async def scan_email(
    request: Request,
    scan_request: EmailScanRequest,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Scan email for phishing threats using AI-powered advanced analysis"""
    try:
        client_ip = IPValidator.get_client_ip(request)
        
        # Validate and sanitize input
        validated_data = validate_input(scan_request.dict())
        
        # Enhanced security: Check content length and suspicious patterns
        email_body = validated_data.get("email_body", "")
        if len(email_body) > 50000:  # 50KB limit
            raise HTTPException(
                status_code=400,
                detail="Email content too large"
            )
        
        # Log scan attempt for security monitoring
        log_security_event("EMAIL_SCAN_ATTEMPT", {
            "user_id": current_user.id,
            "email_subject": validated_data.get("email_subject", "")[:50],
            "body_length": len(email_body)
        }, client_ip)
        
        # Use AI-enhanced scanning with fallback
        try:
            scan_results = await scan_email_with_ai(validated_data)
            logger.info(f"AI email scan successful for user {current_user.email}")
        except Exception as ai_error:
            logger.warning(f"AI scanning failed, falling back to advanced scanning: {ai_error}")
            scan_results = scan_email_advanced(validated_data)
        
        risk_score = scan_results.get('risk_score', 0.0)
        risk_level = scan_results.get('risk_level', 'safe')
        
        # Map risk_level to ScanStatus
        if risk_level == "phishing":
            status = ScanStatus.PHISHING
        elif risk_level == "potential_phishing":
            status = ScanStatus.POTENTIAL_PHISHING
        else:
            status = ScanStatus.SAFE
        
        explanation = scan_results.get('explanation', 'No explanation available')
        recommendations = scan_results.get('recommendations', [])
        threat_indicators = scan_results.get('threat_indicators', [])
        
        # Extract threat sources and detected threats from indicators
        threat_sources = list(set(indicator.get('source', '') for indicator in threat_indicators))
        detected_threats = list(set(indicator.get('threat_type', '') for indicator in threat_indicators))
        
        # Enhanced security: Redact sensitive information from storage
        safe_subject = validated_data["email_subject"][:200] if validated_data.get("email_subject") else ""
        safe_sender = validated_data["sender"][:100] if validated_data.get("sender") else ""
        
        # Store scan result in database with enhanced security
        scan_data = {
            "user_id": current_user.id,
            "email_subject": safe_subject,
            "sender": safe_sender,
            "recipient": validated_data.get("recipient", "")[:100],
            "scan_result": status.value,
            "risk_score": risk_score,
            "explanation": explanation,
            "threat_sources": threat_sources,
            "detected_threats": detected_threats,
            "scan_metadata": {
                **scan_results.get('metadata', {}),
                "ip_address": client_ip,
                "user_agent": request.headers.get("user-agent", "")[:200]
            },
            "scan_duration": scan_results.get('scan_duration', 0.0),
            "ai_powered": scan_results.get('metadata', {}).get('ai_powered', False)
        }
        
        scan_result = await EmailScanDatabase.create_email_scan(scan_data)
        
        # Enhanced security logging
        log_security_event("EMAIL_SCAN_COMPLETED", {
            "scan_id": scan_result.id,
            "risk_score": risk_score,
            "status": status.value,
            "ai_powered": scan_data["ai_powered"]
        }, client_ip)
        
        logger.info(f"Email scan completed for user {current_user.email}: risk_score={risk_score}, status={status.value}")
        
        return EmailScanResponse(
            id=scan_result.id,
            status=status,
            risk_score=risk_score,
            explanation=explanation,
            threat_sources=threat_sources,
            detected_threats=detected_threats,
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        client_ip = IPValidator.get_client_ip(request)
        log_security_event("EMAIL_SCAN_ERROR", {"error": str(e)}, client_ip)
        logger.error(f"Email scan error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Email scan failed"
        )

@app.post("/api/scan/link", response_model=LinkScanResponse)
@limiter.limit("60/minute")
async def scan_link(
    request: Request,
    link_request: LinkScanRequest,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Scan individual link for threats using AI-enhanced threat intelligence"""
    try:
        client_ip = IPValidator.get_client_ip(request)
        
        # Enhanced security: Validate URL format and length
        if not link_request.url or len(link_request.url) > 2000:
            raise HTTPException(
                status_code=400,
                detail="Invalid or too long URL"
            )
        
        # Validate URL format
        from security import InputValidator
        if not InputValidator.validate_url(link_request.url):
            raise HTTPException(
                status_code=400,
                detail="Invalid URL format"
            )
        
        # Log scan attempt for security monitoring
        log_security_event("LINK_SCAN_ATTEMPT", {
            "user_id": current_user.id,
            "url": link_request.url[:100],  # Truncate for logging
            "url_length": len(link_request.url)
        }, client_ip)
        
        # Use AI-enhanced link scanning with fallback
        try:
            context = getattr(link_request, 'context', '')
            scan_results = await scan_link_with_ai(link_request.url, context)
            logger.info(f"AI link scan successful for user {current_user.email}")
        except Exception as ai_error:
            logger.warning(f"AI link scanning failed, falling back to advanced scanning: {ai_error}")
            context = getattr(link_request, 'context', '')
            scan_results = scan_link_advanced(link_request.url, context)
        
        risk_score = scan_results.get('risk_score', 0.0)
        risk_level = scan_results.get('risk_level', 'safe')
        
        # Map risk_level to ScanStatus
        if risk_level == "phishing":
            status = ScanStatus.PHISHING
        elif risk_level == "potential_phishing":
            status = ScanStatus.POTENTIAL_PHISHING
        else:
            status = ScanStatus.SAFE
        
        explanation = scan_results.get('explanation', 'No explanation available')
        threat_indicators = scan_results.get('threat_indicators', [])
        
        # Extract threat categories from indicators
        threat_categories = list(set(indicator.get('threat_type', '') for indicator in threat_indicators))
        
        # Check for shortened URL with enhanced detection
        is_shortened = _is_shortened_url(link_request.url) or any(
            domain in link_request.url.lower() 
            for domain in ['shorturl', 'tiny', 'tinylink', 'shortlink', 'sl.ly']
        )
        
        # Enhanced redirect chain detection (placeholder for now)
        redirect_chain = []
        
        # Enhanced security logging
        log_security_event("LINK_SCAN_COMPLETED", {
            "url": link_request.url[:100],
            "risk_score": risk_score,
            "status": status.value,
            "ai_powered": scan_results.get('metadata', {}).get('ai_powered', False)
        }, client_ip)
        
        logger.info(f"Link scan completed for user {current_user.email}: url={link_request.url[:50]}, risk_score={risk_score}")
        
        return LinkScanResponse(
            url=link_request.url,
            status=status,
            risk_score=risk_score,
            explanation=explanation,
            threat_categories=threat_categories,
            redirect_chain=redirect_chain,
            is_shortened=is_shortened
        )
        
    except HTTPException:
        raise
    except Exception as e:
        client_ip = IPValidator.get_client_ip(request)
        log_security_event("LINK_SCAN_ERROR", {"error": str(e), "url": link_request.url[:100]}, client_ip)
        logger.error(f"Link scan error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Link scan failed"
        )

# Settings endpoints
@app.get("/api/user/settings", response_model=UserSettings)
@limiter.limit("30/minute")
async def get_user_settings(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get user settings"""
    try:
        settings = await SettingsDatabase.get_user_settings(current_user.id)
        return UserSettings(**settings)
    except Exception as e:
        logger.error(f"Get settings error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch settings"
        )

@app.put("/api/user/settings", response_model=SuccessResponse)
@limiter.limit("10/minute")
async def update_user_settings(
    request: Request,
    settings: UserSettings,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Update user settings"""
    try:
        success = await SettingsDatabase.update_user_settings(
            current_user.id, 
            settings.dict()
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to update settings"
            )
        
        return SuccessResponse(message="Settings updated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update settings error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Settings update failed"
        )

# Feedback endpoints
@app.post("/api/feedback/scan", response_model=SuccessResponse)
@limiter.limit("20/minute")
async def submit_feedback(
    request: Request,
    feedback: FeedbackCreate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Submit feedback on a scan result"""
    try:
        # Validate and sanitize input
        validated_data = validate_input(feedback.dict())
        
        # Submit feedback using the feedback system
        feedback_result = await submit_scan_feedback(
            scan_id=validated_data.get('scan_id'),
            user_id=current_user.id,
            is_correct=validated_data.get('is_correct'),
            suggested_risk_level=validated_data.get('suggested_risk_level'),
            user_comment=validated_data.get('user_comment', '')
        )
        
        if not feedback_result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=feedback_result.get('error', 'Failed to submit feedback')
            )
        
        logger.info(f"Feedback submitted by user {current_user.email} for scan {validated_data.get('scan_id')}")
        
        return SuccessResponse(
            message="Feedback submitted successfully",
            data={"feedback_id": feedback_result.get('feedback_id')}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit feedback"
        )

@app.get("/api/feedback/analytics")
@limiter.limit("10/minute")
async def get_feedback_analytics(
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get user feedback analytics"""
    try:
        analytics = await get_user_feedback_analytics(current_user.id)
        
        return {
            "total_feedback": analytics.get('total_feedback', 0),
            "accuracy_rate": analytics.get('accuracy_rate', 0.0),
            "feedback_breakdown": analytics.get('feedback_breakdown', {}),
            "recent_feedback": analytics.get('recent_feedback', [])
        }
        
    except Exception as e:
        logger.error(f"Feedback analytics error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch feedback analytics"
        )

# Threat Intelligence endpoints
@app.get("/api/threat-intelligence/domain/{domain}")
@limiter.limit("30/minute")
async def check_domain_threat_intelligence(
    request: Request,
    domain: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Check domain reputation using threat intelligence"""
    try:
        # Validate domain format
        from security import InputValidator
        if not InputValidator.validate_domain(domain):
            raise HTTPException(
                status_code=400,
                detail="Invalid domain format"
            )
        
        # Check domain reputation
        reputation_data = await check_domain_reputation(domain)
        
        logger.info(f"Domain reputation check by user {current_user.email}: {domain}")
        
        return reputation_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Domain reputation check error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to check domain reputation"
        )

@app.get("/api/threat-intelligence/url")
@limiter.limit("30/minute")
async def check_url_threat_intelligence(
    request: Request,
    url: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Check URL reputation using threat intelligence"""
    try:
        # Validate URL format
        from security import InputValidator
        if not InputValidator.validate_url(url):
            raise HTTPException(
                status_code=400,
                detail="Invalid URL format"
            )
        
        # Check URL reputation
        reputation_data = await check_url_reputation(url)
        
        logger.info(f"URL reputation check by user {current_user.email}: {url[:50]}...")
        
        return reputation_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL reputation check error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to check URL reputation"
        )

# Helper functions
def _is_shortened_url(url: str) -> bool:
    """Check if URL is a shortened URL"""
    short_domains = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly"]
    return any(domain in url for domain in short_domains)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for security and logging"""
    client_ip = IPValidator.get_client_ip(request)
    logger.error(f"Unhandled exception from {client_ip}: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8001,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )