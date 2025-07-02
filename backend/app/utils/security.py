"""
Security utilities for authentication and password handling.
Provides JWT token creation/verification and password hashing.
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from ..core.config import settings

# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: The subject (usually user ID) to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        str: Encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Optional[str]: User ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return str(user_id)
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password from database
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def create_credentials_exception() -> HTTPException:
    """
    Create a standardized credentials exception.
    
    Returns:
        HTTPException: 401 Unauthorized exception
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
