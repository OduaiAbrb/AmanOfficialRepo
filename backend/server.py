"""
Aman Cybersecurity Platform - Secure Backend API
Comprehensive FastAPI backend with JWT authentication, security middleware, and real database operations
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request, BackgroundTasks
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

# Import new advanced modules
from email_scanner import scan_email_advanced, scan_link_advanced
from feedback_system import submit_scan_feedback, get_user_feedback_analytics
from threat_intelligence import check_domain_reputation, check_url_reputation
from models import (
    UserCreate, UserResponse, LoginRequest, Token, RefreshTokenRequest,
    EmailScanRequest, EmailScanResponse, DashboardStats, DashboardData,
    RecentEmailScan, FeedbackCreate, FeedbackResponse, UnblockRequestCreate,
    UnblockRequestResponse, SuccessResponse, ErrorResponse, HealthResponse,
    LinkScanRequest, LinkScanResponse, UserUpdate, UserSettings, ScanStatus
)
from auth import (
    authenticate_user, create_user, get_current_active_user, create_token_response,
    verify_token, get_user_by_id, update_user_last_login
)
from security import (
    limiter, SecurityMiddleware, validate_input, log_security_event,
    auth_rate_limiter, IPValidator
)
from database import (
    connect_to_mongo, close_mongo_connection, init_collections,
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
        from database import get_database
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
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
        
        # Check if temporarily blocked
        if auth_rate_limiter.is_temporarily_blocked(identifier):
            log_security_event("AUTH_BLOCKED", {"email": login_data.email}, client_ip)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account temporarily locked due to failed attempts"
            )
        
        # Authenticate user
        user = await authenticate_user(login_data.email, login_data.password)
        
        if not user:
            auth_rate_limiter.record_failed_attempt(identifier)
            log_security_event("AUTH_FAILED", {"email": login_data.email}, client_ip)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = await get_user_by_id(token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update profile"
            )
        
        logger.info(f"User profile updated: {current_user.email}")
        
        return SuccessResponse(message="Profile updated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    """Scan email for phishing threats using advanced AI-powered analysis"""
    try:
        # Validate and sanitize input
        validated_data = validate_input(scan_request.dict())
        
        # Use advanced email scanning logic
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
        
        # Store scan result in database
        scan_data = {
            "user_id": current_user.id,
            "email_subject": validated_data["email_subject"],
            "sender": validated_data["sender"],
            "recipient": validated_data["recipient"],
            "scan_result": status.value,
            "risk_score": risk_score,
            "explanation": explanation,
            "threat_sources": threat_sources,
            "detected_threats": detected_threats,
            "scan_metadata": scan_results.get('metadata', {}),
            "scan_duration": scan_results.get('scan_duration', 0.0)
        }
        
        scan_result = await EmailScanDatabase.create_email_scan(scan_data)
        
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
        logger.error(f"Email scan error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email scan failed"
        )

@app.post("/api/scan/link", response_model=LinkScanResponse)
@limiter.limit("60/minute")
async def scan_link(
    request: Request,
    link_request: LinkScanRequest,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Scan individual link for threats"""
    try:
        # Validate URL
        from security import InputValidator
        if not InputValidator.validate_url(link_request.url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL format"
            )
        
        # Placeholder link analysis (will be enhanced with real threat intelligence)
        risk_score = await _analyze_link(link_request.url)
        
        if risk_score >= 80:
            status = ScanStatus.PHISHING
            explanation = "High risk malicious link detected"
        elif risk_score >= 40:
            status = ScanStatus.POTENTIAL_PHISHING
            explanation = "Potentially suspicious link"
        else:
            status = ScanStatus.SAFE
            explanation = "Link appears safe"
        
        return LinkScanResponse(
            url=link_request.url,
            status=status,
            risk_score=risk_score,
            explanation=explanation,
            threat_categories=[],
            redirect_chain=[],
            is_shortened=_is_shortened_url(link_request.url)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Link scan error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update settings"
            )
        
        return SuccessResponse(message="Settings updated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update settings error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Settings update failed"
        )

# Helper functions (placeholders for AI integration)
async def _analyze_email_content(email_data: dict) -> float:
    """Analyze email content for threats - placeholder for AI integration"""
    content = email_data.get("email_body", "").lower()
    subject = email_data.get("email_subject", "").lower()
    sender = email_data.get("sender", "").lower()
    
    risk_score = 0.0
    
    # Placeholder risk assessment logic
    suspicious_keywords = [
        "urgent", "verify account", "click here", "limited time", "suspended",
        "congratulations", "winner", "claim now", "act fast", "expires today"
    ]
    
    suspicious_domains = [
        "bit.ly", "tinyurl.com", "suspicious-domain.net", "fake-bank.com",
        "win-now.fake", "prizes.fake"
    ]
    
    # Check for suspicious keywords
    for keyword in suspicious_keywords:
        if keyword in content or keyword in subject:
            risk_score += 15
    
    # Check sender domain
    for domain in suspicious_domains:
        if domain in sender:
            risk_score += 30
    
    # Additional checks
    if "@" not in sender or "." not in sender:
        risk_score += 20
    
    if len(content) < 50:  # Very short emails can be suspicious
        risk_score += 10
    
    return min(risk_score, 100.0)

async def _analyze_link(url: str) -> float:
    """Analyze link for threats - placeholder for threat intelligence integration"""
    risk_score = 0.0
    
    suspicious_domains = [
        "bit.ly", "tinyurl.com", "suspicious-site.com", "malware-site.net"
    ]
    
    for domain in suspicious_domains:
        if domain in url:
            risk_score += 50
    
    if _is_shortened_url(url):
        risk_score += 20
    
    return min(risk_score, 100.0)

def _is_shortened_url(url: str) -> bool:
    """Check if URL is a shortened URL"""
    short_domains = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly"]
    return any(domain in url for domain in short_domains)

def _generate_recommendations(status: ScanStatus, risk_score: float) -> List[str]:
    """Generate security recommendations based on scan results"""
    recommendations = []
    
    if status == ScanStatus.PHISHING:
        recommendations.extend([
            "Do not click any links in this email",
            "Do not download any attachments",
            "Report this email as phishing to your IT department",
            "Delete this email immediately"
        ])
    elif status == ScanStatus.POTENTIAL_PHISHING:
        recommendations.extend([
            "Exercise caution with this email",
            "Verify sender identity through alternative means",
            "Avoid clicking suspicious links",
            "Consider reporting if you suspect phishing"
        ])
    else:
        recommendations.extend([
            "Email appears safe to read",
            "Still exercise normal email security practices"
        ])
    
    return recommendations

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