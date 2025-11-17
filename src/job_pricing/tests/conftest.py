"""
Root Pytest Configuration

Sets up Python path to allow importing from src.job_pricing.*
"""

import sys
import os
from pathlib import Path

# Add the project root directory to Python path
# Project structure: job_pricing/src/job_pricing/...
# We need to add job_pricing/ so we can: from src.job_pricing.* import
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set PYTHONPATH environment variable as well
os.environ['PYTHONPATH'] = str(project_root)

import pytest
from typing import Generator


@pytest.fixture(scope="session")
def test_client() -> Generator:
    """
    Create a TestClient for the FastAPI app.

    This client can be used to make HTTP requests to the API
    without requiring a running server.
    """
    # Import here to avoid circular import issues
    from fastapi.testclient import TestClient
    from src.job_pricing.api.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Setup test environment variables and configuration.

    This runs once at the start of the test session.
    """
    import os

    # Set test environment variables
    os.environ.setdefault("ENVIRONMENT", "testing")
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("OPENAI_API_KEY", "sk-" + "test" * 12)
    os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing")
    os.environ.setdefault("API_KEY_SALT", "test-salt")

    yield

    # Cleanup if needed
