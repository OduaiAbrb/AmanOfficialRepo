import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from database import UserDatabase
from models import UserResponse
import logging

logger = logging.getLogger(__name__)

# Security configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    try:
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Access token creation error: {e}")
        raise

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new refresh token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    try:
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Refresh token creation error: {e}")
        raise

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            logger.warning(f"Invalid token type. Expected: {token_type}, Got: {payload.get('type')}")
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            logger.warning("Token has expired")
            return None
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.JWTError as e:
        logger.warning(f"JWT verification error: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify an access token"""
    return verify_token(token, "access")

def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a refresh token"""
    return verify_token(token, "refresh")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[UserResponse]:
    """Get the current authenticated user"""
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        
        if payload is None:
            return None
        
        email: str = payload.get("sub")
        if email is None:
            return None
        
        # Get user from database
        user_data = await UserDatabase.get_user_by_email(email)
        if user_data is None:
            return None
        
        # Convert to UserResponse model
        user = UserResponse(
            id=user_data.get("id"),
            name=user_data.get("name"),
            email=user_data.get("email"),
            organization=user_data.get("organization", ""),
            role=user_data.get("role", "user"),
            is_active=user_data.get("is_active", True)
        )
        
        return user
        
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        return None

async def get_current_active_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Get the current active authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if current_user is None:
        logger.warning("No current user found")
        raise credentials_exception
    
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user

async def get_optional_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[UserResponse]:
    """Get current user if authenticated, otherwise return None (for optional auth)"""
    try:
        return await get_current_user(credentials)
    except:
        return None

def create_password_reset_token(email: str) -> str:
    """Create a password reset token"""
    data = {
        "sub": email,
        "type": "password_reset"
    }
    expire = datetime.utcnow() + timedelta(hours=1)  # Reset tokens expire in 1 hour
    data.update({"exp": expire, "iat": datetime.utcnow()})
    
    try:
        encoded_jwt = jwt.encode(data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Password reset token creation error: {e}")
        raise

def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token and return the email"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != "password_reset":
            return None
        
        email: str = payload.get("sub")
        return email
        
    except jwt.ExpiredSignatureError:
        logger.warning("Password reset token has expired")
        return None
    except jwt.JWTError as e:
        logger.warning(f"Password reset token verification error: {e}")
        return None
    except Exception as e:
        logger.error(f"Password reset token verification error: {e}")
        return None

def create_email_verification_token(email: str) -> str:
    """Create an email verification token"""
    data = {
        "sub": email,
        "type": "email_verification"
    }
    expire = datetime.utcnow() + timedelta(days=1)  # Verification tokens expire in 1 day
    data.update({"exp": expire, "iat": datetime.utcnow()})
    
    try:
        encoded_jwt = jwt.encode(data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Email verification token creation error: {e}")
        raise

def verify_email_verification_token(token: str) -> Optional[str]:
    """Verify an email verification token and return the email"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != "email_verification":
            return None
        
        email: str = payload.get("sub")
        return email
        
    except jwt.ExpiredSignatureError:
        logger.warning("Email verification token has expired")
        return None
    except jwt.JWTError as e:
        logger.warning(f"Email verification token verification error: {e}")
        return None
    except Exception as e:
        logger.error(f"Email verification token verification error: {e}")
        return None

def check_user_permissions(user: UserResponse, required_role: str = "user") -> bool:
    """Check if user has required permissions"""
    role_hierarchy = {
        "user": 1,
        "admin": 2,
        "super_admin": 3
    }
    
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

async def require_role(required_role: str = "user"):
    """Dependency to require specific role"""
    async def role_checker(current_user: UserResponse = Depends(get_current_active_user)) -> UserResponse:
        if not check_user_permissions(current_user, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user
    
    return role_checker

async def get_current_admin_user(current_user: UserResponse = Depends(get_current_active_user)) -> UserResponse:
    """Get current user and ensure they have admin privileges"""
    if not check_user_permissions(current_user, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

async def get_current_super_admin_user(current_user: UserResponse = Depends(get_current_active_user)) -> UserResponse:
    """Get current user and ensure they have super admin privileges"""
    if not check_user_permissions(current_user, "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    return current_user

# Rate limiting helpers
def create_rate_limit_key(identifier: str, action: str) -> str:
    """Create a rate limiting key"""
    return f"rate_limit:{action}:{identifier}"

def create_login_attempt_key(email: str) -> str:
    """Create a login attempt tracking key"""
    return f"login_attempts:{email}"

def create_password_reset_attempt_key(email: str) -> str:
    """Create a password reset attempt tracking key"""
    return f"password_reset_attempts:{email}"

# Token blacklist helpers (for logout functionality)
_token_blacklist = set()

def blacklist_token(token: str):
    """Add token to blacklist"""
    _token_blacklist.add(token)

def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted"""
    return token in _token_blacklist

def cleanup_expired_blacklisted_tokens():
    """Clean up expired tokens from blacklist (should be run periodically)"""
    global _token_blacklist
    valid_tokens = set()
    
    for token in _token_blacklist:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) > datetime.utcnow():
                valid_tokens.add(token)
        except:
            # Token is invalid or expired, don't add to valid_tokens
            pass
    
    _token_blacklist = valid_tokens

# Utility functions for token info
def get_token_info(token: str) -> Optional[Dict[str, Any]]:
    """Get information about a token without verifying expiration"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
        return {
            "email": payload.get("sub"),
            "type": payload.get("type"),
            "issued_at": datetime.fromtimestamp(payload.get("iat", 0)),
            "expires_at": datetime.fromtimestamp(payload.get("exp", 0)),
            "is_expired": datetime.fromtimestamp(payload.get("exp", 0)) < datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Token info extraction error: {e}")
        return None

def is_token_expired(token: str) -> bool:
    """Check if a token is expired"""
    info = get_token_info(token)
    return info is None or info.get("is_expired", True)

# Security event logging
def log_security_event(event_type: str, user_email: str = None, ip_address: str = None, details: str = None):
    """Log security-related events"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_email": user_email,
        "ip_address": ip_address,
        "details": details
    }
    
    logger.info(f"Security Event: {log_entry}")

# Input validation helpers
def validate_email_format(email: str) -> bool:
    """Basic email format validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength and return status with message"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    if not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"