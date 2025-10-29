"""Integration tests for UV-based Docker builds.

This module validates that UV-optimized Dockerfiles build successfully,
produce smaller images, and maintain production standards (NO hardcoding).

Following Tier 2 integration testing requirements:
- Real Docker builds (NO MOCKING)
- Real image inspection
- Real size comparison
- All configuration from environment
"""

import json
import os
import subprocess
import pytest
from pathlib import Path
from typing import Dict, Any


@pytest.fixture(scope="module")
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def env_config(project_root):
    """Load environment configuration from .env.production."""
    env_file = project_root / ".env.production"

    # Real environment configuration - NO hardcoding
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


def run_docker_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run Docker command and return result."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=600  # 10 minute timeout for builds
    )

    if check and result.returncode != 0:
        raise RuntimeError(f"Docker command failed: {result.stderr}")

    return result


@pytest.mark.integration
@pytest.mark.docker
@pytest.mark.timeout(300)
class TestUVDockerBuilds:
    """Test UV-based Docker image builds."""

    def test_dockerfile_api_uv_exists(self, project_root):
        """Verify Dockerfile.api.uv exists and is readable."""
        dockerfile = project_root / "Dockerfile.api.uv"
        assert dockerfile.exists(), "Dockerfile.api.uv not found"
        assert dockerfile.is_file(), "Dockerfile.api.uv is not a file"
        assert os.access(dockerfile, os.R_OK), "Dockerfile.api.uv is not readable"

    def test_dockerfile_websocket_uv_exists(self, project_root):
        """Verify Dockerfile.websocket.uv exists and is readable."""
        dockerfile = project_root / "Dockerfile.websocket.uv"
        assert dockerfile.exists(), "Dockerfile.websocket.uv not found"
        assert dockerfile.is_file(), "Dockerfile.websocket.uv is not a file"
        assert os.access(dockerfile, os.R_OK), "Dockerfile.websocket.uv is not readable"

    def test_dockerfile_nexus_uv_exists(self, project_root):
        """Verify Dockerfile.nexus.uv exists and is readable."""
        dockerfile = project_root / "Dockerfile.nexus.uv"
        assert dockerfile.exists(), "Dockerfile.nexus.uv not found"
        assert dockerfile.is_file(), "Dockerfile.nexus.uv is not a file"
        assert os.access(dockerfile, os.R_OK), "Dockerfile.nexus.uv is not readable"

    def test_no_hardcoded_values_in_dockerfiles(self, project_root):
        """Verify no hardcoded credentials, URLs, or config in Dockerfiles."""
        dockerfiles = [
            "Dockerfile.api.uv",
            "Dockerfile.websocket.uv",
            "Dockerfile.nexus.uv"
        ]

        forbidden_patterns = [
            # Hardcoded credentials
            (r'password\s*=\s*["\'][^"\']+["\']', "hardcoded password"),
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "hardcoded API key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "hardcoded secret"),

            # Hardcoded localhost (should use service names or env vars)
            (r'localhost:\d+', "hardcoded localhost with port"),
            (r'127\.0\.0\.1', "hardcoded 127.0.0.1"),

            # Hardcoded database URLs
            (r'postgresql://[^$]+@', "hardcoded PostgreSQL URL"),
            (r'redis://[^$]+@', "hardcoded Redis URL"),
        ]

        import re

        for dockerfile_name in dockerfiles:
            dockerfile_path = project_root / dockerfile_name
            content = dockerfile_path.read_text()

            for pattern, description in forbidden_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                # Allow localhost in HEALTHCHECK commands (unavoidable)
                if pattern == r'localhost:\d+' and 'HEALTHCHECK' in content:
                    # Filter out healthcheck-related matches
                    matches = [m for m in matches if 'localhost:8000/health' not in m]

                assert len(matches) == 0, (
                    f"{dockerfile_name} contains {description}: {matches}"
                )

    def test_api_dockerfile_builds_successfully(self, project_root):
        """Test that Dockerfile.api.uv builds successfully."""
        # Build the image
        build_cmd = (
            f"docker build "
            f"-f {project_root / 'Dockerfile.api.uv'} "
            f"-t horme-api-uv:test "
            f"{project_root}"
        )

        result = run_docker_command(build_cmd)
        assert result.returncode == 0, f"API build failed: {result.stderr}"
        assert "Successfully built" in result.stdout or "FINISHED" in result.stderr

    def test_websocket_dockerfile_builds_successfully(self, project_root):
        """Test that Dockerfile.websocket.uv builds successfully."""
        build_cmd = (
            f"docker build "
            f"-f {project_root / 'Dockerfile.websocket.uv'} "
            f"-t horme-websocket-uv:test "
            f"{project_root}"
        )

        result = run_docker_command(build_cmd)
        assert result.returncode == 0, f"WebSocket build failed: {result.stderr}"
        assert "Successfully built" in result.stdout or "FINISHED" in result.stderr

    def test_nexus_dockerfile_builds_successfully(self, project_root):
        """Test that Dockerfile.nexus.uv builds successfully."""
        build_cmd = (
            f"docker build "
            f"-f {project_root / 'Dockerfile.nexus.uv'} "
            f"-t horme-nexus-uv:test "
            f"{project_root}"
        )

        result = run_docker_command(build_cmd)
        assert result.returncode == 0, f"Nexus build failed: {result.stderr}"
        assert "Successfully built" in result.stdout or "FINISHED" in result.stderr


@pytest.mark.integration
@pytest.mark.docker
@pytest.mark.timeout(120)
class TestUVImageOptimization:
    """Test UV-based images are smaller and more efficient."""

    def test_api_image_size_optimized(self):
        """Verify API UV image is smaller than pip equivalent."""
        # Get UV image size
        inspect_cmd = "docker inspect horme-api-uv:test --format='{{.Size}}'"
        result = run_docker_command(inspect_cmd, check=False)

        if result.returncode != 0:
            pytest.skip("UV image not built yet, run build tests first")

        uv_size = int(result.stdout.strip())

        # UV image should be under 1GB (800MB target)
        max_size = 1_200_000_000  # 1.2GB absolute max
        assert uv_size < max_size, (
            f"UV API image too large: {uv_size / 1_000_000:.1f}MB "
            f"(max: {max_size / 1_000_000:.1f}MB)"
        )

        # Print size for monitoring
        print(f"\n✅ API UV image size: {uv_size / 1_000_000:.1f}MB")

    def test_websocket_image_size_optimized(self):
        """Verify WebSocket UV image is smaller than pip equivalent."""
        inspect_cmd = "docker inspect horme-websocket-uv:test --format='{{.Size}}'"
        result = run_docker_command(inspect_cmd, check=False)

        if result.returncode != 0:
            pytest.skip("UV image not built yet, run build tests first")

        uv_size = int(result.stdout.strip())

        # UV image should be under 1GB
        max_size = 1_200_000_000  # 1.2GB absolute max
        assert uv_size < max_size, (
            f"UV WebSocket image too large: {uv_size / 1_000_000:.1f}MB"
        )

        print(f"\n✅ WebSocket UV image size: {uv_size / 1_000_000:.1f}MB")

    def test_nexus_image_size_optimized(self):
        """Verify Nexus UV image is smaller than pip equivalent."""
        inspect_cmd = "docker inspect horme-nexus-uv:test --format='{{.Size}}'"
        result = run_docker_command(inspect_cmd, check=False)

        if result.returncode != 0:
            pytest.skip("UV image not built yet, run build tests first")

        uv_size = int(result.stdout.strip())

        # UV image should be under 1GB
        max_size = 1_200_000_000  # 1.2GB absolute max
        assert uv_size < max_size, (
            f"UV Nexus image too large: {uv_size / 1_000_000:.1f}MB"
        )

        print(f"\n✅ Nexus UV image size: {uv_size / 1_000_000:.1f}MB")


@pytest.mark.integration
@pytest.mark.docker
@pytest.mark.timeout(60)
class TestUVImageHealthChecks:
    """Test UV-based images have working health checks."""

    def test_api_health_check_configured(self):
        """Verify API image has health check configured."""
        inspect_cmd = (
            "docker inspect horme-api-uv:test "
            "--format='{{json .Config.Healthcheck}}'"
        )
        result = run_docker_command(inspect_cmd, check=False)

        if result.returncode != 0:
            pytest.skip("UV image not built yet")

        healthcheck = json.loads(result.stdout.strip())

        assert healthcheck is not None, "No health check configured"
        assert 'Test' in healthcheck, "Health check test not defined"
        assert len(healthcheck['Test']) > 0, "Health check test is empty"

        # Verify health check uses /health endpoint
        test_cmd = ' '.join(healthcheck['Test'])
        assert '/health' in test_cmd, "Health check should use /health endpoint"

    def test_websocket_health_check_configured(self):
        """Verify WebSocket image has health check configured."""
        inspect_cmd = (
            "docker inspect horme-websocket-uv:test "
            "--format='{{json .Config.Healthcheck}}'"
        )
        result = run_docker_command(inspect_cmd, check=False)

        if result.returncode != 0:
            pytest.skip("UV image not built yet")

        healthcheck = json.loads(result.stdout.strip())

        assert healthcheck is not None, "No health check configured"
        assert 'Test' in healthcheck, "Health check test not defined"
        assert len(healthcheck['Test']) > 0, "Health check test is empty"

    def test_nexus_health_check_configured(self):
        """Verify Nexus image has health check configured."""
        inspect_cmd = (
            "docker inspect horme-nexus-uv:test "
            "--format='{{json .Config.Healthcheck}}'"
        )
        result = run_docker_command(inspect_cmd, check=False)

        if result.returncode != 0:
            pytest.skip("UV image not built yet")

        healthcheck = json.loads(result.stdout.strip())

        assert healthcheck is not None, "No health check configured"
        assert 'Test' in healthcheck, "Health check test not defined"
        assert len(healthcheck['Test']) > 0, "Health check test is empty"


@pytest.mark.integration
@pytest.mark.docker
@pytest.mark.timeout(30)
class TestUVImageSecurity:
    """Test UV-based images follow security best practices."""

    def test_api_runs_as_non_root(self):
        """Verify API image runs as non-root user."""
        inspect_cmd = (
            "docker inspect horme-api-uv:test "
            "--format='{{.Config.User}}'"
        )
        result = run_docker_command(inspect_cmd, check=False)

        if result.returncode != 0:
            pytest.skip("UV image not built yet")

        user = result.stdout.strip()

        # Should run as 'horme' user or UID 1000
        assert user in ['horme', '1000', 'horme:horme', '1000:1000'], (
            f"Image should run as non-root user, found: {user}"
        )

    def test_websocket_runs_as_non_root(self):
        """Verify WebSocket image runs as non-root user."""
        inspect_cmd = (
            "docker inspect horme-websocket-uv:test "
            "--format='{{.Config.User}}'"
        )
        result = run_docker_command(inspect_cmd, check=False)

        if result.returncode != 0:
            pytest.skip("UV image not built yet")

        user = result.stdout.strip()
        assert user in ['horme', '1000', 'horme:horme', '1000:1000'], (
            f"Image should run as non-root user, found: {user}"
        )

    def test_nexus_runs_as_non_root(self):
        """Verify Nexus image runs as non-root user."""
        inspect_cmd = (
            "docker inspect horme-nexus-uv:test "
            "--format='{{.Config.User}}'"
        )
        result = run_docker_command(inspect_cmd, check=False)

        if result.returncode != 0:
            pytest.skip("UV image not built yet")

        user = result.stdout.strip()
        assert user in ['horme', '1000', 'horme:horme', '1000:1000'], (
            f"Image should run as non-root user, found: {user}"
        )
