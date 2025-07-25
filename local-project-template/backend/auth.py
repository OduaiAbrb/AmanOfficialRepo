"""
Authentication and Security Module for Aman Cybersecurity Platform
Implements JWT authentication, password hashing, and security utilities
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import secrets
import string
from pydantic import BaseModel, EmailStr
import uuid
from database import get_database

# Security configuration
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer for token authentication
security = HTTPBearer()

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

# Password utilities
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

# JWT token utilities
def create_access_token(data: Dict[Any, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[Any, Any]) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            return None
            
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id is None or email is None:
            return None
            
        return TokenData(user_id=user_id, email=email)
    except JWTError:
        return None

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