"""
Simple token-based authentication system for Aman Cybersecurity Platform  
Replaces JWT with secure token generation using secrets and hashlib
"""

import secrets
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import uuid
import string
import logging
from database import get_database

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

# Pydantic models for authentication
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    organization: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(BaseModel):
    id: str
    email: str
    name: str
    organization: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    organization: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def validate_password_strength(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return all([has_upper, has_lower, has_digit, has_special])

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Generate secure token
    token = secrets.token_urlsafe(32)
    
    # Create token data
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
    
    # Create token data
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

def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
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
        
        return TokenData(user_id=token_data["sub"], email=token_data["email"])
        
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None

def decode_refresh_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify refresh token"""
    token_data = verify_token(refresh_token, "refresh")
    if token_data:
        return {"sub": token_data.user_id, "email": token_data.email}
    return None

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

# Database operations for users
async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Get user from database by email"""
    db = get_database()
    user_doc = await db.users.find_one({"email": email})
    
    if user_doc:
        return UserInDB(**user_doc)
    return None

async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """Get user from database by ID"""
    db = get_database()
    user_doc = await db.users.find_one({"id": user_id})
    
    if user_doc:
        return UserInDB(**user_doc)
    return None

async def create_user(user_create: UserCreate) -> UserInDB:
    """Create new user in database"""
    db = get_database()
    
    # Check if user already exists
    existing_user = await get_user_by_email(user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Validate password strength
    if not validate_password_strength(user_create.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters with uppercase, lowercase, digit, and special character"
        )
    
    # Create user document
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_create.password)
    
    user_doc = {
        "id": user_id,
        "email": user_create.email,
        "name": user_create.name,
        "organization": user_create.organization,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None,
        "failed_login_attempts": 0,
        "locked_until": None
    }
    
    await db.users.insert_one(user_doc)
    return UserInDB(**user_doc)

async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with email and password"""
    db = get_database()
    user = await get_user_by_email(email)
    
    if not user:
        return None
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked until {user.locked_until}"
        )
    
    # Verify password
    if not verify_password(password, user.hashed_password):
        # Increment failed login attempts
        await db.users.update_one(
            {"id": user.id},
            {
                "$inc": {"failed_login_attempts": 1},
                "$set": {
                    "locked_until": datetime.utcnow() + timedelta(minutes=15) 
                    if user.failed_login_attempts >= 4 else None
                }
            }
        )
        return None
    
    # Reset failed login attempts and update last login
    await db.users.update_one(
        {"id": user.id},
        {
            "$set": {
                "failed_login_attempts": 0,
                "locked_until": None,
                "last_login": datetime.utcnow()
            }
        }
    )
    
    return user

async def update_user_last_login(user_id: str):
    """Update user's last login timestamp"""
    db = get_database()
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"last_login": datetime.utcnow()}}
    )

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None:
        raise credentials_exception
    
    user = await get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

# Utility functions
def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

async def revoke_user_tokens(user_id: str):
    """Revoke all tokens for a user (implement token blacklist if needed)"""
    # This would typically involve adding tokens to a blacklist
    # For now, we'll just update the user's token version
    db = get_database()
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"token_version": 1}}
    )

def create_token_response(user: UserInDB) -> Token:
    """Create token response for authenticated user"""
    token_data = {"sub": user.id, "email": user.email}
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

# Run cleanup on module import
cleanup_expired_tokens()