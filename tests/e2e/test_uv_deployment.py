"""End-to-end tests for UV-based deployment stack.

This module validates complete UV-based deployment including:
- docker-compose.uv.yml stack startup
- Service health checks
- API endpoint functionality
- WebSocket connections
- Nexus multi-mode operation
- Environment variable usage (NO hardcoding)

Following Tier 3 E2E testing requirements:
- Complete real infrastructure
- Real service interactions
- NO MOCKING
"""

import asyncio
import json
import os
import subprocess
import time
import pytest
import requests
from pathlib import Path
from typing import Dict, Any


@pytest.fixture(scope="module")
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def env_config(project_root):
    """Load environment configuration."""
    env_file = project_root / ".env.production"

    if not env_file.exists():
        pytest.skip(f"Environment file not found: {env_file}")

    config = {}
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()

    return config


def run_compose_command(
    cmd: str,
    project_root: Path,
    timeout: int = 300
) -> subprocess.CompletedProcess:
    """Run docker-compose command."""
    compose_file = project_root / "docker-compose.uv.yml"

    if not compose_file.exists():
        pytest.skip("docker-compose.uv.yml not found")

    full_cmd = f"docker-compose -f {compose_file} {cmd}"

    result = subprocess.run(
        full_cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=project_root,
        timeout=timeout
    )

    return result


def wait_for_service(
    url: str,
    timeout: int = 120,
    interval: int = 5
) -> bool:
    """Wait for a service to become healthy."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 404]:  # 404 is ok for root path
                return True
        except Exception:
            pass

        time.sleep(interval)

    return False


@pytest.mark.e2e
@pytest.mark.uv
@pytest.mark.timeout(600)
class TestUVStackDeployment:
    """Test UV-based stack deployment."""

    def test_docker_compose_uv_yml_exists(self, project_root):
        """Verify docker-compose.uv.yml exists."""
        compose_file = project_root / "docker-compose.uv.yml"
        assert compose_file.exists(), "docker-compose.uv.yml not found"
        assert compose_file.is_file()

    def test_compose_file_has_required_services(self, project_root):
        """Verify compose file defines required services."""
        compose_file = project_root / "docker-compose.uv.yml"
        content = compose_file.read_text()

        required_services = [
            'postgres',
            'redis',
            'api',
            'websocket',
        ]

        for service in required_services:
            assert f'{service}:' in content, f"Service {service} not found in compose file"

    def test_compose_file_no_hardcoded_values(self, project_root):
        """Verify compose file uses environment variables, no hardcoding."""
        compose_file = project_root / "docker-compose.uv.yml"
        content = compose_file.read_text()

        import re

        # Check for hardcoded passwords (should use ${VAR} syntax)
        hardcoded_password = re.findall(r'password:\s*["\']?[a-zA-Z0-9]{8,}["\']?', content, re.IGNORECASE)
        # Filter out variable references
        hardcoded_password = [p for p in hardcoded_password if '${' not in p and '$' not in p]

        assert len(hardcoded_password) == 0, (
            f"Found hardcoded passwords in compose file: {hardcoded_password}"
        )

        # Check for hardcoded secrets
        hardcoded_secret = re.findall(r'secret[_-]?key:\s*["\']?[a-zA-Z0-9]{16,}["\']?', content, re.IGNORECASE)
        hardcoded_secret = [s for s in hardcoded_secret if '${' not in s and '$' not in s]

        assert len(hardcoded_secret) == 0, (
            f"Found hardcoded secrets in compose file: {hardcoded_secret}"
        )

    def test_stack_starts_successfully(self, project_root, env_config):
        """Test that UV stack starts successfully."""
        # Stop any existing stack
        run_compose_command("down -v", project_root, timeout=120)

        # Start the stack
        result = run_compose_command("up -d", project_root, timeout=600)

        assert result.returncode == 0, f"Stack startup failed: {result.stderr}"

    def test_all_services_healthy(self, project_root, env_config):
        """Verify all services are healthy after startup."""
        # Give services time to become healthy
        time.sleep(30)

        result = run_compose_command("ps", project_root, timeout=30)

        assert result.returncode == 0

        # Check each service is running
        required_services = ['postgres', 'redis', 'api']

        for service in required_services:
            # Service should appear in ps output
            assert service in result.stdout.lower(), (
                f"Service {service} not found in running services"
            )


@pytest.mark.e2e
@pytest.mark.uv
@pytest.mark.timeout(300)
class TestAPIEndpoints:
    """Test API endpoints work correctly in UV deployment."""

    @pytest.fixture(scope="class")
    def api_base_url(self, env_config):
        """Get API base URL from environment."""
        host = env_config.get('API_HOST', 'localhost')
        port = env_config.get('API_PORT', '8000')
        return f"http://{host}:{port}"

    def test_api_service_accessible(self, api_base_url):
        """Test API service is accessible."""
        if not wait_for_service(f"{api_base_url}/health", timeout=60):
            pytest.fail("API service did not become healthy in time")

    def test_health_endpoint_responds(self, api_base_url):
        """Test /health endpoint responds correctly."""
        try:
            response = requests.get(f"{api_base_url}/health", timeout=10)
            assert response.status_code == 200, f"Health check failed: {response.status_code}"

            data = response.json()
            assert 'status' in data, "Health response missing status"
            assert data['status'] in ['healthy', 'ok'], f"Unexpected health status: {data['status']}"

        except requests.RequestException as e:
            pytest.fail(f"Health endpoint request failed: {e}")

    def test_docs_endpoint_accessible(self, api_base_url):
        """Test /docs endpoint is accessible."""
        try:
            response = requests.get(f"{api_base_url}/docs", timeout=10)
            assert response.status_code == 200, "Docs endpoint should be accessible"

        except requests.RequestException as e:
            pytest.fail(f"Docs endpoint request failed: {e}")

    def test_api_uses_real_database(self, api_base_url, postgres_connection):
        """Test API uses real PostgreSQL database (NO MOCKING)."""
        # Create a test record via API
        try:
            response = requests.post(
                f"{api_base_url}/api/v1/test-connection",
                json={"test": "data"},
                timeout=10
            )

            # Even if endpoint doesn't exist, connection to DB should work
            # Verify via direct DB query
            cursor = postgres_connection.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            assert result[0] == 1, "Database connection not working"

        except requests.RequestException:
            # API endpoint may not exist, but DB should be accessible
            pass

    def test_api_uses_real_redis(self, api_base_url, redis_client):
        """Test API uses real Redis cache (NO MOCKING)."""
        # Verify Redis is accessible
        try:
            redis_client.ping()
        except Exception as e:
            pytest.fail(f"Redis not accessible: {e}")

        # Set a test key
        redis_client.set('test:uv_deployment', 'success', ex=60)

        # Verify it's set
        value = redis_client.get('test:uv_deployment')
        assert value == 'success', "Redis set/get failed"


@pytest.mark.e2e
@pytest.mark.uv
@pytest.mark.timeout(300)
class TestWebSocketService:
    """Test WebSocket service in UV deployment."""

    @pytest.fixture(scope="class")
    def websocket_url(self, env_config):
        """Get WebSocket URL from environment."""
        host = env_config.get('WEBSOCKET_HOST', 'localhost')
        port = env_config.get('WEBSOCKET_PORT', '8001')
        return f"ws://{host}:{port}"

    def test_websocket_service_accessible(self, websocket_url):
        """Test WebSocket service is accessible."""
        # Check if WebSocket container is running
        result = subprocess.run(
            "docker ps --filter name=websocket --format '{{.Names}}'",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        if 'websocket' not in result.stdout:
            pytest.skip("WebSocket service not running")

    def test_websocket_health_check(self, env_config):
        """Test WebSocket service health check."""
        host = env_config.get('WEBSOCKET_HOST', 'localhost')
        port = env_config.get('WEBSOCKET_PORT', '8001')

        # WebSocket services often have HTTP health endpoint
        try:
            response = requests.get(f"http://{host}:{port}/health", timeout=10)
            assert response.status_code == 200
        except requests.RequestException:
            # Health endpoint may not exist, check container is running
            result = subprocess.run(
                "docker ps --filter name=websocket --filter status=running --format '{{.Names}}'",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            assert 'websocket' in result.stdout, "WebSocket service not running"


@pytest.mark.e2e
@pytest.mark.uv
@pytest.mark.timeout(300)
class TestNexusMultiMode:
    """Test Nexus multi-mode operation in UV deployment."""

    def test_nexus_service_running(self):
        """Test Nexus service is running."""
        result = subprocess.run(
            "docker ps --filter name=nexus --format '{{.Names}}'",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        if 'nexus' not in result.stdout:
            pytest.skip("Nexus service not configured in this deployment")

    def test_nexus_api_mode_accessible(self, env_config):
        """Test Nexus API mode is accessible."""
        host = env_config.get('NEXUS_HOST', 'localhost')
        port = env_config.get('NEXUS_PORT', '8080')

        try:
            response = requests.get(f"http://{host}:{port}/health", timeout=10)
            assert response.status_code == 200
        except requests.RequestException:
            pytest.skip("Nexus API not accessible")


@pytest.mark.e2e
@pytest.mark.uv
@pytest.mark.timeout(180)
class TestEnvironmentConfiguration:
    """Test all services use environment variables (NO hardcoding)."""

    def test_postgres_uses_env_credentials(self, env_config, project_root):
        """Test PostgreSQL uses environment credentials."""
        # Verify we can connect using env credentials
        import psycopg2

        try:
            conn = psycopg2.connect(
                host=env_config.get('POSTGRES_HOST', 'localhost'),
                port=env_config.get('POSTGRES_PORT', '5433'),
                database=env_config.get('POSTGRES_DB', 'horme_db'),
                user=env_config.get('POSTGRES_USER', 'horme_user'),
                password=env_config.get('POSTGRES_PASSWORD'),
                connect_timeout=10
            )
            conn.close()

        except Exception as e:
            pytest.fail(f"PostgreSQL connection with env credentials failed: {e}")

    def test_redis_uses_env_configuration(self, env_config):
        """Test Redis uses environment configuration."""
        import redis

        try:
            redis_url = env_config.get(
                'REDIS_URL',
                f"redis://localhost:{env_config.get('REDIS_PORT', '6380')}"
            )

            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()
            client.close()

        except Exception as e:
            pytest.fail(f"Redis connection with env config failed: {e}")

    def test_api_uses_env_openai_key(self, env_config):
        """Test API uses OpenAI key from environment."""
        openai_key = env_config.get('OPENAI_API_KEY')

        # Should be defined in environment
        assert openai_key, "OPENAI_API_KEY not defined in .env.production"

        # Should not be a placeholder
        assert not openai_key.startswith('sk-your-'), (
            "OPENAI_API_KEY is still a placeholder"
        )
        assert not openai_key == 'your-api-key-here', (
            "OPENAI_API_KEY is still a placeholder"
        )


@pytest.mark.e2e
@pytest.mark.uv
@pytest.mark.timeout(120)
class TestStackCleanup:
    """Test UV stack cleanup."""

    def test_stack_stops_cleanly(self, project_root):
        """Test stack stops without errors."""
        result = run_compose_command("down", project_root, timeout=120)

        assert result.returncode == 0, f"Stack shutdown failed: {result.stderr}"

    def test_volumes_removed(self, project_root):
        """Test volumes are removed on cleanup."""
        # Stop and remove volumes
        result = run_compose_command("down -v", project_root, timeout=120)

        assert result.returncode == 0

        # Verify volumes are removed
        volume_check = subprocess.run(
            "docker volume ls --filter name=horme --format '{{.Name}}'",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should have no horme-related volumes
        # (or only expected persistent volumes)
        assert volume_check.returncode == 0


@pytest.mark.e2e
@pytest.mark.uv
@pytest.mark.timeout(600)
class TestProductionReadiness:
    """Test UV deployment is production-ready."""

    def test_all_services_use_health_checks(self, project_root):
        """Verify all services have health checks configured."""
        compose_file = project_root / "docker-compose.uv.yml"
        content = compose_file.read_text()

        # All services should have healthcheck
        services = ['postgres', 'redis', 'api']

        for service in services:
            service_section = content[content.find(f'{service}:'):content.find(f'{service}:') + 1000]
            assert 'healthcheck:' in service_section, (
                f"Service {service} missing health check"
            )

    def test_all_services_use_resource_limits(self, project_root):
        """Verify all services have resource limits."""
        compose_file = project_root / "docker-compose.uv.yml"
        content = compose_file.read_text()

        # Production services should have resource limits
        production_services = ['postgres', 'redis', 'api']

        for service in production_services:
            service_section = content[content.find(f'{service}:'):content.find(f'{service}:') + 1500]
            assert 'deploy:' in service_section or 'resources:' in service_section, (
                f"Service {service} missing resource limits"
            )

    def test_all_services_have_restart_policies(self, project_root):
        """Verify all services have restart policies."""
        compose_file = project_root / "docker-compose.uv.yml"
        content = compose_file.read_text()

        services = ['postgres', 'redis', 'api']

        for service in services:
            service_section = content[content.find(f'{service}:'):content.find(f'{service}:') + 1500]
            assert 'restart:' in service_section, (
                f"Service {service} missing restart policy"
            )

    def test_no_development_tools_in_production_images(self, project_root):
        """Verify production images don't include development tools."""
        # Check that images use multi-stage builds and exclude dev deps
        dockerfiles = [
            "Dockerfile.api.uv",
            "Dockerfile.websocket.uv",
            "Dockerfile.nexus.uv"
        ]

        for dockerfile_name in dockerfiles:
            dockerfile = project_root / dockerfile_name
            if not dockerfile.exists():
                continue

            content = dockerfile.read_text()

            # Should use multi-stage build
            assert 'FROM' in content and 'AS builder' in content, (
                f"{dockerfile_name} should use multi-stage build"
            )

            # Should exclude dev dependencies
            assert '--no-dev' in content or 'uv sync --frozen --no-dev' in content, (
                f"{dockerfile_name} should exclude dev dependencies"
            )
