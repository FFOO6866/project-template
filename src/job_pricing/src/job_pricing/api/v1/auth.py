"""
Authentication Endpoints - Login, Register, Token Refresh, User Management
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from job_pricing.core.config import get_settings
from job_pricing.core.database import get_session
from job_pricing.models.auth import User, RefreshToken, UserRole, Permission
from job_pricing.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from job_pricing.api.dependencies import (
    get_current_user,
    get_current_superuser,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


# --------------------------------------------------------------------------
# Request/Response Models
# --------------------------------------------------------------------------

class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=100)
    department: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(BaseModel):
    """User response model"""
    id: int
    email: str
    username: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime]
    department: Optional[str]
    job_title: Optional[str]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UpdateUserRequest(BaseModel):
    """Update user request"""
    full_name: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None


class UpdateUserRoleRequest(BaseModel):
    """Update user role request (admin only)"""
    role: UserRole


# --------------------------------------------------------------------------
# Authentication Endpoints
# --------------------------------------------------------------------------

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_session)
):
    """
    Register a new user.

    Creates a new user account with default role (VIEWER).
    Email verification may be required before full access.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()

    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    # Create new user
    hashed_password = hash_password(user_data.password)

    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=UserRole.VIEWER.value,  # Default role
        department=user_data.department,
        job_title=user_data.job_title,
        phone=user_data.phone,
        is_active=True,
        is_verified=False,  # Requires email verification
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"New user registered: {new_user.email}")

    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_session)
):
    """
    Login with email/username and password.

    Returns access token and refresh token.
    """
    # Find user by email or username
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )

    refresh_token_str = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )

    # Store refresh token in database
    refresh_token_expires = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=refresh_token_expires,
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None
    )

    db.add(refresh_token)

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    logger.info(f"User logged in: {user.email}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_request: RefreshTokenRequest,
    db: Session = Depends(get_session)
):
    """
    Refresh access token using refresh token.

    Returns a new access token and refresh token.
    """
    try:
        # Decode refresh token
        payload = decode_token(token_request.refresh_token)

        # Verify token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # Get user ID from token (JWT 'sub' claim must be string)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in token"
            )

        jti = payload.get("jti")

        # Check if refresh token exists and is not revoked
        refresh_token = db.query(RefreshToken).filter(
            RefreshToken.token == token_request.refresh_token,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False
        ).first()

        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token"
            )

        # Check if token is expired
        if refresh_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )

        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new tokens
        new_access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )

        new_refresh_token_str = create_refresh_token(
            data={"sub": user.id, "email": user.email}
        )

        # Revoke old refresh token
        refresh_token.revoked = True
        refresh_token.revoked_at = datetime.utcnow()

        # Store new refresh token
        refresh_token_expires = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        new_refresh_token = RefreshToken(
            user_id=user.id,
            token=new_refresh_token_str,
            expires_at=refresh_token_expires
        )

        db.add(new_refresh_token)
        db.commit()

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token_str,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token"
        )


@router.post("/logout")
async def logout(
    refresh_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Logout user by revoking refresh token.
    """
    # Revoke refresh token
    token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token,
        RefreshToken.user_id == current_user.id
    ).first()

    if token:
        token.revoked = True
        token.revoked_at = datetime.utcnow()
        db.commit()

    logger.info(f"User logged out: {current_user.email}")

    return {"message": "Successfully logged out"}


# --------------------------------------------------------------------------
# User Management Endpoints
# --------------------------------------------------------------------------

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    """
    return current_user


@router.get("/me/permissions")
async def get_current_user_permissions(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's permissions.
    """
    return {
        "role": current_user.role,
        "is_superuser": current_user.is_superuser,
        "permissions": [perm.value for perm in current_user.permissions]
    }


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Update current user's profile information.
    """
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name
    if update_data.department is not None:
        current_user.department = update_data.department
    if update_data.job_title is not None:
        current_user.job_title = update_data.job_title
    if update_data.phone is not None:
        current_user.phone = update_data.phone

    current_user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(current_user)

    logger.info(f"User updated profile: {current_user.email}")

    return current_user


@router.post("/me/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Change current user's password.
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    current_user.hashed_password = hash_password(password_data.new_password)
    current_user.updated_at = datetime.utcnow()

    db.commit()

    logger.info(f"User changed password: {current_user.email}")

    return {"message": "Password changed successfully"}


# --------------------------------------------------------------------------
# Admin Endpoints
# --------------------------------------------------------------------------

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_session)
):
    """
    List all users (admin only).
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_session)
):
    """
    Get user by ID (admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_data: UpdateUserRoleRequest,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_session)
):
    """
    Update user role (admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.role = role_data.role.value
    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    logger.info(f"Admin {current_user.email} changed role of {user.email} to {role_data.role.value}")

    return user


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_session)
):
    """
    Deactivate user account (admin only).

    Does not delete the user, just marks them as inactive.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    user.is_active = False
    user.updated_at = datetime.utcnow()

    db.commit()

    logger.info(f"Admin {current_user.email} deactivated user {user.email}")

    return {"message": "User deactivated successfully"}
