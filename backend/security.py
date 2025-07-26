"""
Security Middleware and Utilities for Aman Cybersecurity Platform
Implements rate limiting, input validation, CORS, and other security measures
"""

import time
import hashlib
import re
from typing import Dict, Optional, List, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import validators
from datetime import datetime, timedelta
import ipaddress
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting configuration
limiter = Limiter(key_func=get_remote_address)

# Security configuration
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_EXTENSIONS = {'.txt', '.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg'}
BLOCKED_IPS = set()  # Will be populated from database or config
TRUSTED_IPS = {'127.0.0.1', '::1'}  # Localhost IPs

class SecurityHeaders:
    """Security headers middleware"""
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        return response

class InputValidator:
    """Input validation and sanitization utilities"""
    
    # Regex patterns for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?1?[- ]?\(?([0-9]{3})\)?[- ]?([0-9]{3})[- ]?([0-9]{4})$')
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    
    # Dangerous patterns to block
    SQL_INJECTION_PATTERNS = [
        r"(\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\s+)",
        r"(\s*(-{2}|#|\/\*|\*\/)\s*)",
        r"(\s*(OR|AND)\s+[0-9]+\s*=\s*[0-9]+)",
        r"(\s*['\"]?\s*(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)"
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*="
    ]
    
    @classmethod
    def sanitize_string(cls, text: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(text, str):
            return ""
        
        # Limit length
        text = text[:max_length]
        
        # Remove null bytes and control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Escape HTML/XML special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#x27;')
        
        return text.strip()
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email format"""
        if not email or len(email) > 254:
            return False
        return bool(cls.EMAIL_PATTERN.match(email))
    
    @classmethod
    def validate_uuid(cls, uuid_str: str) -> bool:
        """Validate UUID format"""
        if not uuid_str:
            return False
        return bool(cls.UUID_PATTERN.match(uuid_str))
    
    @classmethod
    def detect_sql_injection(cls, text: str) -> bool:
        """Detect potential SQL injection attempts"""
        text_lower = text.lower()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def detect_xss(cls, text: str) -> bool:
        """Detect potential XSS attempts"""
        text_lower = text.lower()
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Validate URL format"""
        try:
            return validators.url(url)
        except:
            return False
    
    @classmethod
    def validate_domain(cls, domain: str) -> bool:
        """Validate domain format"""
        try:
            return validators.domain(domain)
        except:
            return False
    
    @classmethod
    def validate_file_extension(cls, filename: str) -> bool:
        """Validate file extension"""
        if not filename:
            return False
        
        ext = os.path.splitext(filename)[1].lower()
        return ext in ALLOWED_FILE_EXTENSIONS

class IPValidator:
    """IP address validation and filtering"""
    
    @staticmethod
    def is_private_ip(ip_str: str) -> bool:
        """Check if IP is private/local"""
        try:
            ip = ipaddress.ip_address(ip_str)
            return ip.is_private or ip.is_loopback or ip.is_link_local
        except ValueError:
            return False
    
    @staticmethod
    def is_blocked_ip(ip_str: str) -> bool:
        """Check if IP is in blocked list"""
        return ip_str in BLOCKED_IPS
    
    @staticmethod
    def is_trusted_ip(ip_str: str) -> bool:
        """Check if IP is in trusted list"""
        return ip_str in TRUSTED_IPS
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Extract client IP from request"""
        # Check X-Forwarded-For header first (for proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in case of multiple proxies
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

class SecurityMiddleware:
    """Security middleware for request processing"""
    
    def __init__(self):
        self.request_counts: Dict[str, List[float]] = {}
        self.blocked_ips: set = BLOCKED_IPS.copy()
    
    async def __call__(self, request: Request, call_next):
        """Process security checks on incoming requests"""
        
        # Get client IP
        client_ip = IPValidator.get_client_ip(request)
        
        # Log request for monitoring
        logger.info(f"Request from {client_ip}: {request.method} {request.url.path}")
        
        # Check if IP is blocked
        if IPValidator.is_blocked_ip(client_ip):
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_CONTENT_LENGTH:
            logger.warning(f"Request too large from {client_ip}: {content_length} bytes")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request too large"
            )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response = SecurityHeaders.add_security_headers(response)
        
        return response

class AuthRateLimiter:
    """Rate limiter specifically for authentication endpoints"""
    
    def __init__(self):
        self.login_attempts: Dict[str, List[float]] = {}
        self.failed_attempts: Dict[str, int] = {}
    
    def check_rate_limit(self, identifier: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """Check if identifier has exceeded rate limit"""
        now = time.time()
        window_start = now - (window_minutes * 60)
        
        # Clean old attempts
        if identifier in self.login_attempts:
            self.login_attempts[identifier] = [
                attempt for attempt in self.login_attempts[identifier] 
                if attempt > window_start
            ]
        else:
            self.login_attempts[identifier] = []
        
        # Check if limit exceeded
        if len(self.login_attempts[identifier]) >= max_attempts:
            return False
        
        # Add current attempt
        self.login_attempts[identifier].append(now)
        return True
    
    def record_failed_attempt(self, identifier: str):
        """Record a failed authentication attempt"""
        self.failed_attempts[identifier] = self.failed_attempts.get(identifier, 0) + 1
    
    def clear_failed_attempts(self, identifier: str):
        """Clear failed attempts for identifier"""
        self.failed_attempts.pop(identifier, None)
    
    def is_temporarily_blocked(self, identifier: str, max_failures: int = 5) -> bool:
        """Check if identifier is temporarily blocked due to failures"""
        return self.failed_attempts.get(identifier, 0) >= max_failures

# Global instances
auth_rate_limiter = AuthRateLimiter()

# Decorator for validating input
def validate_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize input data"""
    validated_data = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # Check for malicious patterns
            if InputValidator.detect_sql_injection(value):
                logger.warning(f"SQL injection attempt detected in field: {key}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input detected"
                )
            
            if InputValidator.detect_xss(value):
                logger.warning(f"XSS attempt detected in field: {key}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input detected"  
                )
            
            # Sanitize the value
            validated_data[key] = InputValidator.sanitize_string(value)
        else:
            validated_data[key] = value
    
    return validated_data

# Request logging utility
def log_security_event(event_type: str, details: Dict[str, Any], client_ip: str):
    """Log security events for monitoring"""
    logger.warning(f"SECURITY EVENT - {event_type}: {details} from IP: {client_ip}")
    
    # In production, you might want to send this to a SIEM or monitoring system
    # Example: send_to_siem(event_type, details, client_ip)