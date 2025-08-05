"""
Infrastructure Reality Check Tests

These tests capture the current broken state and validate actual technical feasibility.
Tests are written to FAIL first, documenting the real problems, then implementation
fixes the issues to make tests pass.

NEVER modify these tests to make them pass - fix the underlying issues instead.
"""

import pytest
import subprocess
import sys
import os
from pathlib import Path


class TestPythonEnvironmentAccessibility:
    """Test actual Python environment accessibility from the project directory."""
    
    def test_python_command_accessible_from_project_root(self):
        """Should be able to access Python from command line in project directory."""
        project_root = Path("C:/Users/fujif/OneDrive/Documents/GitHub/horme-pov")
        os.chdir(project_root)
        
        try:
            result = subprocess.run([sys.executable, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, f"Python not accessible: {result.stderr}"
            assert "Python" in result.stdout, f"Unexpected Python version output: {result.stdout}"
        except FileNotFoundError:
            pytest.fail("Python executable not found in system PATH")
        except subprocess.TimeoutExpired:
            pytest.fail("Python version check timed out")
    
    def test_pip_accessible_and_working(self):
        """Should be able to run pip commands successfully."""
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, f"pip not accessible: {result.stderr}"
            assert "pip" in result.stdout.lower(), f"Unexpected pip output: {result.stdout}"
        except FileNotFoundError:
            pytest.fail("pip not accessible via python -m pip")
        except subprocess.TimeoutExpired:
            pytest.fail("pip version check timed out")


class TestSDKImportCompatibility:
    """Test Kailash SDK import compatibility on Windows environment."""
    
    def test_basic_kailash_import(self):
        """Should import basic Kailash SDK components without errors."""
        # This test is expected to FAIL due to Windows compatibility issues
        with pytest.raises(ImportError) as exc_info:
            try:
                # Windows compatibility patch
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent.parent.parent))
                import windows_sdk_compatibility  # Apply Windows compatibility for Kailash SDK

                from kailash.workflow.builder import WorkflowBuilder
                pytest.fail("Expected ImportError due to resource module dependency, but import succeeded")
            except ImportError as e:
                # Document the actual error for debugging
                error_msg = str(e)
                print(f"Captured ImportError: {error_msg}")
                raise e
        
        # Verify it's the expected resource module error
        assert "resource" in str(exc_info.value).lower() or "unix" in str(exc_info.value).lower(), \
            f"Unexpected import error: {exc_info.value}"
    
    def test_kailash_runtime_import(self):
        """Should import Kailash runtime components without errors."""
        # This test is also expected to FAIL
        with pytest.raises(ImportError) as exc_info:
            try:
                from kailash.runtime.local import LocalRuntime
                pytest.fail("Expected ImportError due to Windows compatibility, but import succeeded")
            except ImportError as e:
                error_msg = str(e)
                print(f"Captured Runtime ImportError: {error_msg}")
                raise e
        
        # Document the specific error pattern
        assert "resource" in str(exc_info.value).lower() or "unix" in str(exc_info.value).lower(), \
            f"Unexpected runtime import error: {exc_info.value}"
    
    def test_kailash_package_installation_status(self):
        """Should verify if Kailash package is actually installed."""
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "show", "kailash"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"Kailash package info: {result.stdout}")
                # Package is installed but imports fail - compatibility issue
                assert False, "Kailash is installed but imports fail due to Windows compatibility"
            else:
                # Package not installed at all
                assert False, "Kailash SDK is not installed. Run: pip install kailash"
                
        except subprocess.TimeoutExpired:
            pytest.fail("Package check timed out")


class TestDockerServicesHealthCheck:
    """Test actual Docker services connectivity and health."""
    
    def test_docker_command_accessible(self):
        """Should be able to run Docker commands."""
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, f"Docker not accessible: {result.stderr}"
            assert "Docker version" in result.stdout, f"Unexpected docker output: {result.stdout}"
        except FileNotFoundError:
            pytest.fail("Docker command not found - Docker not installed or not in PATH")
        except subprocess.TimeoutExpired:
            pytest.fail("Docker version check timed out")
    
    def test_docker_compose_accessible(self):
        """Should be able to run Docker Compose commands."""
        try:
            result = subprocess.run(["docker", "compose", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                # Try docker-compose as fallback
                result = subprocess.run(["docker-compose", "--version"], 
                                      capture_output=True, text=True, timeout=10)
            
            assert result.returncode == 0, f"Docker Compose not accessible: {result.stderr}"
            assert "docker" in result.stdout.lower() and "compose" in result.stdout.lower(), \
                f"Unexpected docker-compose output: {result.stdout}"
        except FileNotFoundError:
            pytest.fail("Docker Compose not found - neither 'docker compose' nor 'docker-compose' work")
        except subprocess.TimeoutExpired:
            pytest.fail("Docker Compose version check timed out")
    
    def test_test_environment_docker_services_not_running(self):
        """Should document that test environment services are not currently running."""
        project_root = Path("C:/Users/fujif/OneDrive/Documents/GitHub/horme-pov")
        test_utils_path = project_root / "tests" / "utils"
        
        # This test documents the current state - services not running
        if test_utils_path.exists():
            test_env_script = test_utils_path / "test-env"
            if test_env_script.exists():
                try:
                    result = subprocess.run([str(test_env_script), "status"], 
                                          capture_output=True, text=True, timeout=30)
                    # Expected to fail - services not running
                    assert result.returncode != 0, \
                        "Test services unexpectedly running - this should be failing initially"
                    print(f"Expected failure - services not running: {result.stdout} {result.stderr}")
                except FileNotFoundError:
                    pytest.fail("test-env script not executable or not found")
                except subprocess.TimeoutExpired:
                    pytest.fail("test-env status check timed out")
            else:
                pytest.fail("test-env script not found in tests/utils directory")
        else:
            pytest.fail("tests/utils directory not found - missing test infrastructure")


class TestWSL2CompatibilityCheck:
    """Test WSL2 availability and SDK compatibility within WSL2 if available."""
    
    def test_wsl2_availability(self):
        """Should check if WSL2 is available on this Windows system."""
        try:
            result = subprocess.run(["wsl", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"WSL version info: {result.stdout}")
                # WSL is available - this is good news
                assert True, "WSL2 is available for potential SDK compatibility workaround"
            else:
                # WSL not available or not configured
                pytest.skip("WSL2 not available - cannot test SDK compatibility workaround")
                
        except FileNotFoundError:
            pytest.skip("WSL command not found - WSL2 not installed")
        except subprocess.TimeoutExpired:
            pytest.fail("WSL version check timed out")
    
    def test_wsl2_python_environment(self):
        """Should test if Python works within WSL2 environment."""
        try:
            # First check if WSL is available
            wsl_check = subprocess.run(["wsl", "--version"], 
                                     capture_output=True, text=True, timeout=5)
            if wsl_check.returncode != 0:
                pytest.skip("WSL2 not available")
            
            # Test Python in WSL
            result = subprocess.run(["wsl", "python3", "--version"], 
                                  capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                print(f"WSL Python version: {result.stdout}")
                assert "Python" in result.stdout, "WSL Python environment working"
            else:
                pytest.skip("Python not installed in WSL2 environment")
                
        except FileNotFoundError:
            pytest.skip("WSL command not found")
        except subprocess.TimeoutExpired:
            pytest.fail("WSL Python check timed out")


class TestProjectStructureValidation:
    """Test actual project structure matches expected patterns."""
    
    def test_core_directories_exist(self):
        """Should verify core project directories exist."""
        project_root = Path("C:/Users/fujif/OneDrive/Documents/GitHub/horme-pov")
        
        expected_dirs = [
            "src/new_project",
            "tests",
            "tests/utils", 
            "src/new_project/tests",
            "src/new_project/tests/unit",
            "src/new_project/tests/integration", 
            "src/new_project/tests/e2e"
        ]
        
        missing_dirs = []
        for dir_path in expected_dirs:
            full_path = project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        assert len(missing_dirs) == 0, f"Missing expected directories: {missing_dirs}"
    
    def test_test_infrastructure_files_exist(self):
        """Should verify test infrastructure files exist."""
        project_root = Path("C:/Users/fujif/OneDrive/Documents/GitHub/horme-pov")
        
        expected_files = [
            "tests/utils/test-env",
            "src/new_project/pytest.ini",
            "src/new_project/tests/conftest.py"
        ]
        
        missing_files = []
        for file_path in expected_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"Missing test infrastructure files: {missing_files}")
            # Don't fail immediately - document what's missing
            assert False, f"Test infrastructure incomplete - missing: {missing_files}"


if __name__ == "__main__":
    # Run the reality check tests
    print("=== Infrastructure Reality Check Tests ===")
    print("These tests document the current broken state.")
    print("DO NOT modify tests to make them pass - fix the underlying issues.")
    print()
    
    pytest.main([__file__, "-v", "--tb=short"])