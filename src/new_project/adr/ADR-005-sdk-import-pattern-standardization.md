# ADR-005: SDK Import Pattern Standardization

## Status
**Accepted** - Critical for test infrastructure recovery

## Context

The project has critical SDK import violations that are preventing 100% of integration and E2E tests from executing. Analysis reveals inconsistent import patterns using non-existent `BaseNode` instead of the correct `Node` class from the Kailash SDK.

### Problems Identified
1. **Import Failures**: Tests failing with `ImportError: cannot import name 'BaseNode' from 'kailash.nodes.base'`
2. **Inconsistent Patterns**: Mixed usage of `BaseNode` (incorrect) vs `Node` (correct) throughout codebase
3. **Windows Compatibility**: SDK requires `windows_patch` before imports on Windows
4. **Custom Class Confusion**: `SecureGovernedNode` incorrectly imported from SDK instead of local implementation

### Requirements and Constraints
- Must maintain compatibility with Kailash SDK patterns
- Must work on Windows development environment
- Must not break existing working code
- Must enable complete test infrastructure recovery
- Must follow SDK's 3-method parameter pattern

## Decision

**Standardize on correct Kailash SDK import patterns with Windows compatibility integration.**

### Core Import Pattern
```python
# Windows compatibility (must be first)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import windows_patch  # Apply Windows compatibility for Kailash SDK

# Standard SDK imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from kailash.nodes.base import Node, NodeParameter, register_node

# Custom implementations
from src.new_project.nodes.sdk_compliance import SecureGovernedNode
```

### Node Implementation Pattern
```python
@register_node()
class CustomNode(Node):  # Use Node, not BaseNode
    def get_parameters(self) -> Dict[str, NodeParameter]:
        return {
            "param_name": NodeParameter(
                name="param_name", 
                type=str, 
                required=True
            )
        }
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation here
        return {"output": "result"}
```

### Key Components and Integration Points

#### 1. Import Resolution Strategy
- **Primary Pattern**: Always import `Node` from `kailash.nodes.base`
- **Custom Extensions**: Import `SecureGovernedNode` from local implementation
- **Windows Support**: Apply `windows_patch` before any SDK imports
- **Error Prevention**: Never import `BaseNode` (does not exist in SDK)

#### 2. Node Inheritance Hierarchy
```
SDK Node (base class)
    ↳ SecureGovernedNode (custom implementation)
        ↳ Custom business nodes
```

#### 3. Parameter Validation Integration
- Use SDK's `NodeParameter` class
- Follow 3-method parameter pattern
- Integrate with custom validation in `SecureGovernedNode`

## Consequences

### Positive
- **Test Infrastructure Recovery**: All import errors resolved, enabling test execution
- **SDK Compliance**: Full alignment with Kailash SDK patterns
- **Windows Compatibility**: Reliable SDK imports on Windows development environment
- **Consistency**: Single standardized import pattern across entire codebase
- **Maintainability**: Clear separation between SDK components and custom implementations
- **Extensibility**: Proper foundation for additional custom nodes

### Negative
- **Migration Effort**: Requires systematic find-and-replace across multiple files
- **Breaking Changes**: Code using `BaseNode` will need updates
- **Dependency on Patch**: Windows development requires `windows_patch` import
- **Documentation Debt**: All documentation examples need updates
- **Testing Overhead**: Need comprehensive validation of all import fixes

### Technical Debt Incurred
- Windows compatibility patch requirement
- Need to maintain import order (windows_patch first)
- Custom SecureGovernedNode implementation maintenance

## Alternatives Considered

### Option 1: Create BaseNode Alias
```python
# Rejected approach
from kailash.nodes.base import Node
BaseNode = Node  # Create alias
```

**Pros**: Minimal code changes required  
**Cons**: 
- Perpetuates confusion between SDK and custom patterns
- Hides the actual SDK structure from developers
- Creates maintenance burden with unnecessary aliases
- Does not address root cause of pattern inconsistency

**Why Rejected**: Creates technical debt without solving the underlying pattern confusion

### Option 2: Fork SDK to Add BaseNode
**Pros**: Would make current imports work  
**Cons**: 
- Massive maintenance overhead
- Breaks SDK upgrade path
- Not aligned with SDK design principles
- Introduces unnecessary complexity

**Why Rejected**: Violates principle of working with SDK, not against it

### Option 3: Custom Node Framework
**Pros**: Complete control over implementation  
**Cons**: 
- Loses SDK ecosystem benefits
- Massive development effort
- Reinvents solved problems
- No community support

**Why Rejected**: Contradicts goal of leveraging Kailash SDK capabilities

## Implementation Plan

### Phase 1: Critical Import Fixes (1-2 days)
1. **Systematic Find-and-Replace**
   - Replace `from kailash.nodes.base import BaseNode` → `from kailash.nodes.base import Node`
   - Replace `class CustomNode(BaseNode):` → `class CustomNode(Node):`
   - Update `BaseNode = Node` aliases → Remove and use `Node` directly

2. **SecureGovernedNode Import Fixes**
   - Replace `from kailash.nodes.base import SecureGovernedNode` → `from src.new_project.nodes.sdk_compliance import SecureGovernedNode`
   - Verify local SecureGovernedNode implementation completeness

3. **Windows Compatibility Integration**
   - Add `import windows_patch` before SDK imports in all test files
   - Validate import resolution works correctly

### Phase 2: Validation and Testing (1 day)
1. **Import Resolution Testing**
   - Test all imports resolve without errors
   - Validate Windows compatibility across all files
   - Check for any remaining BaseNode references

2. **Integration Test Recovery**
   - Run integration tests with real Docker infrastructure
   - Validate custom node functionality
   - Test parameter validation patterns

### Phase 3: Documentation and Standards (1 day)
1. **Code Example Updates**
   - Update all documentation with correct patterns
   - Fix todo files and markdown examples
   - Create import pattern guidelines

2. **Compliance Validation**
   - Run full test suite
   - Validate SDK compliance
   - Performance testing

## Validation Criteria

### Functional Validation
- [ ] All Python files import successfully without errors
- [ ] Integration tests pass with real infrastructure
- [ ] E2E tests complete full workflows
- [ ] Custom nodes work with SDK patterns

### Technical Validation
- [ ] Import resolution time <100ms per file
- [ ] No BaseNode references remain in codebase
- [ ] Windows compatibility maintained
- [ ] Parameter validation follows 3-method pattern

### Business Validation
- [ ] Complete test infrastructure recovery
- [ ] Developer productivity restored
- [ ] Foundation ready for feature development
- [ ] SDK upgrade path preserved

## Monitoring and Review

### Success Metrics
- **Test Infrastructure**: 100% recovery of integration/E2E test execution
- **Import Errors**: Zero import failures across all Python files
- **Performance**: Import resolution within performance targets
- **Developer Experience**: Clear, consistent patterns for all developers

### Review Points
- **Immediate**: After each phase completion
- **Short-term**: Weekly review of pattern adherence
- **Long-term**: Quarterly SDK upgrade compatibility review

## Related Decisions
- **ADR-001**: Windows Development Environment Strategy
- **ADR-004**: Test Infrastructure Recovery Architecture
- **Future ADR**: Custom Node Development Guidelines

---

**Decision Date**: 2025-08-02  
**Review Date**: 2025-08-16 (2 weeks)  
**Next Review**: 2025-11-02 (Quarterly)