"""
Pytest configuration for Docker-based test infrastructure.

This conftest.py provides shared fixtures for all test tiers (unit, integration, e2e).
All integration and e2e tests MUST use Docker services - NO local execution allowed.

Service URLs when running in Docker test-runner container:
- PostgreSQL: postgres:5432 (internal) or localhost:5434 (external)
- Redis: redis:6379 (internal) or localhost:6380 (external)
- Neo4j: neo4j:7687 (internal) or localhost:7687 (external)
- Ollama: ollama:11434 (internal) or localhost:11435 (external)
- MySQL: mysql:3306 (internal) or localhost:3307 (external)
- MongoDB: mongodb:27017 (internal)
- MinIO: minio:9000 (internal) or localhost:9001 (external)
"""

import os
import sys
import time
from pathlib import Path

import pytest

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Environment Configuration Fixtures
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def configure_docker_environment():
    """
    Configure environment variables for Docker-based testing.
    This fixture runs automatically for all test sessions.
    """
    # Check if running inside Docker container
    in_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'

    # Set default environment variables for Docker services
    docker_defaults = {
        # PostgreSQL configuration
        'POSTGRES_HOST': 'postgres' if in_docker else 'localhost',
        'POSTGRES_PORT': '5432' if in_docker else '5434',
        'POSTGRES_DB': 'horme_test',
        'POSTGRES_USER': 'test_user',
        'POSTGRES_PASSWORD': 'test_password',
        'DB_HOST': 'postgres' if in_docker else 'localhost',
        'DB_PORT': '5432' if in_docker else '5434',
        'DB_NAME': 'horme_test',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',

        # Redis configuration
        'REDIS_HOST': 'redis' if in_docker else 'localhost',
        'REDIS_PORT': '6379' if in_docker else '6380',
        'REDIS_URL': f"redis://{'redis' if in_docker else 'localhost'}:{'6379' if in_docker else '6380'}",

        # Neo4j configuration
        'NEO4J_URI': f"bolt://{'neo4j' if in_docker else 'localhost'}:{'7687' if in_docker else '7687'}",
        'NEO4J_USER': 'neo4j',
        'NEO4J_PASSWORD': 'test_password',

        # Ollama configuration
        'OLLAMA_HOST': 'ollama' if in_docker else 'localhost',
        'OLLAMA_PORT': '11434' if in_docker else '11435',
        'OLLAMA_BASE_URL': f"http://{'ollama' if in_docker else 'localhost'}:{'11434' if in_docker else '11435'}",

        # MySQL configuration
        'MYSQL_HOST': 'mysql' if in_docker else 'localhost',
        'MYSQL_PORT': '3306' if in_docker else '3307',
        'MYSQL_DATABASE': 'horme_test',
        'MYSQL_USER': 'horme_test',
        'MYSQL_PASSWORD': 'test_password',

        # MongoDB configuration
        'MONGODB_HOST': 'mongodb' if in_docker else 'localhost',
        'MONGODB_PORT': '27017',
        'MONGODB_DATABASE': 'horme_test',

        # MinIO configuration
        'MINIO_HOST': 'minio' if in_docker else 'localhost',
        'MINIO_PORT': '9000' if in_docker else '9001',
        'MINIO_ACCESS_KEY': 'testuser',
        'MINIO_SECRET_KEY': 'testpass123',

        # API configuration
        'API_URL': 'http://localhost:8000',
        'WEBSOCKET_URL': 'ws://localhost/ws',

        # Test environment flags
        'TEST_DOCKER_AVAILABLE': 'true',
        'TESTING': 'true',
        'ENVIRONMENT': 'test',
    }

    # Only set if not already set (allows override via docker-compose environment)
    for key, value in docker_defaults.items():
        if key not in os.environ:
            os.environ[key] = value

    yield

    # Cleanup after all tests complete
    pass


@pytest.fixture(scope="session")
def docker_services_available():
    """
    Verify that Docker services are available and healthy.
    This should be used as a dependency for integration/e2e tests.
    """
    import socket
    import redis

    # Check if running in Docker
    in_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'

    # Service health checks
    services_healthy = {
        'postgres': False,
        'redis': False,
    }

    # Check PostgreSQL
    try:
        import psycopg2
        host = os.environ.get('POSTGRES_HOST', 'localhost')
        port = os.environ.get('POSTGRES_PORT', '5434')
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=os.environ.get('POSTGRES_DB', 'horme_test'),
            user=os.environ.get('POSTGRES_USER', 'test_user'),
            password=os.environ.get('POSTGRES_PASSWORD', 'test_password'),
            connect_timeout=10
        )
        conn.close()
        services_healthy['postgres'] = True
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")

    # Check Redis
    try:
        redis_client = redis.from_url(os.environ.get('REDIS_URL'))
        redis_client.ping()
        redis_client.close()
        services_healthy['redis'] = True
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")

    return services_healthy


# ============================================================================
# Database Connection Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def postgres_connection():
    """
    Provide a PostgreSQL connection for testing.
    Automatically rolls back changes after each test.
    """
    import psycopg2

    host = os.environ.get('POSTGRES_HOST', 'localhost')
    port = os.environ.get('POSTGRES_PORT', '5434')

    conn = psycopg2.connect(
        host=host,
        port=port,
        database=os.environ.get('POSTGRES_DB', 'horme_test'),
        user=os.environ.get('POSTGRES_USER', 'test_user'),
        password=os.environ.get('POSTGRES_PASSWORD', 'test_password')
    )
    conn.autocommit = False

    yield conn

    # Rollback any changes made during the test
    conn.rollback()
    conn.close()


@pytest.fixture(scope="function")
def redis_client():
    """
    Provide a Redis client for testing.
    Automatically flushes test data after each test.
    """
    import redis

    client = redis.from_url(
        os.environ.get('REDIS_URL'),
        decode_responses=True
    )

    yield client

    # Cleanup test keys (only delete keys with 'test:' prefix)
    test_keys = client.keys('test:*')
    if test_keys:
        client.delete(*test_keys)

    client.close()


@pytest.fixture(scope="function")
def neo4j_connection():
    """
    Provide a Neo4j connection for testing.
    """
    from neo4j import GraphDatabase

    uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    user = os.environ.get('NEO4J_USER', 'neo4j')
    password = os.environ.get('NEO4J_PASSWORD', 'test_password')

    driver = GraphDatabase.driver(uri, auth=(user, password))

    yield driver

    # Cleanup test data
    with driver.session() as session:
        session.run("MATCH (n:TestNode) DETACH DELETE n")

    driver.close()


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def sample_product_data():
    """Provide sample product data for testing."""
    return {
        'id': 99999,
        'sku': 'TEST-DRILL-001',
        'name': 'Test Cordless Drill 18V',
        'description': 'Professional grade cordless drill for testing',
        'category': 'Power Tools',
        'brand': 'Test Brand',
        'price': 99.99,
        'keywords': ['drill', 'power tool', 'cordless', 'test']
    }


@pytest.fixture(scope="function")
def sample_batch_products():
    """Provide sample batch of products for testing."""
    return [
        {
            'id': i,
            'sku': f'TEST-{i:03d}',
            'name': f'Test Product {i}',
            'description': f'Test product description {i}',
            'category': 'Test Category',
            'price': 10.0 * i
        }
        for i in range(1, 11)
    ]


# ============================================================================
# Pytest Markers and Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "tier1: Unit tests (fast, mocks allowed, no Docker required)"
    )
    config.addinivalue_line(
        "markers", "tier2: Integration tests (real Docker services, NO MOCKING)"
    )
    config.addinivalue_line(
        "markers", "tier3: E2E tests (complete workflows, real infrastructure)"
    )
    config.addinivalue_line(
        "markers", "requires_docker: Test requires Docker services to be running"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer than average"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark tests based on directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.tier1)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.tier2)
            item.add_marker(pytest.mark.requires_docker)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.tier3)
            item.add_marker(pytest.mark.requires_docker)
            item.add_marker(pytest.mark.slow)


# ============================================================================
# Helper Functions
# ============================================================================

def wait_for_service(host, port, timeout=30):
    """Wait for a service to become available."""
    import socket

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, int(port)))
            sock.close()
            if result == 0:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def is_service_healthy(service_name):
    """Check if a Docker service is healthy."""
    import subprocess

    try:
        result = subprocess.run(
            ['docker', 'inspect', '-f', '{{.State.Health.Status}}', f'horme_pov_test_{service_name}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() == 'healthy'
    except Exception:
        return False
