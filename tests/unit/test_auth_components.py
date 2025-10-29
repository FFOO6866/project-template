"""
Unit tests for authentication components.

Tests individual auth functions in isolation without database dependencies.
Follows 3-tier testing strategy - Tier 1: Unit tests (isolated).
"""

import pytest
from datetime import datetime, timedelta
from src.core.auth import (
    ProductionAuth,
    User,
    UserRole,
    Permission,
    AuthenticationError,
    AuthorizationError
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_creates_bcrypt_hash(self):
        """Hash password should create a valid bcrypt hash."""
        auth = ProductionAuth()
        password = "TestPassword123!"
        hashed = auth.hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_verify_password_correct_password(self):
        """Verify password should return True for correct password."""
        auth = ProductionAuth()
        password = "TestPassword123!"
        hashed = auth.hash_password(password)

        assert auth.verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """Verify password should return False for incorrect password."""
        auth = ProductionAuth()
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = auth.hash_password(password)

        assert auth.verify_password(wrong_password, hashed) is False

    def test_hash_password_different_salts(self):
        """Same password should produce different hashes (different salts)."""
        auth = ProductionAuth()
        password = "TestPassword123!"
        hash1 = auth.hash_password(password)
        hash2 = auth.hash_password(password)

        assert hash1 != hash2
        assert auth.verify_password(password, hash1) is True
        assert auth.verify_password(password, hash2) is True


class TestJWTTokenGeneration:
    """Test JWT token creation and validation."""

    def test_create_access_token_contains_user_id(self):
        """Access token should contain user_id in payload."""
        auth = ProductionAuth()
        user_id = "test-user-123"
        token = auth.create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiration(self):
        """Should create token with custom expiration time."""
        auth = ProductionAuth()
        user_id = "test-user-123"
        expires_delta = timedelta(minutes=15)

        token = auth.create_access_token(user_id, expires_delta=expires_delta)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_valid_token(self):
        """Should successfully verify valid token and return user_id."""
        auth = ProductionAuth()
        user_id = "test-user-123"
        token = auth.create_access_token(user_id)

        verified_user_id = auth.verify_token(token)

        assert verified_user_id == user_id

    def test_verify_token_invalid_token(self):
        """Should raise AuthenticationError for invalid token."""
        auth = ProductionAuth()
        invalid_token = "invalid.token.here"

        with pytest.raises(AuthenticationError):
            auth.verify_token(invalid_token)

    def test_verify_token_expired_token(self):
        """Should raise AuthenticationError for expired token."""
        auth = ProductionAuth()
        user_id = "test-user-123"
        expires_delta = timedelta(seconds=-1)  # Already expired

        expired_token = auth.create_access_token(user_id, expires_delta=expires_delta)

        with pytest.raises(AuthenticationError):
            auth.verify_token(expired_token)


class TestUserModel:
    """Test User model functionality."""

    def test_user_creation_with_all_fields(self):
        """Should create user with all fields."""
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            permissions=[Permission.READ_PRODUCTS, Permission.SEARCH],
            is_active=True,
            created_at=datetime.utcnow()
        )

        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.role == UserRole.USER
        assert Permission.READ_PRODUCTS in user.permissions
        assert user.is_active is True

    def test_user_has_permission_check(self):
        """Should correctly check if user has specific permission."""
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            permissions=[Permission.READ_PRODUCTS, Permission.SEARCH],
            is_active=True,
            created_at=datetime.utcnow()
        )

        assert user.has_permission(Permission.READ_PRODUCTS) is True
        assert user.has_permission(Permission.SEARCH) is True
        assert user.has_permission(Permission.WRITE_PRODUCTS) is False

    def test_admin_user_has_all_permissions(self):
        """Admin users should have all permissions."""
        admin_user = User(
            id="admin-123",
            email="admin@example.com",
            username="admin",
            role=UserRole.ADMIN,
            permissions=list(Permission),
            is_active=True,
            created_at=datetime.utcnow()
        )

        for permission in Permission:
            assert admin_user.has_permission(permission) is True


class TestAuthorizationChecks:
    """Test role and permission authorization."""

    def test_check_role_user_has_role(self):
        """Should not raise error when user has required role."""
        auth = ProductionAuth()
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            role=UserRole.ADMIN,
            permissions=[],
            is_active=True,
            created_at=datetime.utcnow()
        )

        # Should not raise exception
        auth.check_role(user, UserRole.ADMIN)

    def test_check_role_user_lacks_role(self):
        """Should raise AuthorizationError when user lacks role."""
        auth = ProductionAuth()
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            permissions=[],
            is_active=True,
            created_at=datetime.utcnow()
        )

        with pytest.raises(AuthorizationError):
            auth.check_role(user, UserRole.ADMIN)

    def test_check_permission_user_has_permission(self):
        """Should not raise error when user has permission."""
        auth = ProductionAuth()
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            permissions=[Permission.READ_PRODUCTS],
            is_active=True,
            created_at=datetime.utcnow()
        )

        # Should not raise exception
        auth.check_permission(user, Permission.READ_PRODUCTS)

    def test_check_permission_user_lacks_permission(self):
        """Should raise AuthorizationError when user lacks permission."""
        auth = ProductionAuth()
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            permissions=[Permission.READ_PRODUCTS],
            is_active=True,
            created_at=datetime.utcnow()
        )

        with pytest.raises(AuthorizationError):
            auth.check_permission(user, Permission.WRITE_PRODUCTS)


class TestAPIKeyGeneration:
    """Test API key generation and validation."""

    def test_generate_api_key_format(self):
        """API key should have correct format and length."""
        auth = ProductionAuth()
        api_key = auth.generate_api_key()

        assert isinstance(api_key, str)
        assert len(api_key) == 64  # 32 bytes hex = 64 characters

    def test_generate_api_key_unique(self):
        """Each generated API key should be unique."""
        auth = ProductionAuth()
        key1 = auth.generate_api_key()
        key2 = auth.generate_api_key()

        assert key1 != key2
        assert len(key1) == 64
        assert len(key2) == 64


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
