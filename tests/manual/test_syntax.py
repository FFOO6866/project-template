#!/usr/bin/env python3
"""Test syntax structure"""

def test_node_structure():
    from kailash.workflow.builder import WorkflowBuilder
    
    workflow = WorkflowBuilder()
    
    # Test node 1
    workflow.add_node("PythonCodeNode", "test1", {
        "code": """
def test_function():
    return {'result': 'test'}

result = test_function()
"""
    })
    
    # Test node 2
    workflow.add_node("PythonCodeNode", "test2", {
        "code": """
def another_test():
    return {'value': 42}

result = another_test()
"""
    })
    
    return workflow

if __name__ == "__main__":
    try:
        workflow = test_node_structure()
        print("Syntax test passed!")
    except Exception as e:
        print(f"Syntax error: {e}")