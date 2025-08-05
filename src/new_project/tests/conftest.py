"""
Test Configuration for Windows-Compatible Kailash SDK Testing
============================================================

This conftest.py ensures that all tests can run on Windows by:
1. Applying the Windows compatibility patch before any imports
2. Setting up proper Python paths for project modules
3. Providing consistent test environment setup
"""

import sys
import os
from pathlib import Path
import pytest

# Apply Windows compatibility patch immediately
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import and apply the Windows patch before any Kailash imports
try:
    from windows_patch import mock_resource
    print("Windows compatibility patch applied successfully")
except ImportError as e:
    print(f"Warning: Could not apply Windows patch: {e}")

# Add src directory to Python path for dataflow_models imports
src_dir = project_root.parent.parent / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))
    print(f"Added src directory to Python path: {src_dir}")
else:
    print(f"Warning: src directory not found at {src_dir}")

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Setup test environment with Windows compatibility
    """
    print("Setting up test environment...")
    
    # Verify key imports work
    try:
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        print("Core Kailash SDK imports successful")
    except ImportError as e:
        pytest.skip(f"Core Kailash SDK not available: {e}")
    
    try:
        from dataflow import DataFlow
        print("DataFlow package import successful")
    except ImportError as e:
        pytest.skip(f"DataFlow package not available: {e}")
    
    print("Test environment setup complete")


@pytest.fixture
def mock_dataflow_config():
    """
    Provide a mock DataFlow configuration for testing without PostgreSQL
    """
    return {
        "database_url": "postgresql://test:test@localhost:5432/test_db",
        "auto_migrate": False,  # Disable auto-migration for tests
        "monitoring": False,
        "echo": False
    }


@pytest.fixture
def basic_workflow():
    """
    Provide a basic workflow for testing
    """
    from kailash.workflow.builder import WorkflowBuilder
    
    workflow = WorkflowBuilder()
    # Add a simple test node that doesn't require external dependencies
    workflow.add_node("DataSourceNode", "test_source", {
        "data": {"test": "value"}
    })
    return workflow


@pytest.fixture
def local_runtime():
    """
    Provide a LocalRuntime instance for testing
    """
    from kailash.runtime.local import LocalRuntime
    return LocalRuntime()


# Test markers for different test tiers
def pytest_configure(config):
    """
    Configure pytest with custom markers
    """
    config.addinivalue_line(
        "markers", "unit: Fast unit tests with mocking allowed"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests with real services, no mocking"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests with complete workflows"
    )
    config.addinivalue_line(
        "markers", "requires_docker: Tests requiring Docker infrastructure"
    )
    config.addinivalue_line(
        "markers", "requires_postgres: Tests requiring PostgreSQL database"
    )
    config.addinivalue_line(
        "markers", "windows_compat: Windows compatibility tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and SLA validation tests"
    )
    config.addinivalue_line(
        "markers", "compliance: SDK compliance validation tests"
    )


@pytest.fixture
def performance_monitor():
    """
    Provide performance monitoring fixture for tests
    """
    class PerformanceMonitor:
        def __init__(self):
            self.measurements = {}
        
        def start(self, operation_name: str):
            """Start timing an operation"""
            import time
            self.measurements[operation_name] = time.time()
            return self
        
        def stop(self, operation_name: str):
            """Stop timing an operation and return duration"""
            import time
            if operation_name in self.measurements:
                duration = time.time() - self.measurements[operation_name]
                return duration
            return 0.0
        
        def assert_within_threshold(self, threshold: float, operation_name: str):
            """Assert that operation completed within threshold"""
            if operation_name in self.measurements:
                import time
                duration = time.time() - self.measurements[operation_name]
                assert duration < threshold, f"Operation '{operation_name}' took {duration:.3f}s, exceeds threshold {threshold}s"
    
    return PerformanceMonitor()


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to handle Windows-specific needs
    """
    for item in items:
        # Add Windows compatibility marker to all tests
        item.add_marker(pytest.mark.windows_compat)
        
        # Skip PostgreSQL-dependent tests if not available
        if "postgres" in item.name.lower() or "dataflow" in item.name.lower():
            item.add_marker(pytest.mark.requires_postgres)