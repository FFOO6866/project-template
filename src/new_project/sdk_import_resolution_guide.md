# SDK Import Resolution Guide

## CRITICAL IMPORT FAILURES IDENTIFIED

### 1. Windows Resource Module Issue
**Status**: ✅ RESOLVED  
**Solution**: Use `windows_sdk_compatibility.py` as the first import

### 2. BaseNode Import Errors  
**Status**: ❌ CRITICAL - Multiple files using wrong imports  
**Error**: `ImportError: cannot import name 'BaseNode' from 'kailash.nodes.base'`

**Wrong Pattern**:
```python
from kailash.nodes.base import BaseNode  # DOES NOT EXIST
```

**Correct Pattern**:
```python
from kailash.nodes.base import Node  # CORRECT
```

### 3. SecureGovernedNode Import Errors
**Status**: ❌ CRITICAL - Custom class imported from wrong location  
**Error**: `ImportError: cannot import name 'SecureGovernedNode' from 'kailash.nodes.base'`

**Wrong Pattern**:
```python
from kailash.nodes.base import SecureGovernedNode  # CUSTOM CLASS, NOT SDK
```

**Correct Pattern**:
```python
from src.new_project.nodes.sdk_compliance import SecureGovernedNode  # CUSTOM CLASS
```

## WORKING SDK IMPORT PATTERNS

### Method 1: Windows Compatibility + Core SDK
```python
# Step 1: Apply Windows compatibility FIRST
import windows_sdk_compatibility  # Must be first!

# Step 2: Import core SDK components
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Step 3: Import base classes (CORRECT names)
from kailash.nodes.base import Node, NodeParameter, register_node

# Step 4: Import specific nodes
from kailash.nodes.code import PythonCodeNode
from kailash.nodes.data import CSVReaderNode, JSONReaderNode
from kailash.nodes.ai import LLMAgentNode

# Step 5: Import custom classes from project
from src.new_project.nodes.sdk_compliance import SecureGovernedNode
```

### Method 2: Direct SDK (if compatibility already applied)
```python
# For files where compatibility is already global
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from kailash.nodes.base import Node, NodeParameter  # CORRECT
from src.new_project.nodes.sdk_compliance import SecureGovernedNode
```

## EXECUTION PATTERNS

### ✅ CORRECT Execution Pattern
```python
workflow = WorkflowBuilder()
workflow.add_node("PythonCodeNode", "node_id", {"code": "result = {'value': 42}"})

runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())  # ALWAYS .build()
```

### ❌ WRONG Patterns (Will Fail)
```python
# Wrong: Missing .build()
results = runtime.execute(workflow)

# Wrong: Backwards execution
results = workflow.execute(runtime)

# Wrong: Using class instances instead of strings
workflow.add_node(PythonCodeNode(), "node_id", {})
```

## FILES REQUIRING FIXES

### Critical Import Fixes Needed:
1. `tests/integration/test_sdk_compliance_integration.py:37`
2. `tests/e2e/test_sdk_compliance_e2e.py:41`
3. Multiple TODO files under `todos/active/`

### Fix Command:
```bash
# Replace BaseNode imports
find . -name "*.py" -exec sed -i 's/from kailash.nodes.base import BaseNode/from kailash.nodes.base import Node/g' {} \;

# Replace SecureGovernedNode imports  
find . -name "*.py" -exec sed -i 's/from kailash.nodes.base import.*SecureGovernedNode/from src.new_project.nodes.sdk_compliance import SecureGovernedNode/g' {} \;
```

## DEPENDENCY INSTALLATION

### Missing Dependencies (from test failures):
```bash
pip install neo4j
pip install chromadb
```

## VALIDATION COMMANDS

### Test SDK imports work:
```bash
python -c "import windows_sdk_compatibility; from kailash.workflow.builder import WorkflowBuilder; print('SUCCESS')"
```

### Test basic workflow execution:
```bash
python windows_sdk_compatibility.py
```

## COMMON MISTAKES TO AVOID

1. **Never import** `BaseNode` (doesn't exist)
2. **Never import** `SecureGovernedNode` from `kailash.nodes.base` (it's custom)
3. **Always use** string-based node API: `"PythonCodeNode"` not `PythonCodeNode()`
4. **Always call** `workflow.build()` before execution
5. **Always apply** Windows compatibility patch first on Windows

## IMPLEMENTATION PRIORITY

1. **HIGH**: Fix BaseNode → Node imports across all files
2. **HIGH**: Fix SecureGovernedNode import locations
3. **MEDIUM**: Install missing dependencies (neo4j, chromadb)
4. **MEDIUM**: Apply Windows compatibility patch globally
5. **LOW**: Update documentation with correct patterns

## SUCCESS CRITERIA

- [ ] `python -c "from kailash.workflow.builder import WorkflowBuilder; print('SUCCESS')"` works
- [ ] `python windows_sdk_compatibility.py` shows all green
- [ ] Basic test execution succeeds without import errors
- [ ] All files use correct import patterns (Node not BaseNode)
- [ ] Custom classes imported from correct locations