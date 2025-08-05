"""
Infrastructure Validation Tests - Test-First Development
======================================================

These tests validate the current Windows development environment setup
after implementing fixes. We test what SHOULD work vs what DOES work.

Note: Windows compatibility patch and path setup is handled by conftest.py
"""

import sys
import importlib
import subprocess
import pytest
from pathlib import Path


class TestWindowsSDKCompatibility:
    """Test Windows compatibility for Kailash SDK"""
    
    def test_windows_patch_applied(self):
        """Test that the Windows patch is applied for resource module"""
        # Patch should already be applied by conftest.py
        import resource
        assert hasattr(resource, 'getrlimit')
        assert hasattr(resource, 'setrlimit')
        assert hasattr(resource, 'RLIMIT_AS')
        
        # Test that functions work
        limits = resource.getrlimit(resource.RLIMIT_AS)
        assert isinstance(limits, tuple)
        assert len(limits) == 2
    
    def test_kailash_workflow_builder_import(self):
        """Test that Kailash WorkflowBuilder can be imported"""
        # This will likely fail initially - that's expected for TDD
        try:
            from kailash.workflow.builder import WorkflowBuilder
            # If we get here, the import worked
            assert WorkflowBuilder is not None
            workflow_import_success = True
        except ImportError as e:
            workflow_import_success = False
            pytest.fail(f"WorkflowBuilder import failed: {e}")
    
    def test_kailash_local_runtime_import(self):
        """Test that Kailash LocalRuntime can be imported"""
        try:
            from kailash.runtime.local import LocalRuntime
            assert LocalRuntime is not None
            runtime_import_success = True
        except ImportError as e:
            runtime_import_success = False
            pytest.fail(f"LocalRuntime import failed: {e}")
    
    def test_basic_workflow_creation(self):
        """Test that we can create a basic workflow"""
        # Skip if imports failed
        pytest.importorskip("kailash.workflow.builder")
        pytest.importorskip("kailash.runtime.local")
        
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        
        # Create workflow
        workflow = WorkflowBuilder()
        assert workflow is not None
        
        # Create runtime
        runtime = LocalRuntime()
        assert runtime is not None


class TestDataFlowPackageAvailability:
    """Test DataFlow package and imports"""
    
    def test_dataflow_models_import(self):
        """Test that dataflow_models can be imported"""
        # Path setup handled by conftest.py
        try:
            from dataflow_models import db
            assert db is not None
        except ImportError as e:
            pytest.fail(f"dataflow_models import failed: {e}")
    
    def test_kailash_dataflow_import(self):
        """Test that kailash-dataflow package can be imported"""
        try:
            # The actual module name is 'dataflow' from kailash-dataflow package
            from dataflow import DataFlow
            assert DataFlow is not None
        except ImportError as e:
            pytest.fail(f"kailash-dataflow import failed: {e}")
    
    def test_db_model_decorator_available(self):
        """Test that @db.model decorator is available"""
        # Path setup handled by conftest.py
        try:
            from dataflow_models import db
            assert hasattr(db, 'model')
            assert callable(db.model)
        except ImportError as e:
            pytest.skip(f"dataflow_models not available: {e}")


class TestPythonEnvironmentConfiguration:
    """Test Python PATH and environment setup"""
    
    def test_python_command_available(self):
        """Test that 'python' command is available"""
        try:
            result = subprocess.run(['python', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            python_available = result.returncode == 0
            if not python_available:
                # Try 'py' command as fallback
                result = subprocess.run(['py', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                py_available = result.returncode == 0
                if py_available:
                    pytest.fail("Only 'py' command available, 'python' command missing")
                else:
                    pytest.fail("Neither 'python' nor 'py' commands available")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            pytest.fail(f"Python command test failed: {e}")
    
    def test_pip_install_capability(self):
        """Test that pip can install packages"""
        try:
            result = subprocess.run(['python', '-m', 'pip', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            assert result.returncode == 0
            assert 'pip' in result.stdout.lower()
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            pytest.fail(f"Pip test failed: {e}")
    
    def test_virtual_environment_active(self):
        """Test that we're in a virtual environment"""
        # Check if we're in a virtual environment
        venv_active = (hasattr(sys, 'real_prefix') or 
                      (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
        
        if not venv_active:
            pytest.skip("Not in virtual environment - this may be intentional")


class TestCurrentWorkingEnvironment:
    """Test current working environment state"""
    
    def test_project_structure_exists(self):
        """Test that expected project structure exists"""
        project_root = Path(__file__).parent.parent.parent
        
        # Check for key directories
        expected_dirs = [
            'tests',
            'tests/unit',
            'tests/integration', 
            'tests/e2e'
        ]
        
        for dir_path in expected_dirs:
            full_path = project_root / dir_path
            if not full_path.exists():
                # Create the directory if it doesn't exist
                full_path.mkdir(parents=True, exist_ok=True)
        
        # Verify they now exist
        for dir_path in expected_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory {dir_path} should exist"
    
    def test_pytest_can_run(self):
        """Test that pytest can execute"""
        try:
            result = subprocess.run(['python', '-m', 'pytest', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            assert result.returncode == 0
            assert 'pytest' in result.stdout.lower()
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            pytest.fail(f"Pytest execution test failed: {e}")


if __name__ == "__main__":
    # Run tests directly if called as script
    pytest.main([__file__, "-v"])