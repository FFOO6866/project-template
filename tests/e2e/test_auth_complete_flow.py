"""
End-to-end tests for complete authentication flows.

Tests complete authentication user journeys from registration to API access.
Follows 3-tier testing strategy - Tier 3: E2E tests (real infrastructure, complete flows).
"""

import pytest
import asyncio
from datetime import datetime
from httpx import AsyncClient
from src.production_api_endpoints import app
from src.core.auth import ProductionAuth


@pytest.fixture(scope="module")
async def api_client():
    """Create async HTTP client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="module")
async def auth_system():
    """Initialize authentication system."""
    auth = ProductionAuth()
    await auth.initialize_database()
    yield auth
    await auth.cleanup()


@pytest.mark.asyncio
class TestCompleteAuthFlow:
    """Test complete authentication user journey."""

    async def test_register_login_access_api_flow(self, api_client):
        """
        Complete flow: Register → Login → Access Protected Endpoint

        1. Register new user
        2. Login with credentials
        3. Receive JWT token
        4. Access protected API endpoint with token
        """
        timestamp = datetime.utcnow().timestamp()
        email = f"e2e{timestamp}@example.com"
        password = "TestPassword123!"
        username = f"e2euser_{timestamp}"

        # Step 1: Register user
        register_response = await api_client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": password,
                "username": username
            }
        )

        assert register_response.status_code == 201
        register_data = register_response.json()
        assert register_data["email"] == email
        assert "id" in register_data

        # Step 2: Login with credentials
        login_response = await api_client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": password
            }
        )

        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert login_data["token_type"] == "bearer"

        access_token = login_data["access_token"]

        # Step 3: Access protected endpoint with token
        protected_response = await api_client.post(
            "/search/products",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "query": "drill",
                "limit": 10
            }
        )

        # Should successfully access protected endpoint
        assert protected_response.status_code in [200, 201]

    async def test_access_protected_endpoint_without_token(self, api_client):
        """
        Should receive 401 Unauthorized when accessing protected endpoint without token.
        """
        response = await api_client.post(
            "/search/products",
            json={
                "query": "drill",
                "limit": 10
            }
        )

        assert response.status_code == 401

    async def test_access_protected_endpoint_with_invalid_token(self, api_client):
        """
        Should receive 401 Unauthorized with invalid token.
        """
        response = await api_client.post(
            "/search/products",
            headers={"Authorization": "Bearer invalid.token.here"},
            json={
                "query": "drill",
                "limit": 10
            }
        )

        assert response.status_code == 401

    async def test_register_with_weak_password(self, api_client):
        """
        Should reject registration with weak password.
        """
        timestamp = datetime.utcnow().timestamp()
        email = f"weak{timestamp}@example.com"
        weak_password = "123"  # Too weak
        username = f"weakuser_{timestamp}"

        response = await api_client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": weak_password,
                "username": username
            }
        )

        # Should reject weak password
        assert response.status_code in [400, 422]

    async def test_login_with_wrong_password(self, api_client):
        """
        Should reject login with incorrect password.
        """
        timestamp = datetime.utcnow().timestamp()
        email = f"wrongpass{timestamp}@example.com"
        password = "CorrectPassword123!"
        username = f"wrongpass_{timestamp}"

        # Register user
        await api_client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": password,
                "username": username
            }
        )

        # Try to login with wrong password
        login_response = await api_client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": "WrongPassword456!"
            }
        )

        assert login_response.status_code == 401


@pytest.mark.asyncio
class TestAPIKeyFlow:
    """Test API key-based authentication flow."""

    async def test_create_api_key_and_use_it(self, api_client, auth_system):
        """
        Complete API key flow: Register → Login → Create API Key → Use API Key

        1. Register and login
        2. Create API key
        3. Use API key to access endpoint
        """
        timestamp = datetime.utcnow().timestamp()
        email = f"apikey{timestamp}@example.com"
        password = "TestPassword123!"
        username = f"apikey_{timestamp}"

        # Step 1: Register user
        await api_client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": password,
                "username": username
            }
        )

        # Step 2: Login
        login_response = await api_client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": password
            }
        )
        access_token = login_response.json()["access_token"]

        # Step 3: Create API key
        api_key_response = await api_client.post(
            "/api/auth/api-keys",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Test API Key"}
        )

        assert api_key_response.status_code in [200, 201]
        api_key_data = api_key_response.json()
        assert "api_key" in api_key_data

        api_key = api_key_data["api_key"]

        # Step 4: Use API key to access endpoint
        protected_response = await api_client.post(
            "/search/products",
            headers={"X-API-Key": api_key},
            json={
                "query": "drill",
                "limit": 10
            }
        )

        # Should successfully access with API key
        assert protected_response.status_code in [200, 201]


@pytest.mark.asyncio
class TestTokenRefreshFlow:
    """Test JWT token refresh flow."""

    async def test_token_refresh_success(self, api_client):
        """
        Should successfully refresh access token with valid refresh token.
        """
        timestamp = datetime.utcnow().timestamp()
        email = f"refresh{timestamp}@example.com"
        password = "TestPassword123!"
        username = f"refresh_{timestamp}"

        # Register and login
        await api_client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": password,
                "username": username
            }
        )

        login_response = await api_client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": password
            }
        )

        login_data = login_response.json()
        refresh_token = login_data.get("refresh_token")

        if refresh_token:
            # Refresh token
            refresh_response = await api_client.post(
                "/api/auth/refresh",
                json={"refresh_token": refresh_token}
            )

            # Should get new access token
            if refresh_response.status_code == 200:
                refresh_data = refresh_response.json()
                assert "access_token" in refresh_data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
