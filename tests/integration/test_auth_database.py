"""
Integration tests for authentication with real database.

Tests authentication system with real PostgreSQL database connection.
Follows 3-tier testing strategy - Tier 2: Integration tests (real infrastructure, no mocking).
"""

import pytest
import asyncio
from datetime import datetime
from src.core.auth import (
    ProductionAuth,
    User,
    UserRole,
    Permission,
    AuthenticationError,
    AuthorizationError
)


@pytest.fixture(scope="module")
async def auth_with_db():
    """Initialize ProductionAuth with real database connection."""
    auth = ProductionAuth()
    await auth.initialize_database()
    yield auth
    # Cleanup after tests
    await auth.cleanup()


@pytest.mark.asyncio
class TestUserRegistration:
    """Test user registration with real database."""

    async def test_register_user_success(self, auth_with_db):
        """Should successfully register new user in database."""
        email = f"test{datetime.utcnow().timestamp()}@example.com"
        password = "TestPassword123!"
        username = f"testuser_{datetime.utcnow().timestamp()}"

        user = await auth_with_db.register_user(
            email=email,
            password=password,
            username=username
        )

        assert user is not None
        assert user.email == email
        assert user.username == username
        assert user.role == UserRole.USER
        assert user.is_active is True

    async def test_register_user_duplicate_email(self, auth_with_db):
        """Should raise error when registering duplicate email."""
        email = f"duplicate{datetime.utcnow().timestamp()}@example.com"
        password = "TestPassword123!"
        username = f"user1_{datetime.utcnow().timestamp()}"

        # Register first user
        await auth_with_db.register_user(
            email=email,
            password=password,
            username=username
        )

        # Try to register with same email
        with pytest.raises(Exception):  # Should raise ValueError or similar
            await auth_with_db.register_user(
                email=email,
                password=password,
                username=f"user2_{datetime.utcnow().timestamp()}"
            )

    async def test_register_user_with_custom_role(self, auth_with_db):
        """Should register user with custom role."""
        email = f"admin{datetime.utcnow().timestamp()}@example.com"
        password = "AdminPassword123!"
        username = f"adminuser_{datetime.utcnow().timestamp()}"

        user = await auth_with_db.register_user(
            email=email,
            password=password,
            username=username,
            role=UserRole.ADMIN
        )

        assert user.role == UserRole.ADMIN


@pytest.mark.asyncio
class TestUserAuthentication:
    """Test user login authentication with real database."""

    async def test_authenticate_user_success(self, auth_with_db):
        """Should successfully authenticate user with correct credentials."""
        email = f"authtest{datetime.utcnow().timestamp()}@example.com"
        password = "TestPassword123!"
        username = f"authuser_{datetime.utcnow().timestamp()}"

        # Register user first
        await auth_with_db.register_user(
            email=email,
            password=password,
            username=username
        )

        # Authenticate with correct credentials
        user = await auth_with_db.authenticate_user(email, password)

        assert user is not None
        assert user.email == email
        assert user.is_active is True

    async def test_authenticate_user_wrong_password(self, auth_with_db):
        """Should raise error for incorrect password."""
        email = f"wrongpass{datetime.utcnow().timestamp()}@example.com"
        password = "TestPassword123!"
        username = f"wrongpass_{datetime.utcnow().timestamp()}"

        # Register user
        await auth_with_db.register_user(
            email=email,
            password=password,
            username=username
        )

        # Try to authenticate with wrong password
        with pytest.raises(AuthenticationError):
            await auth_with_db.authenticate_user(email, "WrongPassword456!")

    async def test_authenticate_user_nonexistent(self, auth_with_db):
        """Should raise error for non-existent user."""
        with pytest.raises(AuthenticationError):
            await auth_with_db.authenticate_user(
                "nonexistent@example.com",
                "AnyPassword123!"
            )

    async def test_authenticate_inactive_user(self, auth_with_db):
        """Should raise error for inactive user."""
        email = f"inactive{datetime.utcnow().timestamp()}@example.com"
        password = "TestPassword123!"
        username = f"inactive_{datetime.utcnow().timestamp()}"

        # Register user
        user = await auth_with_db.register_user(
            email=email,
            password=password,
            username=username
        )

        # Deactivate user
        await auth_with_db.deactivate_user(user.id)

        # Try to authenticate
        with pytest.raises(AuthenticationError):
            await auth_with_db.authenticate_user(email, password)


@pytest.mark.asyncio
class TestUserRetrieval:
    """Test user retrieval from database."""

    async def test_get_user_by_id_exists(self, auth_with_db):
        """Should retrieve user by ID."""
        email = f"getbyid{datetime.utcnow().timestamp()}@example.com"
        password = "TestPassword123!"
        username = f"getbyid_{datetime.utcnow().timestamp()}"

        # Register user
        created_user = await auth_with_db.register_user(
            email=email,
            password=password,
            username=username
        )

        # Retrieve by ID
        retrieved_user = await auth_with_db.get_user_by_id(created_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email

    async def test_get_user_by_id_not_exists(self, auth_with_db):
        """Should return None for non-existent user ID."""
        non_existent_id = f"non-existent-{datetime.utcnow().timestamp()}"

        user = await auth_with_db.get_user_by_id(non_existent_id)

        assert user is None

    async def test_get_user_by_email_exists(self, auth_with_db):
        """Should retrieve user by email."""
        email = f"getbyemail{datetime.utcnow().timestamp()}@example.com"
        password = "TestPassword123!"
        username = f"getbyemail_{datetime.utcnow().timestamp()}"

        # Register user
        created_user = await auth_with_db.register_user(
            email=email,
            password=password,
            username=username
        )

        # Retrieve by email
        retrieved_user = await auth_with_db.get_user_by_email(email)

        assert retrieved_user is not None
        assert retrieved_user.email == email
        assert retrieved_user.id == created_user.id


@pytest.mark.asyncio
class TestAPIKeyManagement:
    """Test API key creation and validation with database."""

    async def test_create_api_key_for_user(self, auth_with_db):
        """Should create API key for user and store in database."""
        email = f"apikey{datetime.utcnow().timestamp()}@example.com"
        password = "TestPassword123!"
        username = f"apikey_{datetime.utcnow().timestamp()}"

        # Register user
        user = await auth_with_db.register_user(
            email=email,
            password=password,
            username=username
        )

        # Create API key
        api_key = await auth_with_db.create_api_key(
            user_id=user.id,
            name="Test API Key"
        )

        assert api_key is not None
        assert isinstance(api_key, str)
        assert len(api_key) > 0

    async def test_validate_api_key_success(self, auth_with_db):
        """Should successfully validate correct API key."""
        email = f"validateapi{datetime.utcnow().timestamp()}@example.com"
        password = "TestPassword123!"
        username = f"validateapi_{datetime.utcnow().timestamp()}"

        # Register user and create API key
        user = await auth_with_db.register_user(
            email=email,
            password=password,
            username=username
        )
        api_key = await auth_with_db.create_api_key(
            user_id=user.id,
            name="Test API Key"
        )

        # Validate API key
        validated_user = await auth_with_db.validate_api_key(api_key)

        assert validated_user is not None
        assert validated_user.id == user.id
        assert validated_user.email == user.email

    async def test_validate_api_key_invalid(self, auth_with_db):
        """Should raise error for invalid API key."""
        invalid_api_key = "invalid-api-key-12345"

        with pytest.raises(AuthenticationError):
            await auth_with_db.validate_api_key(invalid_api_key)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
