"""
Authentication Utilities - JWT, Password Hashing, Token Management
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import secrets

from passlib.context import CryptContext
from jose import JWTError, jwt

from job_pricing.core.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password

    Note:
        Bcrypt has a maximum password length of 72 bytes.
        Passwords are truncated to this length before hashing.
    """
    # Bcrypt maximum is 72 bytes - truncate if necessary
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes.decode('utf-8'))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against

    Returns:
        True if password matches, False otherwise

    Note:
        Bcrypt has a maximum password length of 72 bytes.
        Passwords are truncated to this length before verification.
    """
    # Bcrypt maximum is 72 bytes - truncate if necessary
    password_bytes = plain_password.encode('utf-8')[:72]
    return pwd_context.verify(password_bytes.decode('utf-8'), hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token (user_id, email, role, etc.)
        expires_delta: Token expiration time (default: from settings)

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Data to encode in the token (user_id, email)
        expires_delta: Token expiration time (default: from settings)

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh", "jti": secrets.token_urlsafe(32)})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    return payload


def generate_api_key() -> str:
    """
    Generate a random API key.

    Returns:
        Random API key (64 characters)
    """
    return secrets.token_urlsafe(48)


def verify_api_key(api_key: str, hashed_api_key: str) -> bool:
    """
    Verify an API key against a hashed version.

    Args:
        api_key: Plain API key
        hashed_api_key: Hashed API key

    Returns:
        True if API key matches, False otherwise
    """
    return pwd_context.verify(api_key, hashed_api_key)
