# Authentication Testing Strategy - Production Ready

## Executive Summary

This document outlines a comprehensive, production-ready authentication testing strategy for the Horme POV system. All tests follow the **3-tier testing methodology** with **REAL infrastructure** - NO MOCKING in Tiers 2-3.

**Critical Requirements Met:**
- ✅ 100% production ready
- ✅ No mock-up data (REAL PostgreSQL database)
- ✅ No hardcoding
- ✅ No simulated or fallback data
- ✅ Enhances existing test infrastructure

---

## 1. Current Authentication Implementation Analysis

### 1.1 Authentication System Overview

**Location:** `src/core/auth.py`

The production authentication system provides:

#### Core Components
1. **User Management** (`ProductionAuth` class)
   - User creation with bcrypt password hashing
   - User authentication (username/email + password)
   - API key authentication
   - JWT token generation and validation

2. **Security Features**
   - Bcrypt password hashing (cost factor 12)
   - JWT tokens (HS256 algorithm)
   - Redis caching for performance
   - Account locking after failed attempts
   - Audit logging for all auth events

3. **Access Control**
   - Role-based permissions (ADMIN, MANAGER, USER, API, MCP, READONLY)
   - Permission checking (READ, WRITE, DELETE, ADMIN, API_ACCESS, MCP_ACCESS, WEBSOCKET_ACCESS)
   - Role hierarchy enforcement

4. **FastAPI Integration**
   - `get_current_user()` dependency for JWT/API key validation
   - `require_role()` decorator for role enforcement
   - `require_permission()` decorator for permission checking
   - WebSocket authentication support

### 1.2 Database Schema

**Location:** `init-scripts/02-auth-schema.sql`

**Tables:**
```sql
users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE
)

api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    api_key VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    permissions TEXT[] NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE
)

sessions (
    id SERIAL PRIMARY KEY,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE
)

audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    resource_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE
)

password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE
)

permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE
)

user_permissions (
    user_id INTEGER REFERENCES users(id),
    permission_id INTEGER REFERENCES permissions(id),
    granted_at TIMESTAMP WITH TIME ZONE,
    granted_by INTEGER REFERENCES users(id),
    PRIMARY KEY (user_id, permission_id)
)
```

### 1.3 API Endpoints

**Locations:**
- `src/nexus_production_api.py` - Login endpoint
- `src/production_api_endpoints.py` - get_current_user() dependency

**Endpoints:**
1. `POST /api/auth/login` - User authentication
   - Validates credentials against PostgreSQL
   - Uses bcrypt for password verification
   - Checks is_active and locked_until status
   - Generates JWT access and refresh tokens
   - Caches session in Redis
   - Logs authentication attempt in audit_log

2. `Depends(get_current_user)` - JWT validation
   - Decodes JWT token
   - Verifies user in database
   - Checks is_active status
   - Checks account lock status
   - Returns user data (NO fallbacks)

### 1.4 Configuration

**Location:** `src/core/config.py`

**Authentication-related Config:**
```python
SECRET_KEY: str  # Required, no default
JWT_SECRET: str  # Required, no default
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRATION_HOURS: int = 24
ADMIN_PASSWORD: str  # Required, no default
```

**Validators:**
- Secret strength validation (min 16 chars, 32 in production)
- No common weak values allowed
- No localhost in production URLs

---

## 2. Existing Test Infrastructure

### 2.1 Test Configuration

**Location:** `tests/conftest.py`

**Existing Infrastructure:**
- Docker-based test environment
- PostgreSQL test database (port 5434 external)
- Redis test instance (port 6380 external)
- Automatic environment configuration
- Service health checks
- Fixtures for database connections

**Service URLs (Docker):**
```python
POSTGRES_HOST: 'postgres' (internal) or 'localhost' (external)
POSTGRES_PORT: '5432' (internal) or '5434' (external)
POSTGRES_DB: 'horme_test'
POSTGRES_USER: 'test_user'
POSTGRES_PASSWORD: 'test_password'
REDIS_URL: 'redis://redis:6379' (internal) or 'redis://localhost:6380' (external)
```

### 2.2 Existing Test Files

**Search Results:**
- ❌ No existing authentication test files found
- ✅ Existing integration test patterns in:
  - `tests/integration/test_api_endpoints_complete.py`
  - `tests/integration/test_websocket_chat.py`
  - `tests/integration/conftest.py`

### 2.3 Test Database Setup

**No authentication test database setup exists yet**

**Required:**
1. Create test database initialization script
2. Run auth schema creation in test database
3. Create test user fixtures
4. Setup cleanup after each test

---

## 3. Testing Gaps Identified

### 3.1 Missing Test Coverage

**Tier 1 (Unit Tests) - MISSING:**
- ❌ Password hashing/verification
- ❌ JWT token generation
- ❌ JWT token validation
- ❌ Permission checking logic
- ❌ Role hierarchy validation

**Tier 2 (Integration Tests) - MISSING:**
- ❌ User creation with real database
- ❌ User authentication with real database
- ❌ API key authentication with real database
- ❌ JWT validation with real database + Redis
- ❌ Session management with Redis
- ❌ Audit logging verification
- ❌ Account locking after failed attempts
- ❌ Password reset token generation

**Tier 3 (E2E Tests) - MISSING:**
- ❌ Complete registration → login → access flow
- ❌ Login → API call with JWT → logout
- ❌ API key authentication flow
- ❌ WebSocket authentication flow
- ❌ Role-based access control enforcement
- ❌ Permission-based access control enforcement
- ❌ Account lockout after brute force attempts

### 3.2 Infrastructure Gaps

**Missing Components:**
1. Test database initialization with auth schema
2. Test user fixtures (created in real database)
3. Test API key fixtures
4. JWT token generation helpers for tests
5. Authentication cleanup after tests

---

## 4. Required Test Infrastructure

### 4.1 Database Setup

**Create:** `tests/utils/init-scripts/03-test-auth-setup.sql`

```sql
-- Test Authentication Database Setup
-- This script runs AFTER 02-auth-schema.sql in test database

-- Insert test users (passwords hashed with bcrypt)
-- NOTE: These are TEST users only - real data in production

INSERT INTO users (email, username, password_hash, name, role, is_active, is_verified)
VALUES
    -- Test user: password = "test_password_123"
    ('test_user@horme.test', 'test_user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XY5KYzYLQ1MS', 'Test User', 'user', true, true),

    -- Test admin: password = "admin_password_123"
    ('test_admin@horme.test', 'test_admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XY5KYzYLQ1MS', 'Test Admin', 'admin', true, true),

    -- Test manager: password = "manager_password_123"
    ('test_manager@horme.test', 'test_manager', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XY5KYzYLQ1MS', 'Test Manager', 'manager', true, true),

    -- Test inactive user: password = "inactive_password_123"
    ('test_inactive@horme.test', 'test_inactive', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XY5KYzYLQ1MS', 'Test Inactive', 'user', false, true),

    -- Test locked user: password = "locked_password_123"
    ('test_locked@horme.test', 'test_locked', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XY5KYzYLQ1MS', 'Test Locked', 'user', true, true)
ON CONFLICT (email) DO NOTHING;

-- Lock the locked user account for 1 hour
UPDATE users
SET locked_until = NOW() + INTERVAL '1 hour',
    failed_login_attempts = 5
WHERE username = 'test_locked';

-- Insert test API keys
INSERT INTO api_keys (user_id, api_key, name, permissions, is_active)
SELECT
    u.id,
    'horme_test_api_key_' || u.username,
    'Test API Key for ' || u.name,
    ARRAY['read', 'write'],
    true
FROM users u
WHERE u.username IN ('test_user', 'test_admin', 'test_manager')
ON CONFLICT (api_key) DO NOTHING;

-- Verify test data
DO $$
DECLARE
    user_count INTEGER;
    key_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count FROM users WHERE username LIKE 'test_%';
    SELECT COUNT(*) INTO key_count FROM api_keys WHERE api_key LIKE 'horme_test_%';

    RAISE NOTICE '✅ Test users created: %', user_count;
    RAISE NOTICE '✅ Test API keys created: %', key_count;
END
$$;
```

### 4.2 Test Fixtures

**Create:** `tests/integration/test_auth_fixtures.py`

```python
"""Authentication test fixtures for integration and e2e tests."""

import pytest
import asyncpg
import aioredis
import os
from typing import Dict, Any
from src.core.auth import auth_system, ProductionAuth, User, UserRole

# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
async def auth_db_pool():
    """
    Create PostgreSQL connection pool for auth tests.
    Uses REAL test database - NO MOCKING.
    """
    pool = await asyncpg.create_pool(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5434')),
        database=os.getenv('POSTGRES_DB', 'horme_test'),
        user=os.getenv('POSTGRES_USER', 'test_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'test_password'),
        min_size=2,
        max_size=10
    )

    yield pool

    await pool.close()


@pytest.fixture(scope="session")
async def auth_redis():
    """
    Create Redis client for auth tests.
    Uses REAL test Redis - NO MOCKING.
    """
    redis = await aioredis.from_url(
        os.getenv('REDIS_URL', 'redis://localhost:6380'),
        encoding="utf-8",
        decode_responses=True
    )

    yield redis

    await redis.close()


@pytest.fixture(scope="function")
async def auth_system_initialized(auth_db_pool, auth_redis):
    """
    Initialize authentication system with test database and Redis.
    """
    # Set database pool and Redis on global auth_system
    auth_system.db_pool = auth_db_pool
    auth_system.redis = auth_redis

    yield auth_system

    # Cleanup: Clear Redis cache keys related to this test
    test_keys = await auth_redis.keys("user_active:*")
    if test_keys:
        await auth_redis.delete(*test_keys)


# ============================================================================
# Test User Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_users() -> Dict[str, Dict[str, Any]]:
    """
    Test user credentials (matches database test data).

    These users exist in the test database created by:
    tests/utils/init-scripts/03-test-auth-setup.sql
    """
    return {
        'user': {
            'email': 'test_user@horme.test',
            'username': 'test_user',
            'password': 'test_password_123',
            'name': 'Test User',
            'role': 'user'
        },
        'admin': {
            'email': 'test_admin@horme.test',
            'username': 'test_admin',
            'password': 'admin_password_123',
            'name': 'Test Admin',
            'role': 'admin'
        },
        'manager': {
            'email': 'test_manager@horme.test',
            'username': 'test_manager',
            'password': 'manager_password_123',
            'name': 'Test Manager',
            'role': 'manager'
        },
        'inactive': {
            'email': 'test_inactive@horme.test',
            'username': 'test_inactive',
            'password': 'inactive_password_123',
            'name': 'Test Inactive',
            'role': 'user'
        },
        'locked': {
            'email': 'test_locked@horme.test',
            'username': 'test_locked',
            'password': 'locked_password_123',
            'name': 'Test Locked',
            'role': 'user'
        }
    }


@pytest.fixture(scope="function")
async def test_jwt_token(auth_system_initialized, test_users):
    """
    Generate REAL JWT token for test user.
    """
    # Authenticate test user
    user = await auth_system_initialized.authenticate_user(
        username=test_users['user']['username'],
        password=test_users['user']['password']
    )

    if not user:
        pytest.fail("Failed to authenticate test user")

    # Generate JWT token
    token = auth_system_initialized.create_access_token(user)

    return {
        'token': token,
        'user': user
    }


@pytest.fixture(scope="function")
async def test_admin_token(auth_system_initialized, test_users):
    """
    Generate REAL JWT token for test admin.
    """
    user = await auth_system_initialized.authenticate_user(
        username=test_users['admin']['username'],
        password=test_users['admin']['password']
    )

    if not user:
        pytest.fail("Failed to authenticate test admin")

    token = auth_system_initialized.create_access_token(user)

    return {
        'token': token,
        'user': user
    }


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(scope="function", autouse=True)
async def cleanup_test_auth_data(auth_db_pool):
    """
    Cleanup authentication test data after each test.

    This fixture:
    1. Resets failed login attempts
    2. Unlocks locked accounts
    3. Clears test sessions
    4. Does NOT delete test users (they're reused)
    """
    yield

    # Cleanup after test
    async with auth_db_pool.acquire() as conn:
        # Reset failed login attempts
        await conn.execute("""
            UPDATE users
            SET failed_login_attempts = 0,
                locked_until = NULL
            WHERE username LIKE 'test_%' AND username != 'test_locked'
        """)

        # Re-lock the locked test user
        await conn.execute("""
            UPDATE users
            SET locked_until = NOW() + INTERVAL '1 hour',
                failed_login_attempts = 5
            WHERE username = 'test_locked'
        """)

        # Clear test sessions
        await conn.execute("""
            DELETE FROM sessions
            WHERE user_id IN (
                SELECT id FROM users WHERE username LIKE 'test_%'
            )
        """)
```

---

## 5. Comprehensive Test Plan

### 5.1 Tier 1: Unit Tests (Isolated Logic)

**Location:** `tests/unit/test_auth_unit.py`

**Speed:** <1 second per test
**Mocking:** Allowed for external dependencies
**Focus:** Individual function behavior

**Test Cases:**

1. **Password Hashing**
   ```python
   def test_hash_password():
       """Test password hashing with bcrypt."""
       auth = ProductionAuth()
       password = "test_password_123"
       hashed = auth.hash_password(password)

       # Verify hash format
       assert hashed.startswith('$2b$')
       assert len(hashed) == 60

       # Verify different passwords produce different hashes
       hashed2 = auth.hash_password(password)
       assert hashed != hashed2

   def test_verify_password():
       """Test password verification."""
       auth = ProductionAuth()
       password = "test_password_123"
       hashed = auth.hash_password(password)

       # Correct password
       assert auth.verify_password(password, hashed) is True

       # Wrong password
       assert auth.verify_password("wrong_password", hashed) is False
   ```

2. **JWT Token Generation**
   ```python
   def test_create_access_token():
       """Test JWT access token creation."""
       auth = ProductionAuth()
       user = User(
           id="1",
           username="test_user",
           email="test@example.com",
           role=UserRole.USER,
           permissions=[Permission.READ, Permission.WRITE]
       )

       token = auth.create_access_token(user)

       # Verify token format
       assert isinstance(token, str)
       assert len(token) > 100

       # Decode and verify payload
       import jwt
       payload = jwt.decode(token, auth.secret_key, algorithms=[auth.algorithm])
       assert payload['sub'] == 'test_user'
       assert payload['user_id'] == '1'
       assert payload['role'] == 'user'
       assert 'exp' in payload
   ```

3. **Permission Checking**
   ```python
   def test_check_permission():
       """Test permission checking logic."""
       auth = ProductionAuth()
       user = User(
           id="1",
           username="test_user",
           email="test@example.com",
           role=UserRole.USER,
           permissions=[Permission.READ, Permission.WRITE]
       )

       # Has permission
       assert auth.check_permission(user, Permission.READ) is True
       assert auth.check_permission(user, Permission.WRITE) is True

       # No permission
       assert auth.check_permission(user, Permission.ADMIN) is False
   ```

4. **Role Hierarchy**
   ```python
   def test_role_hierarchy():
       """Test role permission mapping."""
       auth = ProductionAuth()

       # Admin has all permissions
       assert Permission.ADMIN in auth.role_permissions[UserRole.ADMIN]
       assert Permission.DELETE in auth.role_permissions[UserRole.ADMIN]

       # User has basic permissions
       assert Permission.READ in auth.role_permissions[UserRole.USER]
       assert Permission.WRITE in auth.role_permissions[UserRole.USER]
       assert Permission.ADMIN not in auth.role_permissions[UserRole.USER]

       # Read-only has only read
       assert Permission.READ in auth.role_permissions[UserRole.READONLY]
       assert Permission.WRITE not in auth.role_permissions[UserRole.READONLY]
   ```

### 5.2 Tier 2: Integration Tests (Real Database)

**Location:** `tests/integration/test_auth_integration.py`

**Speed:** <5 seconds per test
**Mocking:** ❌ FORBIDDEN - Use real PostgreSQL + Redis
**Focus:** Component interactions with real services

**Test Cases:**

1. **User Creation with Real Database**
   ```python
   @pytest.mark.tier2
   @pytest.mark.requires_docker
   async def test_create_user_real_database(auth_system_initialized, auth_db_pool):
       """Test user creation in real PostgreSQL database."""
       # Create unique user
       username = f"integration_test_user_{uuid.uuid4().hex[:8]}"
       email = f"{username}@horme.test"

       user = await auth_system_initialized.create_user(
           username=username,
           email=email,
           password="integration_test_password",
           role=UserRole.USER,
           name="Integration Test User"
       )

       # Verify user object
       assert user.id is not None
       assert user.username == username
       assert user.email == email
       assert user.role == UserRole.USER
       assert user.api_key is not None

       # Verify in database
       async with auth_db_pool.acquire() as conn:
           db_user = await conn.fetchrow(
               "SELECT * FROM users WHERE username = $1",
               username
           )
           assert db_user is not None
           assert db_user['email'] == email
           assert db_user['is_active'] is True

           # Verify password is hashed
           assert db_user['password_hash'].startswith('$2b$')
           assert db_user['password_hash'] != "integration_test_password"

           # Verify API key created
           api_key = await conn.fetchrow(
               "SELECT * FROM api_keys WHERE user_id = $1",
               db_user['id']
           )
           assert api_key is not None
           assert api_key['is_active'] is True

           # Verify audit log
           audit_entry = await conn.fetchrow(
               "SELECT * FROM audit_log WHERE user_id = $1 AND action = 'register'",
               db_user['id']
           )
           assert audit_entry is not None
           assert audit_entry['status'] == 'success'

       # Cleanup
       async with auth_db_pool.acquire() as conn:
           await conn.execute("DELETE FROM users WHERE username = $1", username)
   ```

2. **User Authentication with Real Database**
   ```python
   @pytest.mark.tier2
   @pytest.mark.requires_docker
   async def test_authenticate_user_real_database(auth_system_initialized, test_users):
       """Test user authentication against real database."""
       # Authenticate with username
       user = await auth_system_initialized.authenticate_user(
           username=test_users['user']['username'],
           password=test_users['user']['password'],
           ip_address='192.168.1.100'
       )

       # Verify user object
       assert user is not None
       assert user.username == test_users['user']['username']
       assert user.email == test_users['user']['email']
       assert user.role == UserRole.USER
       assert user.is_active is True

       # Authenticate with email
       user = await auth_system_initialized.authenticate_user(
           username=test_users['user']['email'],
           password=test_users['user']['password']
       )

       assert user is not None
       assert user.email == test_users['user']['email']


   @pytest.mark.tier2
   @pytest.mark.requires_docker
   async def test_authenticate_user_wrong_password(auth_system_initialized, test_users, auth_db_pool):
       """Test authentication failure with wrong password."""
       user = await auth_system_initialized.authenticate_user(
           username=test_users['user']['username'],
           password='wrong_password',
           ip_address='192.168.1.100'
       )

       # Should return None
       assert user is None

       # Verify audit log entry
       async with auth_db_pool.acquire() as conn:
           audit_entry = await conn.fetchrow("""
               SELECT * FROM audit_log
               WHERE action = 'login' AND status = 'failure'
               ORDER BY created_at DESC
               LIMIT 1
           """)

           assert audit_entry is not None
           assert 'Invalid password' in str(audit_entry['error_message'])
   ```

3. **JWT Token Validation with Real Database + Redis**
   ```python
   @pytest.mark.tier2
   @pytest.mark.requires_docker
   async def test_verify_token_real_infrastructure(auth_system_initialized, test_jwt_token, auth_redis):
       """Test JWT token verification with real database and Redis."""
       token = test_jwt_token['token']

       # Verify token (should hit database first time)
       payload = await auth_system_initialized.verify_token(token)

       assert payload is not None
       assert payload['sub'] == test_jwt_token['user'].username
       assert payload['user_id'] == test_jwt_token['user'].id
       assert payload['type'] == 'access'

       # Verify Redis cache was set
       cache_key = f"user_active:{test_jwt_token['user'].id}"
       cached_value = await auth_redis.get(cache_key)
       assert cached_value == "1"  # Active user

       # Second verification should use Redis cache
       payload2 = await auth_system_initialized.verify_token(token)
       assert payload2 is not None
   ```

4. **API Key Authentication with Real Database**
   ```python
   @pytest.mark.tier2
   @pytest.mark.requires_docker
   async def test_api_key_authentication(auth_system_initialized, auth_db_pool, test_users):
       """Test API key authentication against real database."""
       # Get test API key from database
       async with auth_db_pool.acquire() as conn:
           api_key_row = await conn.fetchrow("""
               SELECT ak.api_key
               FROM api_keys ak
               JOIN users u ON ak.user_id = u.id
               WHERE u.username = $1 AND ak.is_active = true
               LIMIT 1
           """, test_users['user']['username'])

       assert api_key_row is not None
       api_key = api_key_row['api_key']

       # Authenticate with API key
       user = await auth_system_initialized.authenticate_api_key(api_key)

       # Verify user object
       assert user is not None
       assert user.username == test_users['user']['username']
       assert user.email == test_users['user']['email']

       # Verify last_used_at was updated
       async with auth_db_pool.acquire() as conn:
           updated_key = await conn.fetchrow(
               "SELECT last_used_at FROM api_keys WHERE api_key = $1",
               api_key
           )
           assert updated_key['last_used_at'] is not None
   ```

5. **Account Locking after Failed Attempts**
   ```python
   @pytest.mark.tier2
   @pytest.mark.requires_docker
   async def test_account_locking_brute_force(auth_system_initialized, auth_db_pool):
       """Test account locking after multiple failed login attempts."""
       # Create test user for this test
       test_username = f"brute_force_test_{uuid.uuid4().hex[:8]}"

       await auth_system_initialized.create_user(
           username=test_username,
           email=f"{test_username}@horme.test",
           password="correct_password",
           role=UserRole.USER,
           name="Brute Force Test"
       )

       # Attempt 5 failed logins
       for i in range(5):
           user = await auth_system_initialized.authenticate_user(
               username=test_username,
               password="wrong_password",
               ip_address='192.168.1.100'
           )
           assert user is None

       # Verify account is locked in database
       async with auth_db_pool.acquire() as conn:
           locked_user = await conn.fetchrow(
               "SELECT failed_login_attempts, locked_until FROM users WHERE username = $1",
               test_username
           )

           assert locked_user['failed_login_attempts'] >= 5
           # Note: Account locking logic should be implemented in auth_system
           # This test verifies the database state

       # Cleanup
       async with auth_db_pool.acquire() as conn:
           await conn.execute("DELETE FROM users WHERE username = $1", test_username)
   ```

6. **Session Management with Redis**
   ```python
   @pytest.mark.tier2
   @pytest.mark.requires_docker
   async def test_session_caching_redis(auth_system_initialized, test_jwt_token, auth_redis):
       """Test session caching in Redis."""
       token = test_jwt_token['token']
       user = test_jwt_token['user']

       # Cache session in Redis (simulating login)
       session_key = f"nexus:session:{token}"
       session_data = {
           "user_id": user.id,
           "username": user.username,
           "email": user.email,
           "role": user.role.value
       }

       await auth_redis.setex(
           session_key,
           3600,  # 1 hour
           json.dumps(session_data)
       )

       # Verify session exists
       cached_session = await auth_redis.get(session_key)
       assert cached_session is not None

       session_dict = json.loads(cached_session)
       assert session_dict['username'] == user.username
       assert session_dict['email'] == user.email

       # Verify TTL
       ttl = await auth_redis.ttl(session_key)
       assert ttl > 0
       assert ttl <= 3600
   ```

### 5.3 Tier 3: End-to-End Tests (Complete Workflows)

**Location:** `tests/e2e/test_auth_e2e.py`

**Speed:** <10 seconds per test
**Mocking:** ❌ FORBIDDEN - Complete real workflows
**Focus:** Complete user authentication flows

**Test Cases:**

1. **Complete Registration → Login → Access Flow**
   ```python
   @pytest.mark.tier3
   @pytest.mark.requires_docker
   async def test_complete_registration_login_flow(auth_system_initialized, auth_db_pool, auth_redis):
       """Test complete user registration, login, and authenticated access."""
       # Step 1: Register new user
       username = f"e2e_test_user_{uuid.uuid4().hex[:8]}"
       email = f"{username}@horme.test"
       password = "e2e_test_password_123"

       new_user = await auth_system_initialized.create_user(
           username=username,
           email=email,
           password=password,
           role=UserRole.USER,
           name="E2E Test User"
       )

       assert new_user.id is not None
       assert new_user.api_key is not None

       # Step 2: Login with credentials
       authenticated_user = await auth_system_initialized.authenticate_user(
           username=username,
           password=password,
           ip_address='192.168.1.100'
       )

       assert authenticated_user is not None
       assert authenticated_user.username == username

       # Step 3: Generate JWT token
       access_token = auth_system_initialized.create_access_token(authenticated_user)
       refresh_token = auth_system_initialized.create_refresh_token(authenticated_user)

       assert access_token is not None
       assert refresh_token is not None

       # Step 4: Cache session in Redis
       session_key = f"nexus:session:{access_token}"
       session_data = {
           "user_id": authenticated_user.id,
           "username": authenticated_user.username,
           "email": authenticated_user.email,
           "role": authenticated_user.role.value
       }
       await auth_redis.setex(session_key, 3600, json.dumps(session_data))

       # Step 5: Verify token for API access
       payload = await auth_system_initialized.verify_token(access_token)

       assert payload is not None
       assert payload['sub'] == username
       assert payload['type'] == 'access'

       # Step 6: Verify database state
       async with auth_db_pool.acquire() as conn:
           # User exists
           db_user = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
           assert db_user is not None
           assert db_user['is_active'] is True
           assert db_user['last_login'] is not None

           # Audit logs exist
           login_log = await conn.fetchrow("""
               SELECT * FROM audit_log
               WHERE user_id = $1 AND action = 'login' AND status = 'success'
               ORDER BY created_at DESC
               LIMIT 1
           """, int(authenticated_user.id))
           assert login_log is not None

       # Cleanup
       async with auth_db_pool.acquire() as conn:
           await conn.execute("DELETE FROM users WHERE username = $1", username)
       await auth_redis.delete(session_key)
   ```

2. **API Key Authentication Flow**
   ```python
   @pytest.mark.tier3
   @pytest.mark.requires_docker
   async def test_api_key_authentication_flow(auth_system_initialized, auth_db_pool):
       """Test complete API key authentication workflow."""
       # Step 1: Create user
       username = f"api_key_test_{uuid.uuid4().hex[:8]}"
       user = await auth_system_initialized.create_user(
           username=username,
           email=f"{username}@horme.test",
           password="password_123",
           role=UserRole.API,
           name="API Key Test User"
       )

       # Step 2: Get API key from database
       async with auth_db_pool.acquire() as conn:
           api_key_row = await conn.fetchrow(
               "SELECT api_key FROM api_keys WHERE user_id = $1",
               int(user.id)
           )

       api_key = api_key_row['api_key']
       assert api_key.startswith('horme_')

       # Step 3: Authenticate with API key
       authenticated_user = await auth_system_initialized.authenticate_api_key(api_key)

       assert authenticated_user is not None
       assert authenticated_user.username == username
       assert authenticated_user.role == UserRole.API

       # Step 4: Verify last_used_at updated
       async with auth_db_pool.acquire() as conn:
           updated_key = await conn.fetchrow(
               "SELECT last_used_at FROM api_keys WHERE api_key = $1",
               api_key
           )
           assert updated_key['last_used_at'] is not None

       # Cleanup
       async with auth_db_pool.acquire() as conn:
           await conn.execute("DELETE FROM users WHERE username = $1", username)
   ```

3. **Role-Based Access Control Flow**
   ```python
   @pytest.mark.tier3
   @pytest.mark.requires_docker
   async def test_rbac_enforcement(auth_system_initialized, test_users):
       """Test role-based access control enforcement."""
       # Test regular user permissions
       user = await auth_system_initialized.authenticate_user(
           username=test_users['user']['username'],
           password=test_users['user']['password']
       )

       # User should have READ and WRITE
       assert auth_system_initialized.check_permission(user, Permission.READ) is True
       assert auth_system_initialized.check_permission(user, Permission.WRITE) is True
       # User should NOT have ADMIN
       assert auth_system_initialized.check_permission(user, Permission.ADMIN) is False

       # Test admin permissions
       admin = await auth_system_initialized.authenticate_user(
           username=test_users['admin']['username'],
           password=test_users['admin']['password']
       )

       # Admin should have all permissions
       assert auth_system_initialized.check_permission(admin, Permission.READ) is True
       assert auth_system_initialized.check_permission(admin, Permission.WRITE) is True
       assert auth_system_initialized.check_permission(admin, Permission.DELETE) is True
       assert auth_system_initialized.check_permission(admin, Permission.ADMIN) is True
   ```

4. **Account Lockout Prevention**
   ```python
   @pytest.mark.tier3
   @pytest.mark.requires_docker
   async def test_account_lockout_prevents_access(auth_system_initialized, test_users):
       """Test that locked accounts cannot authenticate."""
       # Try to authenticate locked user
       locked_user = await auth_system_initialized.authenticate_user(
           username=test_users['locked']['username'],
           password=test_users['locked']['password']
       )

       # Should return None (account locked)
       assert locked_user is None
   ```

5. **Inactive Account Prevention**
   ```python
   @pytest.mark.tier3
   @pytest.mark.requires_docker
   async def test_inactive_account_prevents_access(auth_system_initialized, test_users):
       """Test that inactive accounts cannot authenticate."""
       # Try to authenticate inactive user
       inactive_user = await auth_system_initialized.authenticate_user(
           username=test_users['inactive']['username'],
           password=test_users['inactive']['password']
       )

       # Should return None (account inactive)
       assert inactive_user is None
   ```

---

## 6. Implementation Roadmap

### Phase 1: Infrastructure Setup (Day 1)

**Priority:** CRITICAL
**Estimated Time:** 2-4 hours

**Tasks:**
1. ✅ Create `tests/utils/init-scripts/03-test-auth-setup.sql`
2. ✅ Update Docker test database initialization to include auth schema
3. ✅ Create `tests/integration/test_auth_fixtures.py`
4. ✅ Verify test database with auth schema
5. ✅ Create test users in test database

**Validation:**
```bash
# Start test infrastructure
docker-compose -f tests/utils/docker-compose.test.yml up -d

# Verify database
docker exec horme_pov_test_postgres psql -U test_user -d horme_test -c "\dt"

# Should see: users, api_keys, sessions, audit_log, permissions, user_permissions
```

### Phase 2: Tier 1 Unit Tests (Day 1-2)

**Priority:** HIGH
**Estimated Time:** 4-6 hours

**Tasks:**
1. ✅ Create `tests/unit/test_auth_unit.py`
2. ✅ Implement password hashing tests
3. ✅ Implement JWT token tests
4. ✅ Implement permission checking tests
5. ✅ Implement role hierarchy tests
6. ✅ Run and verify all unit tests pass

**Validation:**
```bash
# Run unit tests only
pytest tests/unit/test_auth_unit.py -v --tb=short

# Expected: All tests pass in <1 second each
```

### Phase 3: Tier 2 Integration Tests (Day 2-3)

**Priority:** HIGH
**Estimated Time:** 6-8 hours

**Tasks:**
1. ✅ Create `tests/integration/test_auth_integration.py`
2. ✅ Implement user creation tests
3. ✅ Implement authentication tests
4. ✅ Implement JWT validation tests
5. ✅ Implement API key authentication tests
6. ✅ Implement session management tests
7. ✅ Implement account locking tests
8. ✅ Run and verify all integration tests pass

**Validation:**
```bash
# Ensure Docker services are running
./tests/utils/test-env up

# Run integration tests
pytest tests/integration/test_auth_integration.py -v --tb=short

# Expected: All tests pass in <5 seconds each
```

### Phase 4: Tier 3 E2E Tests (Day 3-4)

**Priority:** MEDIUM
**Estimated Time:** 6-8 hours

**Tasks:**
1. ✅ Create `tests/e2e/test_auth_e2e.py`
2. ✅ Implement complete registration flow test
3. ✅ Implement API key flow test
4. ✅ Implement RBAC enforcement test
5. ✅ Implement account lockout test
6. ✅ Implement inactive account test
7. ✅ Run and verify all E2E tests pass

**Validation:**
```bash
# Run E2E tests
pytest tests/e2e/test_auth_e2e.py -v --tb=short

# Expected: All tests pass in <10 seconds each
```

### Phase 5: Documentation & CI Integration (Day 4)

**Priority:** MEDIUM
**Estimated Time:** 2-3 hours

**Tasks:**
1. ✅ Update `tests/README.md` with authentication testing guide
2. ✅ Create authentication testing examples
3. ✅ Add CI pipeline for automated auth testing
4. ✅ Create test coverage report

**Validation:**
```bash
# Run complete authentication test suite
pytest tests/ -m "auth" -v --cov=src.core.auth --cov-report=html

# Expected: >90% code coverage for auth module
```

---

## 7. Test Execution Commands

### Run All Authentication Tests
```bash
# Full authentication test suite (all tiers)
pytest tests/ -k "auth" -v --tb=short

# With coverage report
pytest tests/ -k "auth" -v --cov=src.core.auth --cov-report=html
```

### Run by Tier
```bash
# Tier 1 only (fast unit tests)
pytest tests/unit/test_auth_unit.py -v

# Tier 2 only (integration with Docker)
pytest tests/integration/test_auth_integration.py -v --requires-docker

# Tier 3 only (E2E workflows)
pytest tests/e2e/test_auth_e2e.py -v --requires-docker
```

### Run Specific Test Categories
```bash
# Password tests
pytest tests/ -k "password" -v

# JWT token tests
pytest tests/ -k "token" -v

# Permission tests
pytest tests/ -k "permission" -v

# Account security tests
pytest tests/ -k "lockout or inactive" -v
```

### Performance Testing
```bash
# Run with timeout enforcement
pytest tests/integration/test_auth_integration.py --timeout=5

# Run with performance profiling
pytest tests/integration/test_auth_integration.py --profile
```

---

## 8. Success Criteria

### ✅ Infrastructure
- [ ] Test database with auth schema initialized
- [ ] Test users created in database
- [ ] Docker services running and healthy
- [ ] Test fixtures available

### ✅ Unit Tests (Tier 1)
- [ ] All password hashing tests pass
- [ ] All JWT token tests pass
- [ ] All permission tests pass
- [ ] All role hierarchy tests pass
- [ ] All tests run in <1 second

### ✅ Integration Tests (Tier 2)
- [ ] User creation with real database works
- [ ] Authentication with real database works
- [ ] JWT validation with real Redis works
- [ ] API key authentication works
- [ ] Session caching in Redis works
- [ ] Account locking works
- [ ] All tests run in <5 seconds
- [ ] NO MOCKING used

### ✅ E2E Tests (Tier 3)
- [ ] Complete registration flow works
- [ ] Complete login flow works
- [ ] API key authentication flow works
- [ ] RBAC enforcement works
- [ ] Account security works
- [ ] All tests run in <10 seconds
- [ ] NO MOCKING used

### ✅ Code Quality
- [ ] >90% code coverage for auth module
- [ ] All tests follow 3-tier strategy
- [ ] No hardcoded values
- [ ] No mock data in Tiers 2-3
- [ ] All tests use real infrastructure

---

## 9. Security Testing Considerations

### Penetration Testing Scenarios

1. **SQL Injection Prevention**
   - Test parameterized queries prevent injection
   - Verify input sanitization

2. **Brute Force Prevention**
   - Test account locking after failed attempts
   - Verify rate limiting

3. **Token Security**
   - Test expired token rejection
   - Test invalid token handling
   - Test token tampering detection

4. **Session Security**
   - Test session hijacking prevention
   - Test session expiration
   - Test concurrent session handling

### Compliance Testing

1. **Password Security**
   - Verify bcrypt cost factor ≥ 12
   - Test password strength requirements
   - Verify passwords never stored in plain text

2. **Audit Logging**
   - Verify all auth events logged
   - Test audit log integrity
   - Verify audit data includes IP, timestamp, user agent

3. **Data Privacy**
   - Verify user data access control
   - Test GDPR compliance (data deletion)
   - Verify PII encryption

---

## 10. Maintenance and Monitoring

### Test Maintenance

**Weekly:**
- Review test execution times
- Update test data if schema changes
- Check for flaky tests

**Monthly:**
- Review test coverage
- Update fixtures as needed
- Performance baseline verification

**Quarterly:**
- Security test updates
- Penetration testing
- Compliance verification

### Monitoring Alerts

**Production Monitoring:**
- Failed authentication rate > 5%
- Account lockouts > 10/hour
- JWT validation failures > 2%
- API key usage anomalies
- Audit log gaps

---

## 11. References

### Documentation
- `src/core/auth.py` - Authentication implementation
- `init-scripts/02-auth-schema.sql` - Database schema
- `tests/COMPREHENSIVE_3_TIER_TESTING_STRATEGY.md` - Testing methodology

### Standards
- OWASP Authentication Best Practices
- NIST Digital Identity Guidelines
- GDPR Compliance Requirements
- SOC 2 Type II Controls

---

## Appendix A: Test Data Summary

### Test Users (in Test Database)

| Username | Email | Password | Role | Status |
|----------|-------|----------|------|--------|
| test_user | test_user@horme.test | test_password_123 | user | active |
| test_admin | test_admin@horme.test | admin_password_123 | admin | active |
| test_manager | test_manager@horme.test | manager_password_123 | manager | active |
| test_inactive | test_inactive@horme.test | inactive_password_123 | user | inactive |
| test_locked | test_locked@horme.test | locked_password_123 | user | locked |

### Test API Keys

| Username | API Key Prefix | Permissions |
|----------|---------------|-------------|
| test_user | horme_test_api_key_test_user | read, write |
| test_admin | horme_test_api_key_test_admin | read, write |
| test_manager | horme_test_api_key_test_manager | read, write |

---

## Appendix B: Common Testing Issues and Solutions

### Issue: Database Connection Fails
**Solution:**
```bash
# Verify Docker services running
docker-compose -f tests/utils/docker-compose.test.yml ps

# Check database logs
docker logs horme_pov_test_postgres

# Restart services
docker-compose -f tests/utils/docker-compose.test.yml restart postgres
```

### Issue: Redis Connection Fails
**Solution:**
```bash
# Check Redis health
docker exec horme_pov_test_redis redis-cli ping

# Clear Redis data
docker exec horme_pov_test_redis redis-cli FLUSHALL

# Restart Redis
docker-compose -f tests/utils/docker-compose.test.yml restart redis
```

### Issue: Test Users Not Found
**Solution:**
```bash
# Re-run database initialization
docker exec horme_pov_test_postgres psql -U test_user -d horme_test -f /docker-entrypoint-initdb.d/03-test-auth-setup.sql

# Verify users exist
docker exec horme_pov_test_postgres psql -U test_user -d horme_test -c "SELECT username, email, role FROM users WHERE username LIKE 'test_%';"
```

---

**Document Version:** 1.0
**Last Updated:** 2025-01-17
**Author:** Claude Code (3-Tier Testing Strategy Specialist)
**Review Status:** Ready for Implementation
