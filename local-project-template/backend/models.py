"""
Pydantic Models for Aman Cybersecurity Platform
Defines all data models, request/response schemas, and validation rules
"""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid

# Enums for consistent values
class ScanStatus(str, Enum):
    SAFE = "safe"
    PHISHING = "phishing"
    POTENTIAL_PHISHING = "potential_phishing"
    SCANNING = "scanning"
    ERROR = "error"

class ThreatSource(str, Enum):
    BODY = "body"
    LINK = "link"
    IMAGE = "image"
    FILE = "file"
    SENDER = "sender"
    SUBJECT = "subject"
    AI_ANALYSIS = "ai_analysis"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class OrganizationStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"

class UnblockStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# Base models
class TimestampMixin(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

# User models
class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    organization: Optional[str] = Field(None, max_length=100)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not all([has_upper, has_lower, has_digit, has_special]):
            raise ValueError('Password must contain uppercase, lowercase, digit, and special character')
        
        return v

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    organization: Optional[str] = Field(None, max_length=100)
    
class UserResponse(UserBase, TimestampMixin):
    id: str
    is_active: bool = True
    role: UserRole = UserRole.USER
    last_login: Optional[datetime] = None

class UserInDB(UserResponse):
    hashed_password: str
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    token_version: int = 0

# Authentication models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Organization models
class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    domain: Optional[str] = Field(None, max_length=100)
    contact_email: EmailStr
    
class OrganizationCreate(OrganizationBase):
    admin_user_id: str

class OrganizationResponse(OrganizationBase, TimestampMixin):
    id: str
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    user_count: int = 0
    scan_count: int = 0

# Email scanning models
class EmailScanBase(BaseModel):
    email_subject: str = Field(..., max_length=200)
    sender: str = Field(..., max_length=100)
    recipient: str = Field(..., max_length=100)
    email_body: str = Field(..., max_length=10000)
    
class EmailScanRequest(EmailScanBase):
    scan_links: bool = True
    scan_attachments: bool = True

class LinkInfo(BaseModel):
    url: str
    text: str
    risk_score: float = Field(..., ge=0, le=100)
    status: ScanStatus
    explanation: Optional[str] = None

class AttachmentInfo(BaseModel):
    filename: str
    file_type: str
    file_size: int
    risk_score: float = Field(..., ge=0, le=100)
    status: ScanStatus
    explanation: Optional[str] = None

class EmailScanResult(BaseModel):
    id: str
    user_id: str
    email_subject: str
    sender: str
    recipient: str
    scan_result: ScanStatus
    risk_score: float = Field(..., ge=0, le=100)
    explanation: str
    threat_sources: List[ThreatSource] = []
    detected_threats: List[str] = []
    links_analyzed: List[LinkInfo] = []
    attachments_analyzed: List[AttachmentInfo] = []
    scanned_at: datetime = Field(default_factory=datetime.utcnow)
    scan_duration: Optional[float] = None  # in seconds

class EmailScanResponse(BaseModel):
    id: str
    status: ScanStatus
    risk_score: float
    explanation: str
    threat_sources: List[ThreatSource]
    detected_threats: List[str]
    recommendations: List[str] = []
    links_count: int = 0
    safe_links: int = 0
    suspicious_links: int = 0
    attachments_count: int = 0
    safe_attachments: int = 0
    suspicious_attachments: int = 0

# Dashboard models
class DashboardStats(BaseModel):
    phishing_caught: int = 0
    safe_emails: int = 0
    potential_phishing: int = 0
    total_scans: int = 0
    accuracy_rate: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class RecentEmailScan(BaseModel):
    id: str
    subject: str
    sender: str
    time: str  # Human readable time
    status: ScanStatus
    risk_score: float

class DashboardData(BaseModel):
    stats: DashboardStats
    recent_emails: List[RecentEmailScan]
    daily_scans: List[Dict[str, Any]] = []  # For charts
    threat_trends: List[Dict[str, Any]] = []

# Threat intelligence models
class ThreatDomain(BaseModel):
    domain: str
    risk_score: float = Field(..., ge=0, le=100)
    threat_type: str
    first_seen: datetime
    last_seen: datetime
    source: str
    description: Optional[str] = None

class ThreatLog(BaseModel):
    id: str
    domain: str
    ip_address: Optional[str] = None
    threat_type: str
    severity: str  # low, medium, high, critical
    description: str
    source: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

# Feedback models
class FeedbackBase(BaseModel):
    scan_id: str
    is_correct: bool
    user_comment: Optional[str] = Field(None, max_length=1000)

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackResponse(FeedbackBase, TimestampMixin):
    id: str
    user_id: str

# Unblock request models
class UnblockRequestBase(BaseModel):
    domain: str = Field(..., max_length=100)
    reason: str = Field(..., max_length=500)

class UnblockRequestCreate(UnblockRequestBase):
    pass

class UnblockRequestResponse(UnblockRequestBase, TimestampMixin):
    id: str
    user_id: str
    status: UnblockStatus = UnblockStatus.PENDING
    admin_response: Optional[str] = None
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None

# Settings models
class UserSettings(BaseModel):
    email_notifications: bool = True
    real_time_scanning: bool = True
    block_suspicious_links: bool = False
    scan_attachments: bool = True
    share_threat_intelligence: bool = True
    
class OrganizationSettings(BaseModel):
    enforce_scanning: bool = True
    block_high_risk_emails: bool = False
    require_user_feedback: bool = False
    admin_approval_required: bool = False

# API Response models
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

# Link scanning models
class LinkScanRequest(BaseModel):
    url: str = Field(..., max_length=2000)
    context: Optional[str] = Field(None, max_length=500)  # Context where link was found

class LinkScanResponse(BaseModel):
    url: str
    status: ScanStatus
    risk_score: float
    explanation: str
    threat_categories: List[str] = []
    redirect_chain: List[str] = []
    is_shortened: bool = False
    final_domain: Optional[str] = None

# Bulk operations models
class BulkEmailScanRequest(BaseModel):
    emails: List[EmailScanRequest] = Field(..., max_items=100)

class BulkEmailScanResponse(BaseModel):
    results: List[EmailScanResponse]
    total_processed: int
    successful: int
    failed: int
    processing_time: float

# Analytics models
class AnalyticsQuery(BaseModel):
    start_date: datetime
    end_date: datetime
    group_by: str = "day"  # day, week, month
    filters: Optional[Dict[str, Any]] = None

class AnalyticsResponse(BaseModel):
    data: List[Dict[str, Any]]
    summary: Dict[str, Any]
    period: str

# Health check model
class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "Aman Cybersecurity Platform"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Dict[str, str] = {}

# Configuration models
class APIConfiguration(BaseModel):
    max_requests_per_minute: int = 60
    max_file_size_mb: int = 10
    allowed_file_types: List[str] = [".txt", ".pdf", ".doc", ".docx"]
    ai_providers: List[str] = ["openai", "gemini", "claude"]
    default_scan_timeout: int = 30