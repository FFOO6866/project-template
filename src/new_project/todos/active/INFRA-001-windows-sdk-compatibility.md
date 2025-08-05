# INFRA-001: Emergency Windows SDK Compatibility Patch

**Created:** 2025-08-02  
**Assigned:** Infrastructure Recovery Team  
**Priority:** 🚨 P0 - CRITICAL  
**Status:** PENDING  
**Estimated Effort:** 8 hours  
**Due Date:** 2025-08-03 (24-hour emergency fix)

## Description

Deploy immediate Windows compatibility patch to resolve Unix-only resource module issues that are completely blocking all SDK development and testing. This is the first critical infrastructure fix needed to recover from the infrastructure collapse.

## Critical Issues Identified

1. **Unix-only resource module** blocking all SDK imports on Windows
2. **Path separator conflicts** between Unix/Windows file systems  
3. **Library compatibility issues** with Windows-specific modules
4. **Environment variable handling** differences between platforms

## Acceptance Criteria

- [ ] SDK imports work successfully on Windows without errors
- [ ] All core Kailash SDK modules load properly (WorkflowBuilder, LocalRuntime, Nodes)
- [ ] Windows-specific file path handling implemented correctly
- [ ] Environment compatibility layer established
- [ ] Resource module compatibility shim created
- [ ] All existing Windows patch functionality preserved
- [ ] No regression in Unix/Linux compatibility

## Subtasks

- [ ] Analyze Current Windows Patch Implementation (Est: 1h)
  - Verification: Complete audit of existing windows_patch.py functionality
  - Output: List of fixed vs unfixed compatibility issues
- [ ] Identify Unix-only Resource Module Failures (Est: 2h)
  - Verification: Exact import error locations and root causes identified
  - Output: Detailed error mapping with specific module failures
- [ ] Implement Resource Module Compatibility Shim (Est: 3h)
  - Verification: All resource module imports succeed on Windows
  - Output: Platform-agnostic resource handling layer
- [ ] Fix Path Separator and Environment Issues (Est: 1h)
  - Verification: File operations work on both Windows and Unix systems
  - Output: Cross-platform path and env variable handling
- [ ] Validate SDK Core Import Chain (Est: 1h)
  - Verification: Complete Kailash SDK import chain works without errors
  - Output: Successful import of all critical SDK components

## Dependencies

- No external dependencies (critical path priority)
- Must complete before any other infrastructure tasks
- Blocks all development until resolved

## Risk Assessment

- **CRITICAL**: Complete development blockage if not resolved within 24 hours
- **HIGH**: Windows development environment remains unusable
- **MEDIUM**: Potential for introducing Unix compatibility regressions
- **LOW**: Performance impact from compatibility layer overhead

## Technical Implementation Plan

### Phase 1A: Emergency Analysis (Hour 1)
```python
# Immediate diagnostic script
import sys
import traceback

def diagnose_import_failures():
    """Identify specific import failures"""
    critical_imports = [
        'kailash.workflow.builder',
        'kailash.runtime.local', 
        'kailash.nodes.base',
        'kailash.nodes.core'
    ]
    
    failures = []
    for module in critical_imports:
        try:
            __import__(module)
            print(f"✓ {module}")
        except Exception as e:
            failures.append((module, str(e), traceback.format_exc()))
            print(f"✗ {module}: {e}")
    
    return failures
```

### Phase 1B: Resource Module Compatibility Shim (Hours 2-4)
```python
# windows_resource_compat.py
import platform
import os
import sys
from pathlib import Path

class WindowsResourceCompatibility:
    """Windows compatibility layer for Unix-only resource modules"""
    
    def __init__(self):
        self.platform = platform.system()
        self.is_windows = self.platform == 'Windows'
        
    def patch_resource_module(self):
        """Apply compatibility patches for resource module"""
        if not self.is_windows:
            return  # No patching needed on Unix
            
        # Implement Unix resource module equivalents
        self._patch_resource_functions()
        self._patch_file_descriptors()
        self._patch_signal_handling()
    
    def _patch_resource_functions(self):
        """Patch resource module functions for Windows"""
        import resource
        
        # Windows equivalents for Unix resource constants
        if not hasattr(resource, 'RLIMIT_NOFILE'):
            resource.RLIMIT_NOFILE = 7
        if not hasattr(resource, 'RLIMIT_NPROC'):
            resource.RLIMIT_NPROC = 6
            
        # Safe getrlimit/setrlimit implementations
        original_getrlimit = getattr(resource, 'getrlimit', None)
        if not original_getrlimit:
            def safe_getrlimit(resource_type):
                # Return safe defaults for Windows
                return (1024, 1024)  # soft, hard limits
            resource.getrlimit = safe_getrlimit
```

### Phase 1C: Cross-Platform Path Handling (Hour 5)
```python
# cross_platform_paths.py
import os
from pathlib import Path

class CrossPlatformPathHandler:
    """Handle file paths across Windows/Unix systems"""
    
    @staticmethod
    def normalize_path(path_str: str) -> str:
        """Convert paths to platform-appropriate format"""
        return str(Path(path_str).resolve())
    
    @staticmethod
    def ensure_directory_exists(dir_path: str) -> bool:
        """Create directory if it doesn't exist"""
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
```

## Testing Requirements

### Unit Tests (Critical Priority)
- [ ] SDK import chain validation on Windows
- [ ] Resource module compatibility verification
- [ ] Path handling cross-platform tests
- [ ] Environment variable compatibility tests

### Integration Tests (After Unit Tests Pass)
- [ ] WorkflowBuilder instantiation on Windows
- [ ] LocalRuntime execution on Windows  
- [ ] Node registration and discovery on Windows
- [ ] Cross-platform workflow execution

### Validation Tests (Final Verification)
- [ ] Complete development environment functionality
- [ ] No regression in existing Unix compatibility
- [ ] Performance impact assessment
- [ ] Memory usage validation

## Definition of Done

- [ ] All acceptance criteria met and verified
- [ ] SDK imports succeed on Windows without any errors
- [ ] Existing Unix functionality preserved (no regressions)
- [ ] Cross-platform path and resource handling implemented
- [ ] All unit and integration tests passing
- [ ] Documentation updated with Windows-specific setup notes
- [ ] 24-hour emergency timeline met

## Implementation Files

- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\windows_patch.py` (extend existing)
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\windows_resource_compat.py` (new)
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\cross_platform_paths.py` (new)
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\tests\unit\test_windows_compatibility.py` (new)

## Validation Script

```python
# validate_windows_compatibility.py
def validate_infrastructure_recovery():
    """Validate that Windows SDK compatibility is fully restored"""
    
    checks = [
        ("SDK Imports", test_sdk_imports),
        ("Resource Compatibility", test_resource_compatibility), 
        ("Path Handling", test_path_handling),
        ("Environment Setup", test_environment_setup)
    ]
    
    results = {}
    for check_name, check_function in checks:
        try:
            result = check_function()
            results[check_name] = {"status": "PASS", "details": result}
            print(f"✓ {check_name}: PASS")
        except Exception as e:
            results[check_name] = {"status": "FAIL", "error": str(e)}
            print(f"✗ {check_name}: FAIL - {e}")
    
    return results

if __name__ == "__main__":
    print("Windows SDK Compatibility Validation")
    print("=" * 50)
    results = validate_infrastructure_recovery()
    
    total_checks = len(results)
    passed_checks = sum(1 for r in results.values() if r["status"] == "PASS")
    
    print(f"\nResults: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("🎉 Windows SDK compatibility fully restored!")
        exit(0)
    else:
        print("❌ Infrastructure recovery incomplete")
        exit(1)
```

## Progress Tracking

**Phase 1A (Hour 1):** [ ] Analysis and diagnostic completion  
**Phase 1B (Hours 2-4):** [ ] Resource module compatibility implementation  
**Phase 1C (Hour 5):** [ ] Cross-platform path handling  
**Phase 1D (Hours 6-7):** [ ] Testing and validation  
**Phase 1E (Hour 8):** [ ] Documentation and final verification  

## Success Metrics

- **Import Success Rate**: 100% for all critical SDK modules
- **Cross-Platform Compatibility**: No regressions on Unix systems
- **Performance Impact**: <5% overhead from compatibility layer
- **Test Coverage**: 100% of Windows-specific compatibility features

## Next Actions After Completion

1. **INFRA-002**: Fix NodeParameter violations (depends on working SDK imports)
2. **INFRA-003**: Repair test infrastructure (depends on SDK compatibility)
3. **INFRA-004**: Deploy WSL2 + Docker environment (depends on base functionality)

This task is the critical foundation for all subsequent infrastructure recovery work.