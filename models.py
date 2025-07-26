from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class ScanStatus(str, Enum):
    SAFE = "safe"
    POTENTIAL_PHISHING = "potential_phishing"
    PHISHING = "phishing"

class SUBJECT(str, Enum):
    URGENT = "urgent"
    SECURITY = "security"
    ACCOUNT = "account"
    VERIFICATION = "verification"
    PAYMENT = "payment"
    WINNER = "winner"
    OTHER = "other"

# User Models
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    organization: Optional[str] = ""
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    organization: str
    role: UserRole
    is_active: bool

class UserUpdate(BaseModel):
    name: Optional[str] = None
    organization: Optional[str] = None

# Token Models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class TokenRefresh(BaseModel):
    refresh_token: str

# Scan Models
class EmailScanRequest(BaseModel):
    email_subject: str
    email_body: str
    sender: str
    recipient: Optional[str] = ""

class LinkScanRequest(BaseModel):
    url: str
    context: Optional[str] = ""

class ScanResult(BaseModel):
    id: str
    status: ScanStatus
    risk_score: float
    explanation: str
    threat_sources: List[str]
    detected_threats: List[str]
    recommendations: List[str]
    timestamp: datetime

class EmailScanResult(ScanResult):
    email_subject: str
    sender: str
    recipient: str

class LinkScanResult(ScanResult):
    url: str
    threat_categories: List[str]
    is_shortened: bool

# Settings Models
class UserSettings(BaseModel):
    email_notifications: bool = True
    real_time_scanning: bool = True
    threat_alerts: bool = True
    weekly_reports: bool = False
    scan_attachments: bool = True

# Dashboard Models
class DashboardStats(BaseModel):
    phishing_emails_caught: int
    safe_emails: int
    potential_phishing: int
    total_scans: int

class RecentEmailScan(BaseModel):
    id: str
    subject: str
    sender: str
    status: ScanStatus
    risk_score: float
    timestamp: str

# Feedback Models
class FeedbackSubmission(BaseModel):
    scan_id: str
    rating: int
    feedback_type: str
    comment: Optional[str] = ""
    
    @validator('rating')
    def validate_rating(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

# Admin Models
class AdminDashboardStats(BaseModel):
    total_users: int
    active_users: int
    total_organizations: int
    active_organizations: int
    today_scans: int
    today_threats: int
    total_threats_blocked: int
    avg_risk_score: float
    ai_usage_cost: float
    cache_hit_rate: float

class UserManagementData(BaseModel):
    users: List[Dict[str, Any]]
    total_count: int
    page: int
    per_page: int

class ThreatManagementData(BaseModel):
    threat_timeline: List[Dict[str, Any]]
    top_threat_sources: List[Dict[str, Any]]
    recent_threats: List[Dict[str, Any]]
    analysis_period: str

# AI Cost Models
class AICostUsage(BaseModel):
    total_requests: int
    total_cost: float
    total_tokens: int
    period_start: datetime
    period_end: datetime

class AICacheStats(BaseModel):
    hit_rate: float
    total_requests: int
    cache_hits: int
    cache_misses: int

# WebSocket Models
class WebSocketMessage(BaseModel):
    type: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class NotificationData(BaseModel):
    id: str
    type: str
    title: str
    message: str
    severity: str
    timestamp: datetime

# Response Models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    detail: str
    status_code: int

# Health Check Model
class HealthCheck(BaseModel):
    status: str
    timestamp: str
    database: str
    modules: Dict[str, bool]