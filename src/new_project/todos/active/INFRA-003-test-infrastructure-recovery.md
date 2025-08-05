# INFRA-003: Test Infrastructure Foundation Recovery

**Created:** 2025-08-02  
**Assigned:** Testing Infrastructure Team  
**Priority:** 🚨 P0 - CRITICAL  
**Status:** PENDING  
**Estimated Effort:** 10 hours  
**Due Date:** 2025-08-05 (72-hour critical recovery)

## Description

Repair the completely broken test infrastructure that is preventing all test discovery and execution. Currently showing 0 tests run despite having extensive test files, indicating critical issues with pytest configuration, import errors, and test discovery mechanisms.

## Critical Issues Identified

1. **Zero Test Discovery**: pytest finds 0 tests despite extensive test files existing
2. **Import Failures**: Test files have import errors preventing execution
3. **Missing Test Dependencies**: Required testing modules not properly configured
4. **Pytest Configuration Issues**: Test discovery and execution configuration broken
5. **False Progress Reporting**: Claims of 100% success when 0% tests actually run

## Current Status Analysis

```
Reality Check - Test Execution Results:
- Tests Run: 0 (ZERO)
- Tests Passed: 0  
- Tests Failed: 0
- Success Rate: 0.0% (NOT 100% as claimed)
- Test Discovery: COMPLETELY BROKEN
```

## Acceptance Criteria

- [ ] pytest successfully discovers and lists all test files
- [ ] All test imports resolve without errors
- [ ] Unit tests execute and provide real results (not 0 tests run)
- [ ] Integration tests can connect to required services
- [ ] E2E tests can execute complete workflows
- [ ] Test reporting shows accurate pass/fail counts
- [ ] Progress reporting reflects actual test execution status
- [ ] 3-tier testing strategy fully operational

## Subtasks

- [ ] Diagnose Test Discovery Failures (Est: 2h)
  - Verification: Identify exact causes of 0 test discovery
  - Output: Complete analysis of pytest configuration and import issues
- [ ] Fix Test Import Dependencies (Est: 3h)
  - Verification: All test files import successfully without errors
  - Output: Resolved import paths and dependency issues
- [ ] Repair Pytest Configuration (Est: 2h)
  - Verification: pytest.ini and conftest.py properly configured
  - Output: Working test discovery and execution configuration
- [ ] Establish Test Environment Setup (Est: 2h)
  - Verification: Test fixtures and utilities work correctly
  - Output: Functional testing environment with proper isolation
- [ ] Validate 3-Tier Test Execution (Est: 1h)
  - Verification: Unit, Integration, E2E tests all execute successfully
  - Output: Real test results with accurate pass/fail reporting

## Dependencies

- **INFRA-001**: Windows SDK Compatibility (for SDK imports in tests)
- **INFRA-002**: NodeParameter fixes (for node-related test functionality)
- Python testing dependencies (pytest, pytest-asyncio, etc.)

## Risk Assessment

- **CRITICAL**: Zero test coverage means no validation of any functionality
- **HIGH**: Cannot verify any fixes or implementations without working tests
- **HIGH**: False progress reporting hiding actual development status
- **MEDIUM**: Complex import dependency chain requires careful resolution
- **MEDIUM**: Test environment setup may require significant Docker configuration

## Technical Implementation Plan

### Phase 3A: Test Discovery Diagnostic (Hours 1-2)
```python
# test_discovery_diagnostic.py
import pytest
import sys
import os
from pathlib import Path
import importlib.util

class TestDiscoveryDiagnostic:
    """Diagnose why pytest discovers 0 tests"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_directories = [
            self.project_root / "tests" / "unit",
            self.project_root / "tests" / "integration", 
            self.project_root / "tests" / "e2e"
        ]
    
    def diagnose_discovery_issues(self):
        """Comprehensive test discovery diagnosis"""
        
        print("🔍 TEST DISCOVERY DIAGNOSTIC")
        print("=" * 50)
        
        # Check 1: Test directories exist
        print("📁 Test Directory Analysis:")
        for test_dir in self.test_directories:
            if test_dir.exists():
                test_files = list(test_dir.glob("test_*.py"))
                print(f"  ✓ {test_dir}: {len(test_files)} test files found")
                
                for test_file in test_files:
                    import_status = self._check_import(test_file)
                    print(f"    {'✓' if import_status['success'] else '✗'} {test_file.name}: {import_status['status']}")
            else:
                print(f"  ✗ {test_dir}: DIRECTORY NOT FOUND")
        
        # Check 2: pytest configuration
        print("\n⚙️ Pytest Configuration Analysis:")
        self._check_pytest_config()
        
        # Check 3: Import chain validation
        print("\n🔗 Import Chain Analysis:")
        self._validate_import_chains()
        
        # Check 4: Test function detection  
        print("\n🎯 Test Function Detection:")
        self._detect_test_functions()
    
    def _check_import(self, test_file: Path) -> dict:
        """Check if test file can be imported"""
        try:
            spec = importlib.util.spec_from_file_location("test_module", test_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return {"success": True, "status": "Import successful"}
        except Exception as e:
            return {"success": False, "status": f"Import failed: {str(e)[:50]}..."}
    
    def _check_pytest_config(self):
        """Check pytest.ini and conftest.py configuration"""
        
        # Check pytest.ini
        pytest_ini = self.project_root / "pytest.ini"
        if pytest_ini.exists():
            print(f"  ✓ pytest.ini found")
            with open(pytest_ini) as f:
                content = f.read()
                if "testpaths" in content:
                    print(f"  ✓ testpaths configured")
                else:
                    print(f"  ⚠️ testpaths not configured")
        else:
            print(f"  ✗ pytest.ini NOT FOUND")
        
        # Check conftest.py
        conftest = self.project_root / "tests" / "conftest.py"
        if conftest.exists():
            print(f"  ✓ conftest.py found")
        else:
            print(f"  ✗ conftest.py NOT FOUND")
    
    def _validate_import_chains(self):
        """Validate critical import dependencies"""
        critical_imports = [
            "pytest",
            "kailash.workflow.builder",
            "kailash.runtime.local",
            "kailash.nodes.base"
        ]
        
        for import_name in critical_imports:
            try:
                __import__(import_name)
                print(f"  ✓ {import_name}")
            except ImportError as e:
                print(f"  ✗ {import_name}: {e}")
    
    def _detect_test_functions(self):
        """Detect actual test functions in test files"""
        total_test_functions = 0
        
        for test_dir in self.test_directories:
            if not test_dir.exists():
                continue
                
            for test_file in test_dir.glob("test_*.py"):
                try:
                    with open(test_file, 'r') as f:
                        content = f.read()
                    
                    # Count test functions
                    import re
                    test_functions = re.findall(r'def test_\w+', content)
                    test_classes = re.findall(r'class Test\w+', content) 
                    
                    file_test_count = len(test_functions)
                    total_test_functions += file_test_count
                    
                    print(f"  {test_file.name}: {file_test_count} test functions, {len(test_classes)} test classes")
                    
                except Exception as e:
                    print(f"  ✗ {test_file.name}: Error reading file - {e}")
        
        print(f"\n📊 TOTAL TEST FUNCTIONS FOUND: {total_test_functions}")
        print(f"📊 PYTEST DISCOVERED: 0 (MAJOR PROBLEM!)")

if __name__ == "__main__":
    diagnostic = TestDiscoveryDiagnostic()
    diagnostic.diagnose_discovery_issues()
```

### Phase 3B: Fix Test Import Dependencies (Hours 3-5)
```python
# fix_test_imports.py
import os
import sys
from pathlib import Path
import re

class TestImportFixer:
    """Fix import issues preventing test execution"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.fixed_files = []
        self.import_fixes = []
    
    def fix_all_test_imports(self):
        """Fix import issues in all test files"""
        
        test_files = []
        for test_dir in ["tests/unit", "tests/integration", "tests/e2e"]:
            test_path = self.project_root / test_dir
            if test_path.exists():
                test_files.extend(test_path.glob("test_*.py"))
        
        print(f"🔧 Fixing imports in {len(test_files)} test files...")
        
        for test_file in test_files:
            fixes_applied = self._fix_file_imports(test_file)
            if fixes_applied:
                self.fixed_files.append(test_file)
                print(f"  ✓ Fixed: {test_file.name}")
        
        print(f"\n📋 IMPORT FIX SUMMARY:")
        print(f"  Files processed: {len(test_files)}")
        print(f"  Files fixed: {len(self.fixed_files)}")
        print(f"  Import fixes applied: {len(self.import_fixes)}")
    
    def _fix_file_imports(self, file_path: Path) -> bool:
        """Fix imports in a single test file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Fix 1: Add sys.path modifications for project imports
            if "sys.path.insert" not in content and "from nodes." in content:
                sys_path_fix = """
# Fix imports for project modules
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
"""
                # Insert after existing imports
                import_end = self._find_import_section_end(content)
                content = content[:import_end] + sys_path_fix + content[import_end:]
                self.import_fixes.append(f"{file_path.name}: Added sys.path fix")
            
            # Fix 2: Update relative imports to absolute imports
            relative_imports = re.findall(r'from \.\.(\w+)', content)
            for relative_import in relative_imports:
                old_import = f"from ..{relative_import}"
                new_import = f"from {relative_import}"
                content = content.replace(old_import, new_import)
                self.import_fixes.append(f"{file_path.name}: Fixed relative import {relative_import}")
            
            # Fix 3: Add missing pytest imports  
            if "import pytest" not in content and ("@pytest." in content or "pytest." in content):
                content = "import pytest\n" + content
                self.import_fixes.append(f"{file_path.name}: Added missing pytest import")
            
            # Fix 4: Fix Kailash SDK import patterns
            sdk_import_fixes = [
                ("from kailash.workflow.builder import WorkflowBuilder", 
                 "from kailash.workflow.builder import WorkflowBuilder"),
                ("from kailash.runtime.local import LocalRuntime",
                 "from kailash.runtime.local import LocalRuntime"),
                ("from kailash.nodes.base import Node, register_node, NodeParameter",
                 "from kailash.nodes.base import Node, register_node, NodeParameter")
            ]
            
            for old_pattern, new_pattern in sdk_import_fixes:
                if old_pattern.replace("from kailash.", "from ") in content and old_pattern not in content:
                    content = content.replace(old_pattern.replace("from kailash.", "from "), old_pattern)
                    self.import_fixes.append(f"{file_path.name}: Fixed SDK import pattern")
            
            # Save if changes were made
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                return True
            
            return False
            
        except Exception as e:
            print(f"  ✗ Error fixing {file_path.name}: {e}")
            return False
    
    def _find_import_section_end(self, content: str) -> int:
        """Find the end of the import section"""
        lines = content.split('\n')
        import_end = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ')) or stripped.startswith('#') or not stripped:
                import_end = content.find('\n', import_end) + 1
            else:
                break
        
        return import_end
```

### Phase 3C: Repair Pytest Configuration (Hours 6-7)  
```ini
# pytest.ini (Fixed Configuration)
[tool:pytest]
minversion = 6.0
addopts = 
    -ra
    -q
    --strict-markers
    --strict-config
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests (fast, isolated, mocked dependencies)
    integration: Integration tests (real services, databases)  
    e2e: End-to-end tests (complete workflows)
    performance: Performance and benchmark tests
    slow: Tests that take more than 1 second
    windows: Windows-specific tests
    docker: Tests requiring Docker services
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
asyncio_mode = auto
timeout = 30
```

```python
# tests/conftest.py (Comprehensive Test Configuration)
"""
Test configuration and fixtures for the entire test suite.
Provides common fixtures, utilities, and setup for all test tiers.
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock, AsyncMock

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Apply Windows compatibility patch if needed
import platform
if platform.system() == 'Windows':
    try:
        import windows_patch
        windows_patch.apply_patch()
    except ImportError:
        pass  # Patch not available yet

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_workflow_builder():
    """Mock WorkflowBuilder for testing"""
    from kailash.workflow.builder import WorkflowBuilder
    return Mock(spec=WorkflowBuilder)

@pytest.fixture  
def mock_local_runtime():
    """Mock LocalRuntime for testing"""
    from kailash.runtime.local import LocalRuntime
    runtime = Mock(spec=LocalRuntime)
    runtime.execute = AsyncMock(return_value=({}, "test-run-id"))
    return runtime

@pytest.fixture
def sample_node_parameters():
    """Sample NodeParameter definitions for testing"""
    from kailash.nodes.base import NodeParameter
    return [
        NodeParameter(
            name="test_param",
            type="str", 
            required=True,
            description="Test parameter"
        ),
        NodeParameter(
            name="optional_param",
            type="int",
            required=False,
            default=42,
            description="Optional test parameter"
        )
    ]

@pytest.fixture(scope="session")
def test_database_config():
    """Test database configuration"""
    return {
        "postgresql": {
            "host": "localhost",
            "port": 5433,
            "database": "horme_test", 
            "user": "test_user",
            "password": "test_pass"
        },
        "neo4j": {
            "uri": "bolt://localhost:7688",
            "user": "neo4j",
            "password": "test_password"
        },
        "redis": {
            "host": "localhost",
            "port": 6380,
            "db": 0
        }
    }

# Test environment markers
def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    
    config.addinivalue_line(
        "markers", "unit: Unit tests - fast, isolated, mocked dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests - real services and databases"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests - complete workflow scenarios"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and benchmark tests"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location"""
    
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):  
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically setup test environment for each test"""
    
    # Set test environment variables
    os.environ["ENVIRONMENT"] = "test"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    yield
    
    # Cleanup after test
    test_env_vars = ["ENVIRONMENT", "LOG_LEVEL"]
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]
```

## Testing Requirements

### Unit Tests (Immediate Priority)
- [ ] Test discovery mechanism validation
- [ ] Import resolution testing  
- [ ] Pytest configuration verification
- [ ] Test fixture functionality validation

### Integration Tests (Secondary Priority)
- [ ] Real service connection testing
- [ ] Database test environment validation
- [ ] Docker service integration testing
- [ ] Cross-tier test execution validation

### End-to-End Tests (Final Priority)
- [ ] Complete test suite execution
- [ ] Test reporting accuracy validation
- [ ] Performance benchmark testing
- [ ] Full 3-tier strategy validation

## Definition of Done

- [ ] All acceptance criteria met and verified
- [ ] pytest discovers and lists ALL test files correctly  
- [ ] Test execution shows REAL results (not 0 tests run)
- [ ] All tier markers and configurations work properly
- [ ] Import errors completely resolved
- [ ] Test reporting shows accurate pass/fail counts
- [ ] Progress reporting reflects actual test execution status
- [ ] 3-tier testing strategy fully operational with real results

## Validation Commands

```bash
# Test discovery validation
pytest --collect-only -q

# Run unit tests with real results
pytest tests/unit/ -v -m unit

# Run integration tests (after services available)
pytest tests/integration/ -v -m integration  

# Full test suite execution
pytest -v --tb=short

# Coverage reporting
pytest --cov=src --cov-report=term-missing
```

## Progress Tracking

**Phase 3A (Hours 1-2):** [ ] Complete test discovery diagnostic  
**Phase 3B (Hours 3-5):** [ ] Fix all test import dependencies  
**Phase 3C (Hours 6-7):** [ ] Repair pytest configuration  
**Phase 3D (Hours 8-9):** [ ] Establish test environment setup  
**Phase 3E (Hour 10):** [ ] Validate 3-tier test execution  

## Success Metrics

- **Test Discovery Rate**: 100% of test files discovered by pytest
- **Import Success Rate**: 100% of test files import without errors  
- **Test Execution**: >0 tests run (eliminate false 0 test results)
- **Configuration Compliance**: All pytest markers and settings functional
- **Reporting Accuracy**: Real pass/fail counts replace false success claims

## Next Actions After Completion

1. **INFRA-004**: WSL2 + Docker environment (depends on working test infrastructure)
2. **INFRA-005**: SDK registration compliance (needs test validation)
3. **INFRA-007**: Progress validation checkpoints (builds on real test reporting)

This repair is essential for validating all subsequent infrastructure recovery work and eliminating false progress reporting.