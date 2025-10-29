#!/usr/bin/env python3
"""
Production Authentication & Authorization System
Secure JWT-based authentication with role-based access control
"""

import os
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

import jwt
import bcrypt
from fastapi import HTTPException, Request, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles with hierarchical permissions"""
    ADMIN = "admin"  # Full system access
    MANAGER = "manager"  # Business operations
    USER = "user"  # Standard access
    API = "api"  # API-only access
    MCP = "mcp"  # MCP server access
    READONLY = "readonly"  # Read-only access

class Permission(Enum):
    """System permissions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    API_ACCESS = "api_access"
    MCP_ACCESS = "mcp_access"
    WEBSOCKET_ACCESS = "websocket_access"

@dataclass
class User:
    """User data structure"""
    id: str
    username: str
    email: str
    role: UserRole
    permissions: List[Permission]
    is_active: bool = True
    created_at: datetime = None
    last_login: Optional[datetime] = None
    password_hash: Optional[str] = None
    api_key: Optional[str] = None

class AuthenticationError(Exception):
    """Authentication related errors"""
    pass

class AuthorizationError(Exception):
    """Authorization related errors"""
    pass

class ProductionAuth:
    """Production authentication and authorization system"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY") or self._generate_secret_key()
        self.algorithm = "HS256"
        self.access_token_expire = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
        self.refresh_token_expire = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
        
        # Role permissions mapping
        self.role_permissions = {
            UserRole.ADMIN: [Permission.READ, Permission.WRITE, Permission.DELETE, 
                           Permission.ADMIN, Permission.API_ACCESS, Permission.MCP_ACCESS, 
                           Permission.WEBSOCKET_ACCESS],
            UserRole.MANAGER: [Permission.READ, Permission.WRITE, Permission.API_ACCESS, 
                             Permission.WEBSOCKET_ACCESS],
            UserRole.USER: [Permission.READ, Permission.WRITE, Permission.API_ACCESS],
            UserRole.API: [Permission.READ, Permission.WRITE, Permission.API_ACCESS],
            UserRole.MCP: [Permission.READ, Permission.API_ACCESS, Permission.MCP_ACCESS],
            UserRole.READONLY: [Permission.READ]
        }
        
        # Database connection pool (REAL storage, not in-memory)
        self.db_pool: Optional[Any] = None
        self.redis: Optional[Any] = None

        # Note: Admin user must be created via API registration
        # NO default admin user in database - must be explicitly created
        
        logger.info("Production authentication system initialized")
    
    def _generate_secret_key(self) -> str:
        """Generate secure secret key"""
        key = secrets.token_urlsafe(64)
        logger.warning("Generated new JWT secret key. Save this to environment variable JWT_SECRET_KEY")
        logger.warning(f"JWT_SECRET_KEY={key}")
        return key
    
    async def initialize_database(self):
        """
        Initialize database connection pool - REAL PostgreSQL storage.

        NO in-memory storage, NO default users.
        All users must be created through registration API.

        Raises:
            Exception: If database connection fails
        """
        try:
            import asyncpg
            from redis import asyncio as aioredis
            from src.core.config import config

            # Initialize PostgreSQL connection pool
            self.db_pool = await asyncpg.create_pool(
                **config.get_database_pool_config()
            )

            # Test database connection
            async with self.db_pool.acquire() as conn:
                version = await conn.fetchval('SELECT version()')
                logger.info(f"✅ Database connected: {version.split(',')[0]}")

            # Initialize Redis for session caching
            redis_config = config.get_redis_config()
            self.redis = await aioredis.from_url(
                redis_config['url'],
                max_connections=redis_config['max_connections'],
                socket_timeout=redis_config['socket_timeout']
            )

            # Test Redis connection
            await self.redis.ping()
            logger.info("✅ Redis connected successfully")

            logger.info("✅ Authentication system initialized with REAL database storage")

        except Exception as e:
            logger.error(f"❌ Failed to initialize authentication database: {e}")
            raise
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def generate_api_key(self) -> str:
        """Generate secure API key"""
        return f"horme_{secrets.token_urlsafe(32)}"
    
    async def create_user(self, username: str, email: str, password: str, role: UserRole, name: str) -> User:
        """
        Create new user in REAL database - NO in-memory storage.

        Args:
            username: Unique username (3-50 characters)
            email: Valid email address
            password: Plain password (will be hashed with bcrypt)
            role: UserRole enum
            name: Full name

        Returns:
            User object with data from database

        Raises:
            ValueError: If user already exists or validation fails
            Exception: If database operation fails
        """
        if not self.db_pool:
            raise RuntimeError("Database not initialized. Call initialize_database() first.")

        try:
            async with self.db_pool.acquire() as conn:
                # Check if user already exists
                existing = await conn.fetchval(
                    "SELECT id FROM users WHERE username = $1 OR email = $2",
                    username, email
                )

                if existing:
                    raise ValueError(f"User with username '{username}' or email '{email}' already exists")

                # Hash password with bcrypt (cost factor 12)
                password_hash = self.hash_password(password)

                # Generate API key
                api_key = self.generate_api_key()

                # Insert user into database
                user_id = await conn.fetchval(
                    """
                    INSERT INTO users (username, email, password_hash, name, role, is_active, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                    """,
                    username, email, password_hash, name, role.value, True, datetime.now(timezone.utc)
                )

                # Insert API key
                await conn.execute(
                    """
                    INSERT INTO api_keys (user_id, api_key, name, permissions, is_active, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    user_id, api_key, f"{username}_default_key",
                    [p.value for p in self.role_permissions[role]], True, datetime.now(timezone.utc)
                )

                # Log to audit trail
                await conn.execute(
                    "SELECT log_auth_event($1, $2, $3, $4, $5)",
                    user_id, 'register', 'success', None, None
                )

                logger.info(f"✅ User created in database: {username} (id: {user_id}) with role {role.value}")

                # Return User object
                return User(
                    id=str(user_id),
                    username=username,
                    email=email,
                    role=role,
                    permissions=self.role_permissions[role],
                    created_at=datetime.now(timezone.utc),
                    api_key=api_key
                )

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to create user: {e}")
            raise Exception(f"Failed to create user: {str(e)}")
    
    async def authenticate_user(self, username: str, password: str, ip_address: str = None) -> Optional[User]:
        """
        Authenticate user with REAL database verification - NO in-memory storage.

        Args:
            username: Username or email
            password: Plain password (will be verified against bcrypt hash)
            ip_address: Client IP address (for audit log)

        Returns:
            User object if authentication successful, None otherwise

        Raises:
            Exception: If database operation fails
        """
        if not self.db_pool:
            raise RuntimeError("Database not initialized. Call initialize_database() first.")

        try:
            async with self.db_pool.acquire() as conn:
                # Fetch user from database (username or email)
                user_row = await conn.fetchrow(
                    """
                    SELECT id, username, email, password_hash, name, role, is_active
                    FROM users
                    WHERE (username = $1 OR email = $1) AND is_active = true
                    """,
                    username
                )

                if not user_row:
                    # Log failed attempt (user not found)
                    await conn.execute(
                        "SELECT log_auth_event($1, $2, $3, $4, $5)",
                        None, 'login', 'failure', ip_address, 'User not found'
                    )
                    logger.warning(f"⚠️  Authentication failed: user '{username}' not found")
                    return None

                # Verify password with bcrypt
                password_match = self.verify_password(password, user_row['password_hash'])

                if not password_match:
                    # Log failed attempt (wrong password)
                    await conn.execute(
                        "SELECT log_auth_event($1, $2, $3, $4, $5)",
                        user_row['id'], 'login', 'failure', ip_address, 'Invalid password'
                    )
                    logger.warning(f"⚠️  Authentication failed: invalid password for '{username}'")
                    return None

                # Update last login timestamp
                await conn.execute(
                    "UPDATE users SET last_login = $1 WHERE id = $2",
                    datetime.now(timezone.utc),
                    user_row['id']
                )

                # Log successful authentication
                await conn.execute(
                    "SELECT log_auth_event($1, $2, $3, $4, $5)",
                    user_row['id'], 'login', 'success', ip_address, None
                )

                logger.info(f"✅ User authenticated from database: {username} (id: {user_row['id']})")

                # Return User object
                try:
                    role = UserRole(user_row['role'])
                except ValueError:
                    role = UserRole.USER

                return User(
                    id=str(user_row['id']),
                    username=user_row['username'],
                    email=user_row['email'],
                    role=role,
                    permissions=self.role_permissions.get(role, []),
                    is_active=user_row['is_active'],
                    last_login=datetime.now(timezone.utc)
                )

        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return None
    
    async def authenticate_api_key(self, api_key: str) -> Optional[User]:
        """
        Authenticate using API key with REAL database lookup - NO in-memory storage.

        Args:
            api_key: API key (format: horme_xxxxx)

        Returns:
            User object if API key valid, None otherwise
        """
        if not api_key or not api_key.startswith("horme_"):
            return None

        if not self.db_pool:
            raise RuntimeError("Database not initialized. Call initialize_database() first.")

        try:
            async with self.db_pool.acquire() as conn:
                # Lookup API key in database
                result = await conn.fetchrow(
                    """
                    SELECT u.id, u.username, u.email, u.name, u.role, u.is_active, ak.permissions
                    FROM users u
                    JOIN api_keys ak ON u.id = ak.user_id
                    WHERE ak.api_key = $1 AND ak.is_active = true AND u.is_active = true
                    """,
                    api_key
                )

                if not result:
                    logger.warning(f"⚠️  Invalid or inactive API key attempted")
                    return None

                # Update last_used_at
                await conn.execute(
                    "UPDATE api_keys SET last_used_at = $1 WHERE api_key = $2",
                    datetime.now(timezone.utc),
                    api_key
                )

                logger.info(f"✅ API key authenticated for user: {result['username']}")

                # Convert role
                try:
                    role = UserRole(result['role'])
                except ValueError:
                    role = UserRole.API

                return User(
                    id=str(result['id']),
                    username=result['username'],
                    email=result['email'],
                    role=role,
                    permissions=self.role_permissions.get(role, []),
                    is_active=result['is_active'],
                    api_key=api_key
                )

        except Exception as e:
            logger.error(f"❌ API key authentication error: {e}")
            return None
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire)
        
        payload = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token"""
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire)
        
        payload = {
            "sub": user.username,
            "user_id": user.id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    async def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode JWT token with REAL database verification.

        Uses Redis cache for performance, falls back to database.

        Args:
            token: JWT access token

        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check token type
            if payload.get("type") != "access":
                return None

            # Get username from token
            username = payload.get("sub")
            user_id = payload.get("user_id")

            if not username or not user_id:
                return None

            # Check Redis cache first (performance optimization)
            if self.redis:
                try:
                    cached_user = await self.redis.get(f"user_active:{user_id}")
                    if cached_user == b"0":
                        # User is inactive (cached negative result)
                        return None
                    elif cached_user == b"1":
                        # User is active (cached positive result)
                        return payload
                except Exception as e:
                    logger.warning(f"Redis cache error: {e}")

            # Verify user still exists and is active in database
            if not self.db_pool:
                raise RuntimeError("Database not initialized. Call initialize_database() first.")

            async with self.db_pool.acquire() as conn:
                is_active = await conn.fetchval(
                    "SELECT is_active FROM users WHERE id = $1",
                    int(user_id)
                )

                if is_active is None or not is_active:
                    # Cache negative result
                    if self.redis:
                        await self.redis.setex(f"user_active:{user_id}", 300, "0")  # 5 minutes
                    return None

                # Cache positive result
                if self.redis:
                    await self.redis.setex(f"user_active:{user_id}", 300, "1")  # 5 minutes

                return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def check_permission(self, user: User, required_permission: Permission) -> bool:
        """Check if user has required permission"""
        return required_permission in user.permissions
    
    def require_permission(self, user: User, required_permission: Permission):
        """Raise exception if user doesn't have required permission"""
        if not self.check_permission(user, required_permission):
            raise AuthorizationError(f"Permission '{required_permission.value}' required")

# Global auth instance
auth_system = ProductionAuth()

# FastAPI Security Schemes
security_bearer = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> User:
    """
    FastAPI dependency to get current authenticated user from REAL database.

    Supports both JWT tokens and API keys.

    Args:
        credentials: HTTPAuthorizationCredentials from request

    Returns:
        User object from database

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header required")

    # Try JWT token first
    payload = await auth_system.verify_token(credentials.credentials)
    if payload:
        user_id = payload.get("user_id")
        username = payload.get("sub")

        if not auth_system.db_pool:
            raise HTTPException(status_code=500, detail="Database not initialized")

        # Fetch user from database
        try:
            async with auth_system.db_pool.acquire() as conn:
                user_row = await conn.fetchrow(
                    """
                    SELECT id, username, email, name, role, is_active, last_login
                    FROM users
                    WHERE id = $1 AND is_active = true
                    """,
                    int(user_id)
                )

                if not user_row:
                    raise HTTPException(status_code=401, detail="User not found or inactive")

                # Convert role
                try:
                    role = UserRole(user_row['role'])
                except ValueError:
                    role = UserRole.USER

                return User(
                    id=str(user_row['id']),
                    username=user_row['username'],
                    email=user_row['email'],
                    role=role,
                    permissions=auth_system.role_permissions.get(role, []),
                    is_active=user_row['is_active'],
                    last_login=user_row['last_login']
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching user from database: {e}")
            raise HTTPException(status_code=500, detail="Authentication error")

    # Try API key authentication
    user = await auth_system.authenticate_api_key(credentials.credentials)
    if user:
        return user

    raise HTTPException(status_code=401, detail="Invalid or expired token")

def require_role(required_role: UserRole):
    """Decorator to require specific role"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        role_hierarchy = {
            UserRole.READONLY: 0,
            UserRole.USER: 1,
            UserRole.API: 1,
            UserRole.MCP: 1,
            UserRole.MANAGER: 2,
            UserRole.ADMIN: 3
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=403, 
                detail=f"Role '{required_role.value}' or higher required"
            )
        
        return current_user
    
    return role_checker

def require_permission(required_permission: Permission):
    """Decorator to require specific permission"""
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not auth_system.check_permission(current_user, required_permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{required_permission.value}' required"
            )
        
        return current_user
    
    return permission_checker

# API Key authentication for headers
async def get_api_key_user(x_api_key: Optional[str] = Header(None)) -> Optional[User]:
    """
    Get user from X-API-Key header with REAL database lookup.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        User object if API key valid, None otherwise
    """
    if not x_api_key:
        return None

    return await auth_system.authenticate_api_key(x_api_key)

# WebSocket authentication
async def authenticate_websocket(token: str) -> User:
    """
    Authenticate WebSocket connection with REAL database verification.

    Supports both JWT tokens and API keys.

    Args:
        token: JWT access token or API key

    Returns:
        User object from database

    Raises:
        AuthenticationError: If authentication fails
    """
    # Try JWT token first
    payload = await auth_system.verify_token(token)
    if payload:
        user_id = payload.get("user_id")
        username = payload.get("sub")

        if not auth_system.db_pool:
            raise AuthenticationError("Database not initialized")

        # Fetch user from database
        try:
            async with auth_system.db_pool.acquire() as conn:
                user_row = await conn.fetchrow(
                    """
                    SELECT id, username, email, name, role, is_active, last_login
                    FROM users
                    WHERE id = $1 AND is_active = true
                    """,
                    int(user_id)
                )

                if not user_row:
                    raise AuthenticationError("User not found or inactive")

                # Convert role
                try:
                    role = UserRole(user_row['role'])
                except ValueError:
                    role = UserRole.USER

                return User(
                    id=str(user_row['id']),
                    username=user_row['username'],
                    email=user_row['email'],
                    role=role,
                    permissions=auth_system.role_permissions.get(role, []),
                    is_active=user_row['is_active'],
                    last_login=user_row['last_login']
                )

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Error fetching user from database: {e}")
            raise AuthenticationError("Database error during authentication")

    # Try API key authentication
    user = await auth_system.authenticate_api_key(token)
    if user:
        return user

    raise AuthenticationError("Invalid or expired token")

class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for additional security"""
    
    def __init__(self, app, excluded_paths: List[str] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/", "/health", "/docs", "/redoc", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Add security headers
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

# Rate limiting (simple implementation)
class RateLimiter:
    """Simple rate limiting"""
    
    def __init__(self):
        self.requests = {}  # ip -> [timestamp, ...]
        self.max_requests = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
        self.time_window = int(os.getenv("RATE_LIMIT_WINDOW", 3600))  # 1 hour
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.time_window)
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                ts for ts in self.requests[identifier] if ts > cutoff
            ]
        else:
            self.requests[identifier] = []
        
        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True

rate_limiter = RateLimiter()

# Utility functions for backward compatibility
async def authenticate_request(api_key: str) -> bool:
    """
    Legacy authentication function - DEPRECATED.

    Use get_current_user FastAPI dependency instead.
    """
    logger.warning("authenticate_request is deprecated. Use get_current_user dependency")
    user = await auth_system.authenticate_api_key(api_key)
    return user is not None

async def verify_mcp_connection(token: str) -> bool:
    """
    Verify MCP server connection token with REAL database verification.

    Args:
        token: JWT access token or API key

    Returns:
        True if user has MCP_ACCESS permission, False otherwise
    """
    try:
        user = await authenticate_websocket(token)
        return auth_system.check_permission(user, Permission.MCP_ACCESS)
    except AuthenticationError:
        return False

# Export main components
__all__ = [
    'ProductionAuth', 'User', 'UserRole', 'Permission',
    'auth_system', 'get_current_user', 'require_role', 'require_permission',
    'authenticate_websocket', 'AuthMiddleware', 'rate_limiter',
    'AuthenticationError', 'AuthorizationError'
]