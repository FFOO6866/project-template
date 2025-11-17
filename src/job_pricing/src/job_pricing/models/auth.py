"""
Authentication Models - User, Role, Permission

Implements JWT-based authentication with role-based access control (RBAC).
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Table, Column, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from job_pricing.models.base import Base


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    HR_ANALYST = "hr_analyst"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Permission enumeration"""
    # Job Pricing
    CREATE_JOB_PRICING = "create_job_pricing"
    VIEW_JOB_PRICING = "view_job_pricing"
    UPDATE_JOB_PRICING = "update_job_pricing"
    DELETE_JOB_PRICING = "delete_job_pricing"

    # AI Generation
    USE_AI_GENERATION = "use_ai_generation"

    # Salary Recommendations
    VIEW_SALARY_RECOMMENDATIONS = "view_salary_recommendations"
    APPROVE_SALARY_RECOMMENDATIONS = "approve_salary_recommendations"

    # External Data
    VIEW_EXTERNAL_DATA = "view_external_data"
    REFRESH_EXTERNAL_DATA = "refresh_external_data"

    # HRIS
    VIEW_HRIS_DATA = "view_hris_data"
    MANAGE_HRIS_INTEGRATION = "manage_hris_integration"

    # Applicants
    VIEW_APPLICANTS = "view_applicants"
    MANAGE_APPLICANTS = "manage_applicants"

    # System
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_SETTINGS = "manage_settings"


# Role-Permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        # All permissions
        Permission.CREATE_JOB_PRICING,
        Permission.VIEW_JOB_PRICING,
        Permission.UPDATE_JOB_PRICING,
        Permission.DELETE_JOB_PRICING,
        Permission.USE_AI_GENERATION,
        Permission.VIEW_SALARY_RECOMMENDATIONS,
        Permission.APPROVE_SALARY_RECOMMENDATIONS,
        Permission.VIEW_EXTERNAL_DATA,
        Permission.REFRESH_EXTERNAL_DATA,
        Permission.VIEW_HRIS_DATA,
        Permission.MANAGE_HRIS_INTEGRATION,
        Permission.VIEW_APPLICANTS,
        Permission.MANAGE_APPLICANTS,
        Permission.VIEW_SYSTEM_LOGS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_ROLES,
        Permission.MANAGE_SETTINGS,
    ],
    UserRole.HR_MANAGER: [
        Permission.CREATE_JOB_PRICING,
        Permission.VIEW_JOB_PRICING,
        Permission.UPDATE_JOB_PRICING,
        Permission.USE_AI_GENERATION,
        Permission.VIEW_SALARY_RECOMMENDATIONS,
        Permission.APPROVE_SALARY_RECOMMENDATIONS,
        Permission.VIEW_EXTERNAL_DATA,
        Permission.VIEW_HRIS_DATA,
        Permission.VIEW_APPLICANTS,
        Permission.MANAGE_APPLICANTS,
    ],
    UserRole.HR_ANALYST: [
        Permission.CREATE_JOB_PRICING,
        Permission.VIEW_JOB_PRICING,
        Permission.UPDATE_JOB_PRICING,
        Permission.USE_AI_GENERATION,
        Permission.VIEW_SALARY_RECOMMENDATIONS,
        Permission.VIEW_EXTERNAL_DATA,
        Permission.VIEW_HRIS_DATA,
        Permission.VIEW_APPLICANTS,
    ],
    UserRole.VIEWER: [
        Permission.VIEW_JOB_PRICING,
        Permission.VIEW_SALARY_RECOMMENDATIONS,
        Permission.VIEW_EXTERNAL_DATA,
    ],
}


class User(Base):
    """
    User model for authentication and authorization.

    Supports JWT-based authentication with role-based access control.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Role and permissions
    role: Mapped[str] = mapped_column(String(50), nullable=False, default=UserRole.VIEWER.value)

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Additional info
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission"""
        if self.is_superuser:
            return True

        try:
            user_role = UserRole(self.role)
            return permission in ROLE_PERMISSIONS.get(user_role, [])
        except ValueError:
            return False

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(self.has_permission(perm) for perm in permissions)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions"""
        return all(self.has_permission(perm) for perm in permissions)

    @property
    def permissions(self) -> List[Permission]:
        """Get all permissions for this user's role"""
        if self.is_superuser:
            return list(Permission)

        try:
            user_role = UserRole(self.role)
            return ROLE_PERMISSIONS.get(user_role, [])
        except ValueError:
            return []

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class RefreshToken(Base):
    """
    Refresh token for JWT authentication.

    Stores refresh tokens to enable token revocation.
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(500), unique=True, index=True, nullable=False)

    # Token metadata
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Client information
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.revoked})>"


class AuditLog(Base):
    """
    Audit log for tracking user actions.

    Records all important user actions for compliance and security monitoring.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Action details
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Request metadata
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)

    # Client information
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Additional data (JSON)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}')>"
