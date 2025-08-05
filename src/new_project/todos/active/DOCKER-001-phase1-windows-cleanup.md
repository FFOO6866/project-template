# DOCKER-001-Phase1-Windows-Cleanup

## Description
Phase 1: Complete removal of Windows-specific code, documentation, and infrastructure to prepare for containerized deployment. This phase establishes a clean foundation for Docker migration by eliminating Windows dependencies.

## Acceptance Criteria
- [ ] All Windows SDK compatibility code removed from codebase
- [ ] Windows-specific documentation files deleted and references updated
- [ ] Windows-specific tests removed and test infrastructure cleaned
- [ ] WSL2 and Windows PowerShell scripts archived or removed
- [ ] Cross-platform compatibility assumptions updated
- [ ] All references to Windows-specific paths, registry, and services removed
- [ ] Updated architecture documentation reflects containerized approach
- [ ] Dependency analysis completed with Windows-specific packages identified for removal

## Dependencies
- EXEC-001: Import violations fixed (prerequisite)
- Current active todos involving Windows components must be resolved or archived

## Risk Assessment
- **HIGH**: Removing Windows code may break existing functionality if not properly catalogued
- **MEDIUM**: Documentation references may be scattered throughout the codebase
- **LOW**: Test cleanup should be straightforward with existing test infrastructure

## Subtasks

### Windows Code Removal (Est: 8h)
- [ ] **DOCKER-001-01**: Audit Windows-specific modules (Est: 2h)
  - Scan for imports like `winreg`, `win32api`, `os.path.win` patterns
  - Identify Windows-only conditional code blocks
  - Document dependencies that will be removed
  - Verification: Complete inventory of Windows-specific code

- [ ] **DOCKER-001-02**: Remove Windows SDK compatibility layer (Est: 3h)
  - Delete `src/new_project/windows_sdk_compatibility.py`
  - Remove `src/new_project/windows_patch.py`
  - Delete `src/new_project/windows_resource_compat.py`
  - Update imports in dependent modules
  - Verification: No Windows SDK compatibility imports remain

- [ ] **DOCKER-001-03**: Remove Windows infrastructure setup scripts (Est: 2h)
  - Archive `setup_wsl2_environment.ps1`
  - Remove `setup_windows_infrastructure.py`
  - Delete `quick_fix_windows.bat` and related batch files
  - Remove Windows-specific Docker setup files
  - Verification: No Windows infrastructure scripts in repository

- [ ] **DOCKER-001-04**: Clean up Windows validation and testing utilities (Est: 1h)
  - Remove `validate_windows_compatibility.py`
  - Delete `validate_windows_sdk_compatibility.py`
  - Remove `windows_test_runner.py`
  - Archive Windows-specific validation reports
  - Verification: No Windows validation utilities remain

### Documentation Cleanup (Est: 4h)
- [ ] **DOCKER-001-05**: Remove Windows documentation files (Est: 2h)
  - Delete `WINDOWS_INFRASTRUCTURE_SOLUTIONS.md`
  - Remove `WINDOWS_SDK_COMPATIBILITY_VALIDATION_REPORT.md`
  - Archive `WINDOWS_SDK_VALIDATION_SUMMARY.md`
  - Remove Windows-specific ADR documents
  - Verification: No standalone Windows documentation files

- [ ] **DOCKER-001-06**: Update architecture documentation (Est: 2h)
  - Remove Windows deployment sections from main documentation
  - Update system requirements to reflect containerized approach
  - Update installation instructions to remove Windows-specific steps
  - Add containerization-first approach to architecture docs
  - Verification: Documentation reflects container-first architecture

### Test Infrastructure Cleanup (Est: 6h)
- [ ] **DOCKER-001-07**: Remove Windows-specific tests (Est: 3h)
  - Delete tests with `windows` in filename or test name
  - Remove Windows compatibility test suites
  - Update test configuration to remove Windows test markers
  - Clean up Windows-specific test fixtures and mocks
  - Verification: pytest runs without Windows-specific tests

- [ ] **DOCKER-001-08**: Update test infrastructure configuration (Est: 2h)
  - Remove Windows-specific pytest markers from `pytest.ini`
  - Update test discovery patterns to exclude archived Windows tests
  - Update CI test matrices to remove Windows runners
  - Clean up Windows-specific test dependencies
  - Verification: Test suite runs cleanly without Windows dependencies

- [ ] **DOCKER-001-09**: Archive Windows test results and reports (Est: 1h)
  - Move Windows validation reports to archive directory
  - Compress Windows-specific test result files
  - Update test reporting to remove Windows metrics
  - Clean up Windows-specific test result JSON files
  - Verification: Active test directory contains no Windows artifacts

## Testing Requirements
- [ ] **Unit Tests**: Verify no Windows imports remain in any module
- [ ] **Integration Tests**: Ensure removed Windows code doesn't break cross-platform functionality
- [ ] **Regression Tests**: Run existing test suite to ensure no functionality broken by cleanup

## Definition of Done
- [ ] All Windows-specific code removed from active codebase
- [ ] Documentation updated to reflect containerized deployment approach
- [ ] Test suite runs cleanly without Windows dependencies or references
- [ ] Windows artifacts properly archived for potential future reference
- [ ] Codebase audit confirms no remaining Windows-specific dependencies
- [ ] Architecture documentation reflects container-first approach

## Phase 1 Success Criteria
- **Codebase Cleanliness**: 0 Windows-specific imports or code blocks
- **Documentation Accuracy**: All docs reflect containerized deployment
- **Test Suite Health**: 100% test pass rate without Windows components
- **Dependency Clarity**: Clear inventory of removed Windows dependencies
- **Architecture Alignment**: Documentation and code aligned for containerization

## Next Phase Dependencies
This phase must be completed before Phase 2 containerization can begin effectively, as Windows-specific code may interfere with container deployment patterns.