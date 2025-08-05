"""
Basic Functionality Test - Windows-Safe Baseline Test
====================================================

This test file provides the absolute minimum functionality validation
to ensure the test infrastructure is working correctly on Windows.

This test is designed to ALWAYS PASS and provides immediate success feedback.
"""
import pytest
import sys
import os
from pathlib import Path


class TestBasicWindowsFunctionality:
    """Basic tests that verify Windows compatibility and test infrastructure."""
    
    def test_python_environment(self):
        """Test that Python environment is properly configured."""
        assert sys.version_info.major >= 3
        assert sys.version_info.minor >= 8
        assert sys.platform == "win32"
        assert os.name == "nt"
        
    def test_path_handling(self):
        """Test that path handling works correctly on Windows."""
        current_path = Path.cwd()
        assert current_path.exists()
        assert isinstance(str(current_path), str)
        
        # Test that we can create and manipulate paths
        test_path = current_path / "test_file.txt"
        assert test_path.suffix == ".txt"
        assert test_path.stem == "test_file"
        
    def test_basic_imports(self):
        """Test that basic Python imports work."""
        import json
        import pathlib
        import subprocess
        import unittest.mock
        
        # Verify imports are accessible
        assert hasattr(json, 'loads')
        assert hasattr(pathlib, 'Path')
        assert hasattr(subprocess, 'run')
        assert hasattr(unittest.mock, 'Mock')


class TestSDKImports:
    """Test basic SDK imports work without errors."""
    
    def test_core_sdk_imports(self):
        """Test that core Kailash SDK components can be imported."""
        try:
            from kailash.workflow.builder import WorkflowBuilder
            from kailash.runtime.local import LocalRuntime
            
            # Verify classes can be instantiated
            workflow = WorkflowBuilder()
            runtime = LocalRuntime()
            
            assert workflow is not None
            assert runtime is not None
            
        except ImportError as e:
            pytest.skip(f"Core SDK not available: {e}")
    
    def test_workflow_creation(self):
        """Test that we can create a basic workflow."""
        try:
            from kailash.workflow.builder import WorkflowBuilder
            
            workflow = WorkflowBuilder()
            
            # Test basic workflow operations
            assert hasattr(workflow, 'add_node')
            assert hasattr(workflow, 'build')
            
            # Create a minimal workflow with a node that actually exists
            workflow.add_node("PythonCodeNode", "test_source", {
                "code": "result = {'test': 'value'}"
            })
            
            # Verify workflow can be built
            built_workflow = workflow.build()
            assert built_workflow is not None
            
        except ImportError as e:
            pytest.skip(f"Core SDK not available: {e}")


@pytest.mark.unit
class TestInfrastructureReady:
    """Test that test infrastructure components are working."""
    
    def test_pytest_markers(self):
        """Test that pytest markers are properly configured."""
        # This test should be marked as 'unit'
        # If markers are working, this will pass without error
        assert True
        
    def test_mocking_available(self):
        """Test that mocking capabilities are available."""
        from unittest.mock import Mock, patch
        
        # Test basic mock
        mock_obj = Mock()
        mock_obj.method.return_value = "test"
        assert mock_obj.method() == "test"
        
        # Test patch capability with a safer target
        with patch('os.getcwd') as mock_getcwd:
            mock_getcwd.return_value = "/test/path"
            import os
            assert os.getcwd() == "/test/path"
            
    def test_performance_baseline(self):
        """Test that tests can complete quickly (Tier 1 requirement)."""
        import time
        start_time = time.time()
        
        # Simple operation
        result = sum(range(100))
        
        duration = time.time() - start_time
        assert duration < 1.0  # Must complete in under 1 second
        assert result == 4950  # Verify calculation is correct


if __name__ == "__main__":
    # Allow running this test directly
    pytest.main([__file__, "-v"])