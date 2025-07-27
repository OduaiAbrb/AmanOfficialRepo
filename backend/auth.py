import os
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "aman-cybersecurity-secret-key-2024-super-secure")
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    BCRYPT_AVAILABLE = True
    print("✅ Bcrypt available")
except ImportError:
    print("❌ Passlib not available - using simple hashing")
    BCRYPT_AVAILABLE = False
    pwd_context = None

# Bearer token security
security = HTTPBearer(auto_error=False)

# In-memory token storage (in production, use Redis or database)
active_tokens = {}
active_refresh_tokens = {}

class SimpleToken:
    """Simple token class without JWT"""
    
    def __init__(self, user_email: str, token_type: str = "access"):
        self.user_email = user_email
        self.token_type = token_type
        self.created_at = datetime.utcnow()
        self.token = self._generate_token()
        
        if token_type == "access":
            self.expires_at = self.created_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        else:  # refresh
            self.expires_at = self.created_at + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    def _generate_token(self) -> str:
        """Generate a secure random token"""
        # Create a unique token using secrets and user info
        random_part = secrets.token_urlsafe(32)
        user_part = hashlib.sha256(f"{self.user_email}{self.created_at}".encode()).hexdigest()[:16]
        return f"{random_part}{user_part}"
    
    def is_valid(self) -> bool:
        """Check if token is still valid"""
        return datetime.utcnow() < self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "user_email": self.user_email,
            "token_type": self.token_type,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "token": self.token
        }

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash"""
    if not BCRYPT_AVAILABLE or not pwd_context:
        # Simple comparison for development
        return plain_password == hashed_password
    
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt or simple hashing"""
    if not BCRYPT_AVAILABLE or not pwd_context:
        # Simple hash for development - NOT secure for production
        return hashlib.sha256(f"{SECRET_KEY}{password}".encode()).hexdigest()
    
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise HTTPException(status_code=500, detail="Password hashing failed")

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new access token"""
    user_email = data.get("sub")
    if not user_email:
        raise HTTPException(status_code=500, detail="Invalid token data")
    
    # Create simple token
    token_obj = SimpleToken(user_email, "access")
    
    # Store in memory (use database in production)
    active_tokens[token_obj.token] = token_obj
    
    # Clean expired tokens
    _cleanup_expired_tokens()
    
    logger.info(f"Access token created for: {user_email}")
    return token_obj.token

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new refresh token"""
    user_email = data.get("sub")
    if not user_email:
        raise HTTPException(status_code=500, detail="Invalid token data")
    
    # Create simple refresh token
    token_obj = SimpleToken(user_email, "refresh")
    
    # Store in memory (use database in production)
    active_refresh_tokens[token_obj.token] = token_obj
    
    # Clean expired tokens
    _cleanup_expired_tokens()
    
    logger.info(f"Refresh token created for: {user_email}")
    return token_obj.token

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify and decode a simple token"""
    try:
        # Clean expired tokens first
        _cleanup_expired_tokens()
        
        # Get token storage based on type
        token_storage = active_tokens if token_type == "access" else active_refresh_tokens
        
        # Check if token exists
        token_obj = token_storage.get(token)
        if not token_obj:
            logger.warning(f"Token not found: {token[:10]}...")
            return None
        
        # Check if token is valid
        if not token_obj.is_valid():
            logger.warning(f"Token expired for: {token_obj.user_email}")
            # Remove expired token
            del token_storage[token]
            return None
        
        # Return token data in JWT-like format for compatibility
        return {
            "sub": token_obj.user_email,
            "type": token_obj.token_type,
            "exp": token_obj.expires_at.timestamp(),
            "iat": token_obj.created_at.timestamp()
        }
        
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify an access token"""
    return verify_token(token, "access")

def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a refresh token"""
    return verify_token(token, "refresh")

def _cleanup_expired_tokens():
    """Remove expired tokens from storage"""
    try:
        current_time = datetime.utcnow()
        
        # Clean access tokens
        expired_access = [token for token, obj in active_tokens.items() 
                         if not obj.is_valid()]
        for token in expired_access:
            del active_tokens[token]
        
        # Clean refresh tokens
        expired_refresh = [token for token, obj in active_refresh_tokens.items() 
                          if not obj.is_valid()]
        for token in expired_refresh:
            del active_refresh_tokens[token]
        
        if expired_access or expired_refresh:
            logger.info(f"Cleaned {len(expired_access)} access and {len(expired_refresh)} refresh tokens")
            
    except Exception as e:
        logger.error(f"Token cleanup error: {e}")

def invalidate_token(token: str):
    """Invalidate a specific token (for logout)"""
    try:
        if token in active_tokens:
            del active_tokens[token]
            logger.info("Access token invalidated")
        if token in active_refresh_tokens:
            del active_refresh_tokens[token]
            logger.info("Refresh token invalidated")
    except Exception as e:
        logger.error(f"Token invalidation error: {e}")

def get_active_token_count() -> Dict[str, int]:
    """Get count of active tokens"""
    _cleanup_expired_tokens()
    return {
        "access_tokens": len(active_tokens),
        "refresh_tokens": len(active_refresh_tokens)
    }

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get the current authenticated user"""
    if not credentials:
        return None
        
    # Import here to avoid circular imports
    try:
        from database import UserDatabase
        from models import UserResponse
    except ImportError as e:
        logger.error(f"Database import error: {e}")
        return None
    
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

async def get_current_active_user(current_user = Depends(get_current_user)):
    """Get the current active authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if current_user is None:
        raise credentials_exception
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user

# Log setup status
logger.info("✅ Simple Token Auth Setup Complete - NO JWT REQUIRED")
print("🔑 Using Simple Token Authentication (No JWT)")