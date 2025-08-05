# FOUND-001: SDK Compliance Foundation

**Created:** 2025-08-01  
**Assigned:** pattern-expert + gold-standards-validator  
**Priority:** 🚨 P1 - CORE PHASE  
**Status:** PENDING  
**Estimated Effort:** 2 hours  
**Due Date:** 2025-08-04 (After GATE 1 passage)

## Description

Implement SDK compliance patterns using exact specifications from sdk-navigator analysis. Focus on adding @register_node decorators to classification nodes and ensuring proper SecureGovernedNode usage. Based on analysis, the core patterns are already working - just need decorator additions.

## Acceptance Criteria

- [ ] All custom nodes use @register_node decorator with proper metadata
- [ ] SecureGovernedNode is properly implemented for nodes handling sensitive data
- [ ] All nodes follow the string-based workflow pattern: `workflow.add_node("NodeName", "id", {})`
- [ ] Node parameter validation follows the 3-method approach (direct, workflow, runtime)
- [ ] All workflow executions use `runtime.execute(workflow.build())` pattern
- [ ] No deprecated node instantiation patterns remain in codebase
- [ ] All tests pass with compliance fixes

## Subtasks

- [ ] Add @register_node decorators to classification nodes (Est: 45min)
  - Verification: Classification nodes in `nodes/classification_nodes.py` have decorators
  - Output: Proper node registration for discovery and validation
- [ ] Implement SecureGovernedNode for data operations (Est: 45min)
  - Verification: Database and API nodes extend SecureGovernedNode
  - Output: Governance compliance for sensitive data handling
- [ ] Validate string-based workflow patterns (Est: 30min)
  - Verification: All workflows use `workflow.add_node("NodeName", "id", {})`
  - Output: Consistent workflow construction patterns

## Dependencies

- No external dependencies
- Must complete before FOUND-002 (Architecture Setup)
- Prerequisite for all AI and data integration tasks

## Risk Assessment

- **HIGH**: Existing sales assistant MCP server may have compliance violations
- **MEDIUM**: Pattern changes might break existing functionality
- **LOW**: Documentation may need updates after fixes

## Technical Implementation Plan

### Phase F1: Classification Node Decorators (45 minutes)
```python
# File: C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\nodes\classification_nodes.py
# Add @register_node decorators to existing classification nodes:

from kailash.core.base import register_node, SecureGovernedNode

@register_node(
    name="UnspscClassificationNode",
    version="1.0.0", 
    description="Classifies items using UNSPSC codes with 170k+ taxonomy",
    category="classification"
)
class UnspscClassificationNode(SecureGovernedNode):
    def __init__(self):
        super().__init__()
        self.required_params = ["item_description", "classification_context"]
    
    def execute(self, item_description: str, classification_context: dict = None):
        # Existing implementation with governance wrapper
        return self._secure_execute(locals())
    
    def _secure_execute(self, params):
        # Add security logging and validation
        self.log_access("UNSPSC classification requested", params)
        # Existing classification logic here
        return {"unspsc_code": "12345678", "confidence": 0.95}

@register_node(
    name="EtimClassificationNode", 
    version="1.0.0",
    description="Classifies items using ETIM classes with 49k+ categories",
    category="classification"
)
class EtimClassificationNode(SecureGovernedNode):
    def __init__(self):
        super().__init__()
        self.required_params = ["item_description", "category_hint"]
```

### Phase F2: SecureGovernedNode Implementation (45 minutes)
```python
# File: C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\core\governance.py
# Extend SecureGovernedNode for database operations:

from kailash.core.governance import SecureGovernedNode
import logging
from datetime import datetime

class DatabaseGovernedNode(SecureGovernedNode):
    """Base class for database operations with governance"""
    
    def __init__(self):
        super().__init__()
        self.audit_logger = logging.getLogger('governance.database')
    
    def log_access(self, operation: str, params: dict):
        """Log database access for governance compliance"""
        self.audit_logger.info({
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'node_type': self.__class__.__name__,
            'params_count': len(params),
            'user_context': self.get_user_context()
        })
    
    def validate_data_access(self, data_type: str) -> bool:
        """Validate user permissions for data access"""
        # Implement governance rules
        return True  # Simplified for development

@register_node(
    name="PostgreSQLQueryNode",
    version="1.0.0", 
    description="Executes PostgreSQL queries with governance",
    category="database"
)
class PostgreSQLQueryNode(DatabaseGovernedNode):
    def execute(self, query: str, params: dict = None):
        self.log_access("PostgreSQL query", {"query": query[:100]})
        return self._secure_execute(query, params)
```

### Phase F3: Workflow Pattern Validation (30 minutes)  
```python
# File: C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\workflows\classification_workflow.py
# Ensure string-based workflow patterns:

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

def create_classification_workflow():
    """Create classification workflow using proper SDK patterns"""
    workflow = WorkflowBuilder()
    
    # ✅ CORRECT: String-based node references
    workflow.add_node("UnspscClassificationNode", "unspsc_classifier", {
        "item_description": "{{ input.description }}",
        "classification_context": "{{ input.context }}"
    })
    
    workflow.add_node("EtimClassificationNode", "etim_classifier", {
        "item_description": "{{ input.description }}",
        "category_hint": "{{ unspsc_classifier.category }}"
    })
    
    # ✅ CORRECT: Always use .build() method
    return workflow.build()

def execute_classification(item_description: str, context: dict = None):
    """Execute classification workflow with proper runtime pattern"""
    workflow_def = create_classification_workflow()
    runtime = LocalRuntime()
    
    # ✅ CORRECT: runtime.execute(workflow.build()) pattern
    results, run_id = runtime.execute(workflow_def, {
        "input": {
            "description": item_description,
            "context": context or {}
        }
    })
    
    return results
```

## Testing Requirements

- [ ] Unit tests: All nodes instantiate correctly with new patterns
- [ ] Integration tests: Existing workflows still function after compliance fixes
- [ ] E2E tests: Sales assistant MCP server still operates correctly

## Implementation Files to Check

- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\sales_assistant_mcp_server.py`
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\dataflow_models.py`
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\nexus_app.py`
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\nodes\`
- `C:\Users\fujif\OneDrive\Documents\GitHub\horme-pov\src\new_project\workflows\`

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Code review completed by senior developer
- [ ] All existing tests pass
- [ ] New compliance tests added and passing
- [ ] Documentation updated with new patterns
- [ ] Gold standards validator approves implementation

## Notes

- Reference sdk-users/2-core-concepts/validation/critical-rules.md for compliance requirements
- Use pattern-expert agent for guidance on proper node implementation patterns
- Check sdk-users/7-gold-standards/ for absolute requirements

## Progress Log

**2025-08-01:** Task created and prioritized as critical foundation work