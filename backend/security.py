import logging
import re
import hashlib
from typing import Any, Dict
from datetime import datetime
from fastapi import Request

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Security middleware for request processing"""
    
    def __init__(self):
        self.blocked_ips = set()
        self.rate_limits = {}
    
    def process_request(self, request: Request) -> bool:
        """Process incoming request for security checks"""
        client_ip = request.client.host if request.client else "unknown"
        
        # Check blocked IPs
        if client_ip in self.blocked_ips:
            return False
        
        return True

class IPValidator:
    """IP validation utilities"""
    
    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """Validate IP address format"""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except Exception:
            return False
    
    @staticmethod
    def is_private_ip(ip: str) -> bool:
        """Check if IP is in private range"""
        try:
            parts = [int(x) for x in ip.split('.')]
            return (
                parts[0] == 10 or
                (parts[0] == 172 and 16 <= parts[1] <= 31) or
                (parts[0] == 192 and parts[1] == 168)
            )
        except Exception:
            return False

class RateLimiter:
    """Rate limiting utilities"""
    
    def __init__(self):
        self.requests = {}
    
    def is_rate_limited(self, key: str, limit: int, window: int) -> bool:
        """Check if request is rate limited"""
        now = datetime.utcnow().timestamp()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if now - req_time < window]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= limit:
            return True
        
        # Add current request
        self.requests[key].append(now)
        return False

class InputValidator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_domain(domain: str) -> bool:
        """Validate domain name format"""
        if not domain or len(domain) > 255:
            return False
        
        pattern = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*'
            r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )
        return pattern.match(domain) is not None
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return pattern.match(email) is not None
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not input_str:
            return ""
        
        # Remove potential HTML/script tags
        sanitized = re.sub(r'<[^>]*>', '', input_str)
        
        # Limit length
        return sanitized[:max_length]
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        pattern = re.compile(
            r'^https?://'                       # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'                      # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'                      # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        return pattern.match(url) is not None

def log_security_event(event_type: str, details: Dict[str, Any] = None, ip_address: str = None, user_id: str = None):
    """Log security events"""
    event_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "ip_address": ip_address,
        "user_id": user_id,
        "details": details or {}
    }
    logger.warning(f"Security Event: {event_data}")

def validate_input(input_data: Any, validation_type: str = "general") -> bool:
    """General input validation"""
    if input_data is None:
        return False
    
    if isinstance(input_data, str):
        # Check for common injection patterns
        dangerous_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
            r'<embed'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                log_security_event("suspicious_input", {"pattern": pattern, "input": input_data[:100]})
                return False
    
    return True

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging/storage"""
    return hashlib.sha256(data.encode()).hexdigest()[:16]

def generate_csrf_token() -> str:
    """Generate CSRF token"""
    import secrets
    return secrets.token_urlsafe(32)

def validate_csrf_token(token: str, session_token: str) -> bool:
    """Validate CSRF token"""
    return token == session_token

class SecurityHeaders:
    """Security headers management"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
