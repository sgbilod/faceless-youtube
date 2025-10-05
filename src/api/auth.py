"""
JWT Authentication for FastAPI

Provides secure API authentication using JWT tokens.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


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
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password from user
        hashed_password: Bcrypt hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Bcrypt hashed password
    """
    return pwd_context.hash(password)


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
        "hashed_password": get_password_hash("admin"),  # Change in production!
        "full_name": "Administrator",
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
