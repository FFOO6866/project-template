"""
Authentication Dependencies for FastAPI

Provides dependency functions for protecting endpoints with JWT authentication
and role-based access control (RBAC).
"""

from typing import Optional, List
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from job_pricing.core.database import get_session
from job_pricing.models.auth import User, Permission, AuditLog
from job_pricing.utils.auth import decode_token

# HTTP Bearer security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session)
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials (JWT token)
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = decode_token(credentials.credentials)

        # Verify token type
        if payload.get("type") != "access":
            raise credentials_exception

        # Get user ID from token (JWT 'sub' claim must be string)
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        # Convert to integer for database query
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise credentials_exception

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.commit()

        return user

    except JWTError:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.

    Args:
        current_user: Current user from token

    Returns:
        Current user if active

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_session)
) -> Optional[User]:
    """
    Get the current user from JWT token, but don't require authentication.

    Returns None if no token is provided or if token is invalid.
    Useful for endpoints that work with or without authentication.

    Args:
        credentials: Optional HTTP Bearer credentials
        db: Database session

    Returns:
        Current user if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        # Decode JWT token
        payload = decode_token(credentials.credentials)

        # Verify token type
        if payload.get("type") != "access":
            return None

        # Get user ID from token
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None

        # Convert to integer
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            return None

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or not user.is_active:
            return None

        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.commit()

        return user

    except (JWTError, Exception):
        # Silently fail - return None for any errors
        return None


async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current verified user.

    Args:
        current_user: Current user from token

    Returns:
        Current user if verified

    Raises:
        HTTPException: If user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email to access this resource."
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current superuser.

    Args:
        current_user: Current user from token

    Returns:
        Current user if superuser

    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Superuser access required."
        )
    return current_user


class PermissionChecker:
    """
    Dependency class for checking user permissions.

    Usage:
        @app.get("/salary", dependencies=[Depends(PermissionChecker([Permission.VIEW_SALARY_RECOMMENDATIONS]))])
        async def get_salary_recommendations():
            ...
    """

    def __init__(self, required_permissions: List[Permission], require_all: bool = True):
        """
        Initialize permission checker.

        Args:
            required_permissions: List of required permissions
            require_all: If True, user must have ALL permissions. If False, user needs ANY permission.
        """
        self.required_permissions = required_permissions
        self.require_all = require_all

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        Check if user has required permissions.

        Args:
            current_user: Current authenticated user

        Returns:
            Current user if authorized

        Raises:
            HTTPException: If user doesn't have required permissions
        """
        if self.require_all:
            has_permission = current_user.has_all_permissions(self.required_permissions)
        else:
            has_permission = current_user.has_any_permission(self.required_permissions)

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: {[p.value for p in self.required_permissions]}"
            )

        return current_user


class RoleChecker:
    """
    Dependency class for checking user roles.

    Usage:
        @app.post("/users", dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
        async def create_user():
            ...
    """

    def __init__(self, allowed_roles: List[str]):
        """
        Initialize role checker.

        Args:
            allowed_roles: List of allowed roles
        """
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        Check if user has one of the allowed roles.

        Args:
            current_user: Current authenticated user

        Returns:
            Current user if authorized

        Raises:
            HTTPException: If user doesn't have required role
        """
        if current_user.role not in self.allowed_roles and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required role: one of {self.allowed_roles}"
            )

        return current_user


async def log_user_action(
    action: str,
    user: User,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    method: str = "GET",
    endpoint: str = "/",
    status_code: int = 200,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    db: Session = Depends(get_session)
):
    """
    Log user action to audit log.

    Args:
        action: Action performed
        user: User who performed the action
        resource_type: Type of resource accessed
        resource_id: ID of resource accessed
        details: Additional details (JSON string)
        method: HTTP method
        endpoint: API endpoint
        status_code: HTTP status code
        ip_address: Client IP address
        user_agent: Client user agent
        db: Database session
    """
    audit_log = AuditLog(
        user_id=user.id if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        method=method,
        endpoint=endpoint,
        status_code=status_code,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )

    db.add(audit_log)
    db.commit()
