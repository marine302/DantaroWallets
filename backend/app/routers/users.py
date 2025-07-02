"""
User-related API routes.
Handles user registration, authentication, and profile management.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from ..core.db import get_db
from ..core.config import settings
from ..utils.security import create_access_token
from ..crud import crud_user
from ..deps import get_current_active_user
from .. import schemas, models

router = APIRouter()


@router.post("/signup", response_model=schemas.SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    Create new user account.
    
    - **email**: Valid email address (will be used for login)
    - **password**: Strong password (minimum 8 characters, must contain uppercase, digit)
    """
    # Check if user already exists
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system."
        )
    
    # Create new user
    try:
        user = crud_user.create(db, user_create=user_in)
        return schemas.SuccessResponse(
            message="User account created successfully",
            data={
                "user_id": int(user.id),  # type: ignore
                "email": str(user.email)  # type: ignore
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user account: {str(e)}"
        )


@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    - **username**: User email address
    - **password**: User password
    """
    user = crud_user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires  # type: ignore
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/login/email", response_model=schemas.Token)
def login_with_email(
    *,
    db: Session = Depends(get_db),
    user_credentials: schemas.UserLogin
) -> Any:
    """
    Alternative login endpoint using JSON payload.
    
    - **email**: User email address
    - **password**: User password
    """
    user = crud_user.authenticate(
        db, email=user_credentials.email, password=user_credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires  # type: ignore
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=schemas.UserProfile)
def read_user_me(
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user profile information.
    
    Returns the profile of the currently authenticated user.
    """
    return schemas.UserProfile(
        id=int(current_user.id),  # type: ignore
        email=str(current_user.email),  # type: ignore
        is_admin=bool(current_user.is_admin),  # type: ignore
        is_active=bool(current_user.is_active),  # type: ignore
        created_at=current_user.created_at  # type: ignore
    )


@router.get("/profile", response_model=schemas.UserProfile)
def get_user_profile(
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get detailed user profile (alias for /me endpoint).
    
    Returns comprehensive profile information for the authenticated user.
    """
    return schemas.UserProfile(
        id=int(current_user.id),  # type: ignore
        email=str(current_user.email),  # type: ignore
        is_admin=bool(current_user.is_admin),  # type: ignore
        is_active=bool(current_user.is_active),  # type: ignore
        created_at=current_user.created_at  # type: ignore
    )
