import secrets
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from database import get_database, UserDatabase
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

# Token storage (in production, use Redis or database)
active_tokens = {}
refresh_tokens = {}

# Token settings
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Generate secure token
    token = secrets.token_urlsafe(32)
    
    # Create token hash for validation
    token_data = {
        "sub": data.get("sub"),
        "email": data.get("email"),
        "exp": expire.timestamp(),
        "iat": datetime.utcnow().timestamp(),
        "type": "access"
    }
    
    # Store token data
    active_tokens[token] = token_data
    
    logger.info(f"Created access token for user: {data.get('email')}")
    return token


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a new refresh token"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Generate secure refresh token
    token = secrets.token_urlsafe(32)
    
    # Create token hash for validation
    token_data = {
        "sub": data.get("sub"),
        "email": data.get("email"),
        "exp": expire.timestamp(),
        "iat": datetime.utcnow().timestamp(),
        "type": "refresh"
    }
    
    # Store refresh token data
    refresh_tokens[token] = token_data
    
    logger.info(f"Created refresh token for user: {data.get('email')}")
    return token


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify and decode a token"""
    try:
        # Choose the right token storage
        token_storage = active_tokens if token_type == "access" else refresh_tokens
        
        # Check if token exists
        if token not in token_storage:
            return None
        
        token_data = token_storage[token]
        
        # Check token type
        if token_data.get("type") != token_type:
            return None
        
        # Check if token is expired
        if token_data["exp"] < datetime.utcnow().timestamp():
            # Remove expired token
            del token_storage[token]
            return None
        
        return token_data
        
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


def decode_refresh_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify refresh token"""
    return verify_token(refresh_token, "refresh")


def revoke_token(token: str, token_type: str = "access"):
    """Revoke a token"""
    token_storage = active_tokens if token_type == "access" else refresh_tokens
    if token in token_storage:
        del token_storage[token]
        logger.info(f"Revoked {token_type} token")


def revoke_all_user_tokens(user_id: str):
    """Revoke all tokens for a specific user"""
    # Remove all access tokens for user
    access_tokens_to_remove = [
        token for token, data in active_tokens.items() 
        if data.get("sub") == user_id
    ]
    for token in access_tokens_to_remove:
        del active_tokens[token]
    
    # Remove all refresh tokens for user
    refresh_tokens_to_remove = [
        token for token, data in refresh_tokens.items() 
        if data.get("sub") == user_id
    ]
    for token in refresh_tokens_to_remove:
        del refresh_tokens[token]
    
    logger.info(f"Revoked all tokens for user: {user_id}")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from token"""
    token = credentials.credentials
    
    # Verify token
    token_data = verify_token(token, "access")
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    try:
        user = await UserDatabase.get_user_by_id(token_data["sub"])
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def authenticate_user(email: str, password: str):
    """Authenticate user with email and password"""
    try:
        # Get user from database
        user = await UserDatabase.get_user_by_email(email)
        if not user:
            return False
        
        # Verify password
        if not verify_password(password, user["password_hash"]):
            return False
        
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return False


def cleanup_expired_tokens():
    """Clean up expired tokens (should be run periodically)"""
    current_time = datetime.utcnow().timestamp()
    
    # Clean access tokens
    expired_access = [
        token for token, data in active_tokens.items()
        if data["exp"] < current_time
    ]
    for token in expired_access:
        del active_tokens[token]
    
    # Clean refresh tokens
    expired_refresh = [
        token for token, data in refresh_tokens.items()
        if data["exp"] < current_time
    ]
    for token in expired_refresh:
        del refresh_tokens[token]
    
    if expired_access or expired_refresh:
        logger.info(f"Cleaned up {len(expired_access)} access tokens and {len(expired_refresh)} refresh tokens")


# Run cleanup on module import
cleanup_expired_tokens()