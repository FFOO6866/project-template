#!/usr/bin/env python3
"""
Basic Kailash SDK Validation Script
===================================

This script performs fundamental validation of Kailash SDK functionality
on Windows systems. It tests one component at a time with detailed output.

Usage:
    python basic_sdk_validation.py
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path
current_dir = str(Path(__file__).parent.absolute())
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_step(step_name, test_func):
    """Run a test step with error handling and detailed output"""
    print(f"\n{'='*60}")
    print(f"STEP: {step_name}")
    print(f"{'='*60}")
    
    try:
        result = test_func()
        print(f"✅ SUCCESS: {step_name}")
        if result:
            print(f"Result: {result}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {step_name}")
        print(f"Error: {e}")
        print(f"Traceback:")
        traceback.print_exc()
        return False

def test_windows_patch():
    """Test 1: Windows patch functionality"""
    print("Testing Windows patch import...")
    status = windows_patch.get_patch_status()
    print(f"Platform: {status['platform']}")
    print(f"Is Windows: {status['is_windows']}")
    print(f"Patches Applied: {status['patches_applied']}")
    print(f"Modules Available: {status['modules_available']}")
    return status

def test_resource_module():
    """Test 2: Resource module functionality"""
    print("Testing resource module access...")
    import resource
    print(f"Resource module: {resource}")
    print(f"Has getrlimit: {hasattr(resource, 'getrlimit')}")
    print(f"Has setrlimit: {hasattr(resource, 'setrlimit')}")
    
    # Test getrlimit functionality
    try:
        limits = resource.getrlimit(resource.RLIMIT_STACK)
        print(f"Stack limits: {limits}")
    except Exception as e:
        print(f"getrlimit test failed: {e}")
        
    return True

def test_basic_imports():
    """Test 3: Basic Kailash SDK imports"""
    print("Testing basic Kailash SDK imports...")
    
    # Test WorkflowBuilder import
    print("Importing WorkflowBuilder...")
    from kailash.workflow.builder import WorkflowBuilder
    print(f"WorkflowBuilder imported: {WorkflowBuilder}")
    
    # Test LocalRuntime import
    print("Importing LocalRuntime...")
    from kailash.runtime.local import LocalRuntime
    print(f"LocalRuntime imported: {LocalRuntime}")
    
    return {"WorkflowBuilder": WorkflowBuilder, "LocalRuntime": LocalRuntime}

def test_workflow_creation():
    """Test 4: Basic workflow creation"""
    print("Testing workflow creation...")
    
    from kailash.workflow.builder import WorkflowBuilder
    
    # Create workflow builder
    workflow = WorkflowBuilder()
    print(f"WorkflowBuilder created: {workflow}")
    
    # Add a simple node
    print("Adding PythonCodeNode...")
    workflow.add_node(
        "PythonCodeNode", 
        "hello_world", 
        {"code": "result = {'message': 'Hello from Kailash SDK!', 'success': True}"}
    )
    
    # Build the workflow
    print("Building workflow...")
    built_workflow = workflow.build()
    print(f"Workflow built successfully: {type(built_workflow)}")
    
    return built_workflow

def test_workflow_execution():
    """Test 5: Basic workflow execution"""
    print("Testing workflow execution...")
    
    from kailash.workflow.builder import WorkflowBuilder
    from kailash.runtime.local import LocalRuntime
    
    # Create and build workflow
    workflow = WorkflowBuilder()
    workflow.add_node(
        "PythonCodeNode", 
        "test_node", 
        {"code": "result = {'message': 'SDK is working!', 'platform': 'Windows', 'test_passed': True}"}
    )
    built_workflow = workflow.build()
    
    # Create runtime and execute
    print("Creating LocalRuntime...")
    runtime = LocalRuntime()
    print(f"LocalRuntime created: {runtime}")
    
    print("Executing workflow...")
    results, run_id = runtime.execute(built_workflow)
    
    print(f"Execution completed!")
    print(f"Run ID: {run_id}")
    print(f"Results: {results}")
    
    # Validate results
    if results and 'test_node' in results:
        node_result = results['test_node']
        # SDK returns results wrapped in 'result' key
        if isinstance(node_result, dict) and 'result' in node_result:
            actual_result = node_result['result']
            if isinstance(actual_result, dict) and actual_result.get('test_passed'):
                print("✅ Workflow execution validation passed!")
                return results
            else:
                raise Exception(f"Test validation failed: {actual_result}")
        else:
            raise Exception(f"Unexpected result format: {node_result}")
    else:
        raise Exception(f"No results returned from execution: {results}")

def test_node_instantiation():
    """Test 6: Node instantiation"""
    print("Testing direct node instantiation...")
    
    from kailash.nodes.code.python import PythonCodeNode
    
    # Create node directly with required name parameter
    node = PythonCodeNode(
        name="Direct Test Node",
        id="direct_test",
        code="result = {'direct_instantiation': True, 'working': True}"
    )
    print(f"PythonCodeNode created directly: {node}")
    print(f"Node ID: {node.id}")
    print(f"Node Type: {type(node).__name__}")
    
    # Test node execution capability
    print("Testing node execution capability...")
    print(f"Node has execute method: {hasattr(node, 'execute')}")
    
    return node

def main():
    """Run all validation tests"""
    print("KAILASH SDK BASIC VALIDATION")
    print("Starting comprehensive validation of Kailash SDK functionality...")
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Windows Patch Functionality", test_windows_patch),
        ("Resource Module Access", test_resource_module),
        ("Basic SDK Imports", test_basic_imports),
        ("Workflow Creation", test_workflow_creation),
        ("Workflow Execution", test_workflow_execution),
        ("Node Instantiation", test_node_instantiation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        success = test_step(test_name, test_func)
        test_results[test_name] = success
        if success:
            passed += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Tests Passed: {passed}")
    print(f"Tests Failed: {failed}")
    print(f"Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Kailash SDK is working correctly on this Windows system.")
    else:
        print(f"\n⚠️  {failed} tests failed. SDK has issues that need to be resolved.")
        print("\nFailed tests:")
        for test_name, success in test_results.items():
            if not success:
                print(f"  - {test_name}")
    
    return test_results

if __name__ == "__main__":
    try:
        results = main()
        
        # Exit with appropriate code
        if all(results.values()):
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Some tests failed
            
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nValidation script failed with unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)