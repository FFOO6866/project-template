# Requirements Analysis: Custom Node Compliance Implementation

## Executive Summary

**Feature**: Custom Node Compliance Implementation  
**Complexity**: Medium (24/40 based on ultrathink-analyst assessment)  
**Risk Level**: High (3 critical risks identified)  
**Estimated Effort**: 5-7 days  
**Impact**: Complete test infrastructure recovery (currently 100% integration/E2E tests failing)

## Problem Statement

Critical SDK import violations are preventing all integration and E2E tests from executing, blocking validation of the entire test infrastructure. The primary issue is incorrect import patterns using non-existent `BaseNode` instead of the correct `Node` import from the Kailash SDK.

## Functional Requirements Matrix

| Requirement | Description | Input | Output | Business Logic | Edge Cases | SDK Mapping |
|-------------|-------------|-------|---------|----------------|------------|-------------|
| REQ-001 | Correct SDK Imports | Python import statements | Valid SDK imports | Import `Node` not `BaseNode` | Missing SDK, Windows compatibility | `from kailash.nodes.base import Node` |
| REQ-002 | SecureGovernedNode Implementation | Custom node requirements | Working custom node class | Extend `Node` class correctly | Missing methods, parameter validation | Custom class in `nodes/sdk_compliance.py` |
| REQ-003 | Parameter Validation | Node parameters | Validated parameters | 3-method parameter pattern | Type errors, missing params | `NodeParameter` declarations |
| REQ-004 | Test Infrastructure Recovery | Test files | Passing tests | Correct imports and dependencies | Import errors, missing deps | Test file corrections |
| REQ-005 | Windows Compatibility | Windows environment | Working SDK | Apply windows_patch before imports | Resource module missing | `import windows_patch` |

## Non-Functional Requirements

### Performance Requirements
- Import resolution: <100ms per file
- Test execution: Integration <5s, E2E <10s per test
- Memory usage: <512MB per test process

### Security Requirements
- SecureGovernedNode: Sensitive data sanitization
- Audit logging: All parameter validation events
- Error handling: No sensitive data in error messages

### Scalability Requirements
- Test parallel execution: Support pytest-xdist
- Node registry: Handle 100+ custom nodes
- Parameter validation: <10ms per validation

## User Journey Mapping

### Developer Journey: Test Infrastructure Recovery
1. **Current State**: 100% integration/E2E tests failing with import errors
2. **Import Fixes** → Correct `Node` imports, apply Windows compatibility
3. **Custom Node Validation** → Verify SecureGovernedNode implementation
4. **Test Execution** → All tests pass with real infrastructure
5. **Success State**: Full test coverage with validated SDK compliance

**Success Criteria**:
- All import statements resolve correctly
- Integration tests pass with real infrastructure (Docker services)
- E2E tests complete full user workflows
- No test failures due to import violations

**Failure Points**:
- Incorrect import patterns persist
- Windows compatibility issues
- Missing dependencies for test infrastructure
- Custom node implementation errors

## Risk Assessment Matrix

### High Probability, High Impact (Critical)
1. **Import Pattern Inconsistency** (Risk Level: Critical)
   - **Issue**: Mixed usage of `BaseNode` vs `Node` throughout codebase
   - **Mitigation**: Systematic find-and-replace with validation
   - **Prevention**: Use pattern-expert for SDK compliance review

2. **Windows SDK Compatibility** (Risk Level: Critical)
   - **Issue**: `resource` module not available on Windows
   - **Mitigation**: Apply `windows_patch` before any SDK imports
   - **Prevention**: Standardize Windows compatibility pattern

3. **Test Infrastructure Dependencies** (Risk Level: Critical)
   - **Issue**: Missing dependencies (neo4j, chromadb) causing test failures
   - **Mitigation**: Complete dependency installation process
   - **Prevention**: Automated dependency validation

### Medium Risk (Monitor)
1. **Custom Node Implementation** (Risk Level: Medium)
   - **Issue**: SecureGovernedNode may not implement all required methods
   - **Mitigation**: Validate against SDK Node interface
   - **Prevention**: Use SDK compliance patterns

2. **Parameter Validation Complexity** (Risk Level: Medium)
   - **Issue**: 3-method parameter pattern may be incorrectly implemented
   - **Mitigation**: Follow SDK parameter guidelines exactly
   - **Prevention**: Integration tests with real parameters

## Integration with Existing SDK

### Current Architecture Analysis

#### Correct SDK Patterns (Working)
```python
# ✅ CORRECT: Use these patterns
from kailash.nodes.base import Node, NodeParameter, register_node
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

@register_node()
class CustomNode(Node):
    def get_parameters(self):
        return {"param": NodeParameter(name="param", type=str, required=True)}
```

#### Violation Patterns (Failing)
```python
# ❌ INCORRECT: These patterns cause failures
from kailash.nodes.base import BaseNode  # Does not exist
from kailash.nodes.base import SecureGovernedNode  # Custom class, not SDK

class CustomNode(BaseNode):  # BaseNode undefined
    pass
```

### Reusable Components Analysis

#### Can Reuse Directly
- `Node` base class from SDK
- `NodeParameter` for parameter definitions
- `register_node` decorator
- `WorkflowBuilder` and `LocalRuntime`

#### Need Modification
- Test files with incorrect imports
- Documentation with BaseNode references
- Todo files with incorrect code examples

#### Must Build New
- SecureGovernedNode (already implemented in `nodes/sdk_compliance.py`)
- Enhanced parameter validation
- Windows compatibility integration

## Implementation Roadmap

### Phase 1: Critical Import Fixes (1-2 days)
**Objective**: Fix all import violations blocking tests

1. **Find and Replace BaseNode Imports**
   - Replace `from kailash.nodes.base import BaseNode` with `from kailash.nodes.base import Node`
   - Update all class definitions using `BaseNode` to use `Node`
   - Apply Windows compatibility pattern where needed

2. **SecureGovernedNode Import Fix**
   - Change `from kailash.nodes.base import SecureGovernedNode` to `from src.new_project.nodes.sdk_compliance import SecureGovernedNode`
   - Verify SecureGovernedNode implementation is complete

3. **Windows Compatibility Integration**
   - Ensure `import windows_patch` precedes all SDK imports
   - Test import resolution on Windows environment

### Phase 2: Test Infrastructure Recovery (2-3 days)
**Objective**: Restore full test infrastructure functionality

1. **Missing Dependencies Installation**
   - Install neo4j, chromadb, and other missing test dependencies
   - Update requirements-test.txt with complete dependency list
   - Validate Docker services for integration tests

2. **Test Execution Validation**
   - Run integration tests with real infrastructure
   - Execute E2E tests with complete workflows
   - Validate pytest configuration and markers

3. **Parameter Validation Testing**
   - Test 3-method parameter patterns
   - Validate NodeParameter declarations
   - Test workflow execution with custom nodes

### Phase 3: Compliance Validation (1-2 days)
**Objective**: Ensure complete SDK compliance

1. **SDK Compliance Audit**
   - Validate all custom nodes follow SDK patterns
   - Test parameter passing methods
   - Verify workflow execution patterns

2. **Performance Validation**
   - Test import resolution performance
   - Validate test execution times
   - Check memory usage compliance

3. **Documentation Updates**
   - Update all code examples with correct patterns
   - Fix documentation references to BaseNode
   - Update README and guides

## Architecture Decision Record

See: [ADR-005: SDK Import Pattern Standardization](./adr/ADR-005-sdk-import-pattern-standardization.md)

## Success Criteria

### Functional Success Criteria
- [ ] All import statements resolve without errors
- [ ] Integration tests pass with real Docker infrastructure
- [ ] E2E tests complete full user workflow scenarios
- [ ] Custom nodes implement correct SDK patterns
- [ ] Parameter validation works with 3-method pattern

### Technical Success Criteria
- [ ] Import resolution time <100ms per file
- [ ] Test execution times meet performance targets
- [ ] Memory usage stays within bounds
- [ ] Windows compatibility maintained throughout

### Business Success Criteria
- [ ] Complete test infrastructure recovery
- [ ] Developer productivity restored
- [ ] SDK compliance validated
- [ ] Foundation ready for feature development

## Next Steps

1. **Immediate Action**: Use sdk-navigator to find correct import patterns
2. **Implementation**: Apply systematic find-and-replace for import violations
3. **Validation**: Run test suite to verify fixes
4. **Documentation**: Update all references to correct patterns

## File Mapping for Implementation

### Files Requiring Import Fixes
- `tests/unit/test_sdk_compliance_foundation.py` - Remove BaseNode alias
- `tests/integration/test_sdk_compliance_integration.py` - Fix SecureGovernedNode import
- `tests/e2e/test_sdk_compliance_e2e.py` - Fix SecureGovernedNode import
- `todos/active/AI-001-custom-classification-workflows.md` - Update code examples

### Files Providing Correct Patterns
- `nodes/sdk_compliance.py` - SecureGovernedNode implementation
- `windows_patch.py` - Windows compatibility solution
- Working test files - Reference for correct import patterns

This analysis provides the foundation for systematic implementation of SDK compliance fixes and complete test infrastructure recovery.