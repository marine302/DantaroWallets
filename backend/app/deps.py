"""
Dependency injection for FastAPI routes.
Handles authentication, database sessions, and user validation.
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .core.db import get_db
from .utils.security import verify_token, create_credentials_exception
from .crud import crud_user
from . import models

# Security scheme
security = HTTPBearer()


def get_token_from_cookie(request: Request) -> Optional[str]:
    """
    쿠키에서 JWT 토큰을 추출합니다.
    
    Args:
        request: FastAPI Request 객체
        
    Returns:
        Optional[str]: 토큰 문자열 또는 None
    """
    token = request.cookies.get("access_token")
    if token and token.startswith("Bearer "):
        return token[7:]  # "Bearer " 제거
    return None


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> models.User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        db: Database session
        credentials: HTTP Bearer token credentials
        
    Returns:
        models.User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Verify token and get user ID
    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise create_credentials_exception()
    
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise create_credentials_exception()
    
    # Get user from database
    user = crud_user.get(db, user_id=user_id_int)
    if user is None:
        raise create_credentials_exception()
    
    # Check if user is active
    if not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """
    쿠키에서 현재 인증된 사용자를 가져옵니다 (선택적).
    
    Args:
        request: FastAPI Request 객체
        db: 데이터베이스 세션
        
    Returns:
        Optional[models.User]: 현재 인증된 사용자 또는 None
    """
    token = get_token_from_cookie(request)
    if not token:
        return None
    
    # 토큰 검증 및 사용자 ID 추출
    user_id = verify_token(token)
    if user_id is None:
        return None
    
    try:
        user_id_int = int(user_id)
    except ValueError:
        return None
    
    # 데이터베이스에서 사용자 가져오기
    user = crud_user.get(db, user_id=user_id_int)
    if user is None or not crud_user.is_active(user):
        return None
    
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Get current active user (alias for get_current_user).
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        models.User: Current active user
    """
    return current_user


def get_current_admin_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Get current admin user.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        models.User: Current admin user
        
    Raises:
        HTTPException: If user is not admin
    """
    if not crud_user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_current_admin_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db)
) -> models.User:
    """
    쿠키에서 현재 인증된 관리자 사용자를 가져옵니다.
    
    Args:
        request: FastAPI Request 객체
        db: 데이터베이스 세션
        
    Returns:
        models.User: 현재 인증된 관리자 사용자
        
    Raises:
        HTTPException: 토큰이 유효하지 않거나 관리자가 아닌 경우
    """
    token = get_token_from_cookie(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 토큰 검증 및 사용자 ID 추출
    user_id = verify_token(token)
    if user_id is None:
        raise create_credentials_exception()
    
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise create_credentials_exception()
    
    # 데이터베이스에서 사용자 가져오기
    user = crud_user.get(db, user_id=user_id_int)
    if user is None:
        raise create_credentials_exception()
    
    # 사용자 활성화 상태 확인
    if not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성화된 사용자입니다"
        )
    
    # 관리자 권한 확인
    if not crud_user.is_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    
    return user


# Common pagination dependencies
def common_pagination_params(page: int = 1, page_size: int = 20) -> dict:
    """
    Common pagination parameters.
    
    Args:
        page: Page number (1-based)
        page_size: Number of items per page
        
    Returns:
        dict: Pagination parameters with skip and limit
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100
    
    skip = (page - 1) * page_size
    return {"skip": skip, "limit": page_size, "page": page, "page_size": page_size}
