#!/usr/bin/env python3
"""
JWT Authentication Implementation
Secure JWT token generation, validation, and management
"""

import os
import jwt
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Union, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TokenType(Enum):
    """JWT token types"""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"
    VERIFICATION = "verification"

@dataclass
class TokenConfig:
    """JWT token configuration"""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    reset_token_expire_minutes: int = 15
    verification_token_expire_hours: int = 24
    issuer: str = "horme-api"
    audience: str = "horme-users"

class JWTManager:
    """
    Production JWT token management
    """
    
    def __init__(self, config: Optional[TokenConfig] = None):
        self.config = config or self._create_default_config()
        
        # Validate configuration
        if len(self.config.secret_key) < 32:
            raise ValueError("JWT secret key must be at least 32 characters")
        
        # Token blacklist (in production, use Redis or database)
        self._blacklisted_tokens = set()
        
        logger.info("JWT manager initialized with secure configuration")
    
    def _create_default_config(self) -> TokenConfig:
        """Create default configuration from environment"""
        secret_key = os.getenv("JWT_SECRET_KEY")
        
        if not secret_key:
            # Generate secure secret key
            secret_key = secrets.token_urlsafe(64)
            logger.warning("No JWT_SECRET_KEY found. Generated new key. Set JWT_SECRET_KEY environment variable.")
            logger.warning(f"Generated JWT_SECRET_KEY: {secret_key}")
        
        return TokenConfig(
            secret_key=secret_key,
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)),
            reset_token_expire_minutes=int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", 15)),
            verification_token_expire_hours=int(os.getenv("VERIFICATION_TOKEN_EXPIRE_HOURS", 24))
        )
    
    def create_access_token(
        self, 
        user_id: str,
        username: str,
        role: str,
        permissions: List[str],
        additional_claims: Dict = None
    ) -> str:
        """
        Create JWT access token
        
        Args:
            user_id: User ID
            username: Username
            role: User role
            permissions: User permissions
            additional_claims: Additional claims to include
            
        Returns:
            str: JWT access token
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.config.access_token_expire_minutes)
        
        payload = {
            # Standard claims
            "sub": username,  # Subject
            "iat": now,       # Issued at
            "exp": expire,    # Expiration
            "iss": self.config.issuer,    # Issuer
            "aud": self.config.audience,  # Audience
            "jti": secrets.token_urlsafe(16),  # JWT ID (for blacklisting)
            
            # Custom claims
            "type": TokenType.ACCESS.value,
            "user_id": user_id,
            "role": role,
            "permissions": permissions,
            "token_version": 1
        }
        
        # Add additional claims
        if additional_claims:
            payload.update(additional_claims)
        
        try:
            token = jwt.encode(
                payload, 
                self.config.secret_key, 
                algorithm=self.config.algorithm
            )
            
            logger.debug(f"Access token created for user: {username}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise
    
    def create_refresh_token(
        self, 
        user_id: str,
        username: str
    ) -> str:
        """
        Create JWT refresh token
        
        Args:
            user_id: User ID
            username: Username
            
        Returns:
            str: JWT refresh token
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.config.refresh_token_expire_days)
        
        payload = {
            "sub": username,
            "iat": now,
            "exp": expire,
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "jti": secrets.token_urlsafe(16),
            "type": TokenType.REFRESH.value,
            "user_id": user_id,
            "token_version": 1
        }
        
        try:
            token = jwt.encode(
                payload, 
                self.config.secret_key, 
                algorithm=self.config.algorithm
            )
            
            logger.debug(f"Refresh token created for user: {username}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise
    
    def create_reset_token(self, user_id: str, username: str, email: str) -> str:
        """
        Create password reset token
        
        Args:
            user_id: User ID
            username: Username
            email: User email
            
        Returns:
            str: Password reset token
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.config.reset_token_expire_minutes)
        
        payload = {
            "sub": username,
            "iat": now,
            "exp": expire,
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "jti": secrets.token_urlsafe(16),
            "type": TokenType.RESET.value,
            "user_id": user_id,
            "email": email,
            "token_version": 1
        }
        
        try:
            token = jwt.encode(
                payload, 
                self.config.secret_key, 
                algorithm=self.config.algorithm
            )
            
            logger.info(f"Password reset token created for user: {username}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to create reset token: {e}")
            raise
    
    def verify_token(
        self, 
        token: str, 
        expected_type: Optional[TokenType] = None
    ) -> Optional[Dict]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token to verify
            expected_type: Expected token type
            
        Returns:
            dict: Token payload if valid, None if invalid
        """
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                audience=self.config.audience,
                issuer=self.config.issuer
            )
            
            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and jti in self._blacklisted_tokens:
                logger.warning(f"Attempt to use blacklisted token: {jti}")
                return None
            
            # Check token type if specified
            if expected_type and payload.get("type") != expected_type.value:
                logger.warning(f"Token type mismatch. Expected: {expected_type.value}, Got: {payload.get('type')}")
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.debug("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def blacklist_token(self, token: str) -> bool:
        """
        Add token to blacklist
        
        Args:
            token: Token to blacklist
            
        Returns:
            bool: True if successful
        """
        try:
            payload = self.verify_token(token)
            if payload:
                jti = payload.get("jti")
                if jti:
                    self._blacklisted_tokens.add(jti)
                    logger.info(f"Token blacklisted: {jti}")
                    return True
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
        
        return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if token is blacklisted
        
        Args:
            token: Token to check
            
        Returns:
            bool: True if blacklisted
        """
        try:
            payload = self.verify_token(token)
            if payload:
                jti = payload.get("jti")
                return jti in self._blacklisted_tokens if jti else False
        except Exception:
            pass
        
        return True  # Treat invalid tokens as blacklisted
    
    def get_token_info(self, token: str) -> Optional[Dict]:
        """
        Get token information without verification (for debugging)
        
        Args:
            token: JWT token
            
        Returns:
            dict: Token information
        """
        try:
            # Decode without verification
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            
            return {
                "username": payload.get("sub"),
                "user_id": payload.get("user_id"),
                "role": payload.get("role"),
                "type": payload.get("type"),
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp"),
                "jti": payload.get("jti"),
                "is_expired": datetime.fromtimestamp(payload.get("exp", 0), timezone.utc) < datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return None
    
    def cleanup_blacklist(self) -> int:
        """
        Remove expired tokens from blacklist
        
        Returns:
            int: Number of tokens removed
        """
        # In production, implement proper cleanup logic
        # This would query the token store and remove expired JTIs
        removed_count = 0
        logger.info(f"Blacklist cleanup completed. Removed {removed_count} expired tokens")
        return removed_count

# Global JWT manager instance
jwt_manager = JWTManager()

# Convenience functions
def create_access_token(user_id: str, username: str, role: str, permissions: List[str]) -> str:
    """Create access token using global manager"""
    return jwt_manager.create_access_token(user_id, username, role, permissions)

def create_refresh_token(user_id: str, username: str) -> str:
    """Create refresh token using global manager"""
    return jwt_manager.create_refresh_token(user_id, username)

def verify_token(token: str, expected_type: Optional[TokenType] = None) -> Optional[Dict]:
    """Verify token using global manager"""
    return jwt_manager.verify_token(token, expected_type)

def blacklist_token(token: str) -> bool:
    """Blacklist token using global manager"""
    return jwt_manager.blacklist_token(token)

# Export main components
__all__ = [
    'TokenType', 'TokenConfig', 'JWTManager', 'jwt_manager',
    'create_access_token', 'create_refresh_token', 'verify_token', 'blacklist_token'
]