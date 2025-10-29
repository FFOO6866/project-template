#!/usr/bin/env python3
"""
User Management System
Production-ready user CRUD operations with proper security
"""

import logging
import secrets
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import asdict

from ..core.auth import (
    User, UserRole, Permission, auth_system,
    AuthenticationError, AuthorizationError
)

logger = logging.getLogger(__name__)

class UserManager:
    """
    Production user management with security controls
    """
    
    def __init__(self):
        self.auth = auth_system
        logger.info("User management system initialized")
    
    def create_user(
        self, 
        username: str, 
        email: str, 
        password: str, 
        role: UserRole,
        created_by: User
    ) -> User:
        """
        Create new user with security checks
        """
        # Only admins can create users
        if created_by.role != UserRole.ADMIN:
            raise AuthorizationError("Only administrators can create users")
        
        # Validate input
        if len(username) < 3 or len(username) > 50:
            raise ValueError("Username must be 3-50 characters")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        if not self._is_valid_email(email):
            raise ValueError("Invalid email format")
        
        # Check if user already exists
        if username in self.auth.users:
            raise ValueError(f"User '{username}' already exists")
        
        # Create user
        try:
            user = self.auth.create_user(username, email, password, role)
            logger.info(f"User created: {username} by {created_by.username}")
            return user
        except Exception as e:
            logger.error(f"Failed to create user {username}: {e}")
            raise
    
    def update_user(
        self, 
        username: str, 
        updates: Dict[str, Any],
        updated_by: User
    ) -> User:
        """
        Update user with security checks
        """
        user = self.auth.users.get(username)
        if not user:
            raise ValueError(f"User '{username}' not found")
        
        # Authorization checks
        if updated_by.role != UserRole.ADMIN and updated_by.username != username:
            raise AuthorizationError("Can only update own profile or admin required")
        
        # Apply updates
        if "email" in updates:
            if not self._is_valid_email(updates["email"]):
                raise ValueError("Invalid email format")
            user.email = updates["email"]
        
        if "role" in updates and updated_by.role == UserRole.ADMIN:
            user.role = UserRole(updates["role"])
            user.permissions = self.auth.role_permissions[user.role]
        
        if "is_active" in updates and updated_by.role == UserRole.ADMIN:
            user.is_active = bool(updates["is_active"])
        
        logger.info(f"User updated: {username} by {updated_by.username}")
        return user
    
    def change_password(
        self, 
        username: str, 
        old_password: str, 
        new_password: str,
        changed_by: User
    ) -> bool:
        """
        Change user password with verification
        """
        user = self.auth.users.get(username)
        if not user:
            raise ValueError(f"User '{username}' not found")
        
        # Authorization checks
        if changed_by.role != UserRole.ADMIN and changed_by.username != username:
            raise AuthorizationError("Can only change own password or admin required")
        
        # Verify old password (unless admin override)
        if changed_by.role != UserRole.ADMIN:
            if not self.auth.verify_password(old_password, user.password_hash):
                raise AuthenticationError("Current password is incorrect")
        
        # Validate new password
        if len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters")
        
        # Update password
        user.password_hash = self.auth.hash_password(new_password)
        logger.info(f"Password changed for user: {username} by {changed_by.username}")
        
        return True
    
    def deactivate_user(self, username: str, deactivated_by: User) -> bool:
        """
        Deactivate user account
        """
        if deactivated_by.role != UserRole.ADMIN:
            raise AuthorizationError("Only administrators can deactivate users")
        
        user = self.auth.users.get(username)
        if not user:
            raise ValueError(f"User '{username}' not found")
        
        if username == "admin":
            raise AuthorizationError("Cannot deactivate admin user")
        
        user.is_active = False
        logger.info(f"User deactivated: {username} by {deactivated_by.username}")
        
        return True
    
    def list_users(
        self, 
        requested_by: User, 
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List users with filtering
        """
        # Only admins and managers can list users
        if requested_by.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise AuthorizationError("Insufficient permissions to list users")
        
        users = []
        for username, user in self.auth.users.items():
            if not include_inactive and not user.is_active:
                continue
                
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            users.append(user_data)
        
        return users
    
    def get_user(self, username: str, requested_by: User) -> Optional[Dict[str, Any]]:
        """
        Get user details
        """
        # Can view own profile or admin/manager can view any
        if (requested_by.username != username and 
            requested_by.role not in [UserRole.ADMIN, UserRole.MANAGER]):
            raise AuthorizationError("Insufficient permissions to view user details")
        
        user = self.auth.users.get(username)
        if not user:
            return None
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "api_key": user.api_key if requested_by.username == username or requested_by.role == UserRole.ADMIN else "[HIDDEN]"
        }
    
    def regenerate_api_key(self, username: str, requested_by: User) -> str:
        """
        Regenerate API key for user
        """
        # Can regenerate own API key or admin can do any
        if (requested_by.username != username and 
            requested_by.role != UserRole.ADMIN):
            raise AuthorizationError("Can only regenerate own API key or admin required")
        
        user = self.auth.users.get(username)
        if not user:
            raise ValueError(f"User '{username}' not found")
        
        # Remove old API key mapping
        if user.api_key and user.api_key in self.auth.api_keys:
            del self.auth.api_keys[user.api_key]
        
        # Generate new API key
        new_api_key = self.auth.generate_api_key()
        user.api_key = new_api_key
        self.auth.api_keys[new_api_key] = username
        
        logger.info(f"API key regenerated for user: {username} by {requested_by.username}")
        return new_api_key
    
    def get_user_sessions(self, username: str, requested_by: User) -> List[Dict[str, Any]]:
        """
        Get active sessions for user (placeholder - would integrate with session store)
        """
        # Can view own sessions or admin can view any
        if (requested_by.username != username and 
            requested_by.role != UserRole.ADMIN):
            raise AuthorizationError("Can only view own sessions or admin required")
        
        # This would integrate with a real session store (Redis, database, etc.)
        # For now, return placeholder data
        return [
            {
                "session_id": "session_123",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0..."
            }
        ]
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

# Global user manager instance
user_manager = UserManager()

# Export main components
__all__ = ['UserManager', 'user_manager']