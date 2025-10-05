"""
JWT Authentication for FastAPI

Provides secure API authentication using JWT tokens.
"""

import os
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# HTTPBearer with auto_error=False to manually handle 401 vs 403
security = HTTPBearer(auto_error=False)


class Token(BaseModel):
    """JWT Token response model"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded JWT token data"""
    username: Optional[str] = None
    exp: Optional[datetime] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password using bcrypt directly.
    
    Args:
        plain_password: Plain text password from user
        hashed_password: Bcrypt hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Convert strings to bytes and verify with bcrypt
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt directly.
    
    Args:
        password: Plain text password
        
    Returns:
        Bcrypt hashed password string
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing claims (must include 'sub' for username)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_access_token({"sub": "admin"})
        >>> # Returns JWT token valid for 30 minutes
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Verify JWT token from Authorization header.
    
    Args:
        credentials: HTTP Bearer token from request header
        
    Returns:
        TokenData with decoded claims
        
    Raises:
        HTTPException: If token is invalid, expired, or missing
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # If credentials are None, token was not provided
    if credentials is None:
        raise credentials_exception
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        exp: datetime = datetime.fromtimestamp(payload.get("exp", 0))
        token_data = TokenData(username=username, exp=exp)
        
        return token_data
        
    except JWTError:
        raise credentials_exception


async def get_current_user(
    token_data: TokenData = Depends(verify_token)
) -> str:
    """
    Get current authenticated user from token.
    
    Use as a dependency in protected endpoints:
    
    Example:
        @app.get("/protected")
        async def protected_route(user: str = Depends(get_current_user)):
            return {"user": user}
    
    Args:
        token_data: Decoded token data from verify_token
        
    Returns:
        Username of authenticated user
    """
    return token_data.username


# Demo user database (REPLACE WITH REAL DATABASE IN PRODUCTION)
DEMO_USERS = {
    "admin": {
        "username": "admin",
        # Hash for password "admin"
        "hashed_password": (
            "$2b$12$HbEF3ZQEMkyVb2I1YkhZdefownavHrPJUsh0z6e/zjDFNZTsPjvQa"
        ),
        "full_name": "Administrator",
        "disabled": False,
    },
    "test@example.com": {
        "username": "test@example.com",
        # Hash for password "password"
        "hashed_password": (
            "$2b$12$wIErhDkakaSRLtJtS2dd3OvhASOyrUQOkwGrtnqI5Wh/aMtp6BhT6"
        ),
        "full_name": "Test User",
        "disabled": False,
    }
}


async def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate user credentials.
    
    TODO: Replace with real database lookup in production
    
    Args:
        username: User's username
        password: Plain text password
        
    Returns:
        True if authentication succeeds, False otherwise
    """
    user = DEMO_USERS.get(username)
    if not user:
        return False
    
    if not verify_password(password, user["hashed_password"]):
        return False
    
    return True
