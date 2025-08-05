# EXEC-001-Fix-Import-Violations

## Description
Execute automated script to fix the remaining 2 import violations identified by analysis. This is a critical first step that must be completed before infrastructure deployment.

## Acceptance Criteria
- [ ] Execute fix_sdk_imports.py script successfully
- [ ] Verify 0 import violations remaining after fix
- [ ] Confirm all SDK imports are properly resolved
- [ ] Validate compatibility layer (windows_patch.py) remains functional
- [ ] All tests pass without import-related errors

## Dependencies
- NONE - This is the first task in the execution sequence

## Risk Assessment
- **LOW**: Automated fix script already validated by sdk-navigator
- **LOW**: Only 2 violations remaining, well-understood issues
- **MEDIUM**: Must maintain existing windows_patch.py compatibility

## Subtasks
- [ ] Execute import fix script (Est: 15min) - Run python src/new_project/fix_sdk_imports.py
- [ ] Validate fix results (Est: 10min) - Check for remaining violations
- [ ] Test import functionality (Est: 5min) - Quick smoke test of imports

## Testing Requirements
- [ ] Unit tests: Import resolution validation
- [ ] Integration tests: SDK compatibility verification
- [ ] No E2E tests required for this isolated fix

## Commands to Execute
```bash
# Primary execution command
python src/new_project/fix_sdk_imports.py

# Validation command
python -c "import src.new_project.core; print('Imports working')"
```

## Definition of Done
- [ ] fix_sdk_imports.py executed without errors
- [ ] 0 import violations detected in validation
- [ ] All core module imports functional
- [ ] No regression in windows_patch.py functionality
- [ ] Ready to proceed to EXEC-002 (infrastructure deployment)

## Success Metrics
- **Target**: 0 import violations (down from 2)
- **Time**: 30 minutes maximum
- **Validation**: Automated import testing passes
- **Next Step**: EXEC-002 infrastructure deployment enabled