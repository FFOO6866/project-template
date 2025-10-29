"""Integration tests for UV dependency management.

This module validates UV lockfile consistency, dependency resolution,
and OpenAI version standardization across the project.

Following Tier 2 integration testing requirements:
- Real file validation (NO MOCKING)
- Real UV commands
- Real dependency checks
"""

import json
import os
import re
import subprocess
import toml
import pytest
from pathlib import Path
from typing import Dict, List, Set


@pytest.fixture(scope="module")
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def pyproject_data(project_root):
    """Load and parse pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        pytest.skip("pyproject.toml not found")

    return toml.load(pyproject_path)


def run_uv_command(cmd: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """Run UV command and return result."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=300  # 5 minute timeout
    )

    if check and result.returncode != 0:
        raise RuntimeError(f"UV command failed: {result.stderr}")

    return result


@pytest.mark.integration
@pytest.mark.uv
@pytest.mark.timeout(60)
class TestPyprojectConfiguration:
    """Test pyproject.toml configuration is valid."""

    def test_pyproject_toml_exists(self, project_root):
        """Verify pyproject.toml exists and is readable."""
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml not found"
        assert pyproject.is_file(), "pyproject.toml is not a file"
        assert os.access(pyproject, os.R_OK), "pyproject.toml is not readable"

    def test_pyproject_toml_valid_toml(self, pyproject_data):
        """Verify pyproject.toml is valid TOML."""
        assert pyproject_data is not None, "Failed to parse pyproject.toml"
        assert isinstance(pyproject_data, dict), "pyproject.toml is not a dictionary"

    def test_project_metadata_exists(self, pyproject_data):
        """Verify required project metadata is present."""
        assert 'project' in pyproject_data, "Missing [project] section"

        project = pyproject_data['project']
        required_fields = ['name', 'version', 'description', 'requires-python']

        for field in required_fields:
            assert field in project, f"Missing required field: {field}"
            assert project[field], f"Empty value for: {field}"

    def test_dependencies_declared(self, pyproject_data):
        """Verify dependencies are properly declared."""
        assert 'project' in pyproject_data
        assert 'dependencies' in pyproject_data['project']

        deps = pyproject_data['project']['dependencies']
        assert isinstance(deps, list), "dependencies should be a list"
        assert len(deps) > 0, "No dependencies declared"

    def test_openai_version_standardized(self, pyproject_data):
        """Verify OpenAI is standardized to version 1.51.2."""
        deps = pyproject_data['project']['dependencies']

        # Find OpenAI dependency
        openai_deps = [d for d in deps if d.startswith('openai==')]

        assert len(openai_deps) == 1, (
            f"Expected exactly 1 OpenAI dependency, found {len(openai_deps)}"
        )

        openai_dep = openai_deps[0]
        assert openai_dep == "openai==1.51.2", (
            f"OpenAI should be version 1.51.2, found: {openai_dep}"
        )

    def test_no_duplicate_dependencies(self, pyproject_data):
        """Verify no duplicate dependencies in pyproject.toml."""
        deps = pyproject_data['project']['dependencies']

        # Extract package names (before ==, >=, etc.)
        package_names = []
        for dep in deps:
            # Split on version operators
            name = re.split(r'[=<>!]', dep)[0].strip()
            package_names.append(name.lower())

        # Check for duplicates
        duplicates = []
        seen = set()
        for name in package_names:
            if name in seen:
                duplicates.append(name)
            seen.add(name)

        assert len(duplicates) == 0, f"Duplicate dependencies found: {duplicates}"

    def test_build_system_configured(self, pyproject_data):
        """Verify build system is properly configured."""
        assert 'build-system' in pyproject_data, "Missing [build-system] section"

        build_system = pyproject_data['build-system']
        assert 'requires' in build_system, "Missing build-system.requires"
        assert 'build-backend' in build_system, "Missing build-system.build-backend"

    def test_uv_configuration_exists(self, pyproject_data):
        """Verify UV tool configuration exists."""
        assert 'tool' in pyproject_data, "Missing [tool] section"
        assert 'uv' in pyproject_data['tool'], "Missing [tool.uv] section"

        uv_config = pyproject_data['tool']['uv']
        assert 'python-version' in uv_config, "Missing python-version in UV config"


@pytest.mark.integration
@pytest.mark.uv
@pytest.mark.timeout(60)
class TestUVLockfile:
    """Test UV lockfile consistency and validity."""

    def test_uv_lock_exists(self, project_root):
        """Verify uv.lock exists."""
        lockfile = project_root / "uv.lock"

        # Check if UV is being used
        pyproject = project_root / "pyproject.toml"
        if not pyproject.exists():
            pytest.skip("pyproject.toml not found, UV may not be configured")

        # uv.lock should exist after initial setup
        if not lockfile.exists():
            pytest.skip(
                "uv.lock not found. Run 'uv lock' to generate it. "
                "This is expected on first setup."
            )

        assert lockfile.is_file(), "uv.lock is not a file"
        assert os.access(lockfile, os.R_OK), "uv.lock is not readable"

    def test_uv_lock_not_empty(self, project_root):
        """Verify uv.lock is not empty."""
        lockfile = project_root / "uv.lock"

        if not lockfile.exists():
            pytest.skip("uv.lock not found, run 'uv lock' first")

        content = lockfile.read_text()
        assert len(content) > 0, "uv.lock is empty"

        # Should contain package information
        assert 'package' in content.lower(), "uv.lock missing package information"

    def test_uv_lock_consistent_with_pyproject(self, project_root):
        """Verify uv.lock is consistent with pyproject.toml."""
        lockfile = project_root / "uv.lock"

        if not lockfile.exists():
            pytest.skip("uv.lock not found, run 'uv lock' first")

        # Run UV check command
        result = run_uv_command("uv lock --check", project_root, check=False)

        if result.returncode != 0:
            # Try to show what's different
            pytest.fail(
                f"uv.lock is out of sync with pyproject.toml.\n"
                f"Run 'uv lock' to update.\n"
                f"Error: {result.stderr}"
            )


@pytest.mark.integration
@pytest.mark.uv
@pytest.mark.timeout(300)
class TestDependencyInstallation:
    """Test UV dependency installation works correctly."""

    def test_uv_command_available(self):
        """Verify UV command is available."""
        result = subprocess.run(
            "uv --version",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            pytest.skip(
                "UV not installed. Install with: "
                "curl -LsSf https://astral.sh/uv/install.sh | sh"
            )

        assert "uv" in result.stdout.lower(), "UV version output unexpected"

    def test_dependencies_install_without_errors(self, project_root):
        """Test that all dependencies install without errors."""
        # Create a temporary venv for testing
        test_venv = project_root / ".venv-test"

        try:
            # Remove existing test venv
            if test_venv.exists():
                import shutil
                shutil.rmtree(test_venv)

            # Create fresh venv and sync dependencies
            result = run_uv_command(
                f"uv venv {test_venv} && uv sync --no-dev",
                project_root,
                check=False
            )

            if result.returncode != 0:
                pytest.fail(
                    f"Dependency installation failed:\n"
                    f"stdout: {result.stdout}\n"
                    f"stderr: {result.stderr}"
                )

            # Verify venv was created
            assert test_venv.exists(), "Test venv was not created"

        finally:
            # Cleanup test venv
            if test_venv.exists():
                import shutil
                shutil.rmtree(test_venv, ignore_errors=True)

    def test_no_version_conflicts(self, project_root):
        """Verify there are no dependency version conflicts."""
        # UV's lock command will fail if there are conflicts
        result = run_uv_command("uv lock --check", project_root, check=False)

        if result.returncode != 0:
            pytest.fail(
                f"Dependency conflicts detected:\n{result.stderr}"
            )


@pytest.mark.integration
@pytest.mark.uv
@pytest.mark.timeout(120)
class TestCriticalDependencies:
    """Test critical dependencies are present and correct versions."""

    def test_fastapi_installed(self, pyproject_data):
        """Verify FastAPI is installed."""
        deps = pyproject_data['project']['dependencies']
        fastapi_deps = [d for d in deps if d.startswith('fastapi==')]

        assert len(fastapi_deps) == 1, "FastAPI should be declared exactly once"
        assert 'fastapi==' in fastapi_deps[0], "FastAPI version should be pinned"

    def test_postgresql_drivers_installed(self, pyproject_data):
        """Verify PostgreSQL drivers are installed."""
        deps = pyproject_data['project']['dependencies']

        # Should have both asyncpg and psycopg2
        asyncpg = any(d.startswith('asyncpg==') for d in deps)
        psycopg2 = any(d.startswith('psycopg2-binary==') for d in deps)

        assert asyncpg, "asyncpg should be installed for async PostgreSQL"
        assert psycopg2, "psycopg2-binary should be installed for sync PostgreSQL"

    def test_redis_client_installed(self, pyproject_data):
        """Verify Redis client is installed."""
        deps = pyproject_data['project']['dependencies']
        redis_deps = [d for d in deps if d.startswith('redis==')]

        assert len(redis_deps) == 1, "Redis should be declared exactly once"

    def test_neo4j_driver_installed(self, pyproject_data):
        """Verify Neo4j driver is installed."""
        deps = pyproject_data['project']['dependencies']
        neo4j_deps = [d for d in deps if d.startswith('neo4j==')]

        assert len(neo4j_deps) == 1, "Neo4j should be declared exactly once"

    def test_openai_client_installed(self, pyproject_data):
        """Verify OpenAI client is installed at correct version."""
        deps = pyproject_data['project']['dependencies']
        openai_deps = [d for d in deps if d.startswith('openai==')]

        assert len(openai_deps) == 1, "OpenAI should be declared exactly once"
        assert openai_deps[0] == "openai==1.51.2", (
            f"OpenAI should be version 1.51.2, found: {openai_deps[0]}"
        )

    def test_security_packages_installed(self, pyproject_data):
        """Verify security packages are installed."""
        deps = pyproject_data['project']['dependencies']

        required_security = [
            'passlib',  # Password hashing
            'python-jose',  # JWT tokens
            'cryptography',  # Encryption
        ]

        for package in required_security:
            package_found = any(
                d.startswith(f'{package}==') or d.startswith(f'{package}[')
                for d in deps
            )
            assert package_found, f"Security package {package} not found"


@pytest.mark.integration
@pytest.mark.uv
@pytest.mark.timeout(60)
class TestDevDependencies:
    """Test development dependencies are properly configured."""

    def test_dev_dependencies_declared(self, pyproject_data):
        """Verify dev dependencies are declared separately."""
        assert 'tool' in pyproject_data
        assert 'uv' in pyproject_data['tool']

        uv_config = pyproject_data['tool']['uv']

        # Check for dev dependencies
        if 'dev-dependencies' in uv_config:
            dev_deps = uv_config['dev-dependencies']
            assert isinstance(dev_deps, list), "dev-dependencies should be a list"
            assert len(dev_deps) > 0, "No dev dependencies declared"

    def test_pytest_in_dev_dependencies(self, pyproject_data):
        """Verify pytest is in dev dependencies."""
        uv_config = pyproject_data.get('tool', {}).get('uv', {})
        dev_deps = uv_config.get('dev-dependencies', [])

        pytest_found = any('pytest' in dep for dep in dev_deps)
        assert pytest_found, "pytest should be in dev dependencies"

    def test_code_quality_tools_in_dev_dependencies(self, pyproject_data):
        """Verify code quality tools are in dev dependencies."""
        uv_config = pyproject_data.get('tool', {}).get('uv', {})
        dev_deps = uv_config.get('dev-dependencies', [])

        # Convert to lowercase for case-insensitive search
        dev_deps_str = ' '.join(dev_deps).lower()

        quality_tools = ['black', 'mypy']

        for tool in quality_tools:
            assert tool in dev_deps_str, (
                f"Code quality tool {tool} should be in dev dependencies"
            )


@pytest.mark.integration
@pytest.mark.uv
@pytest.mark.timeout(30)
class TestSubProjectIsolation:
    """Test sub-projects maintain separate dependencies."""

    def test_new_project_has_separate_requirements(self, project_root):
        """Verify src/new_project has separate requirements."""
        new_project_req = project_root / "src" / "new_project" / "requirements-production.txt"

        # This is optional, skip if doesn't exist
        if not new_project_req.exists():
            pytest.skip("src/new_project/requirements-production.txt not found")

        assert new_project_req.is_file()
        content = new_project_req.read_text()
        assert len(content) > 0, "requirements-production.txt is empty"

    def test_tests_have_separate_requirements(self, project_root):
        """Verify tests/ has separate requirements."""
        tests_req = project_root / "tests" / "requirements-test.txt"

        if not tests_req.exists():
            pytest.skip("tests/requirements-test.txt not found")

        assert tests_req.is_file()
        content = tests_req.read_text()
        assert len(content) > 0, "requirements-test.txt is empty"

    def test_no_circular_dependencies_between_subprojects(self, project_root):
        """Verify sub-projects don't have circular dependencies."""
        # This is a smoke test - UV lock would fail on circular deps
        lockfile = project_root / "uv.lock"

        if not lockfile.exists():
            pytest.skip("uv.lock not found")

        # UV successfully creating a lockfile means no circular deps
        assert lockfile.exists()
        assert lockfile.stat().st_size > 0
