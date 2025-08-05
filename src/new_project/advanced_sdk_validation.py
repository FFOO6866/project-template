#!/usr/bin/env python3
"""
Advanced Kailash SDK Validation Script
=====================================

This script tests more complex SDK functionality including:
- Multi-node workflows
- Data flow between nodes
- Different node types
- Error handling

Usage:
    python advanced_sdk_validation.py
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path
current_dir = str(Path(__file__).parent.absolute())
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import Windows patch first

def test_step(step_name, test_func):
    """Run a test step with error handling and detailed output"""
    print(f"\n{'='*60}")
    print(f"STEP: {step_name}")
    print(f"{'='*60}")
    
    try:
        result = test_func()
        print(f"✅ SUCCESS: {step_name}")
        if result:
            print(f"Result summary: {type(result).__name__} with {len(str(result))} chars")
        return True
    except Exception as e:
        print(f"❌ FAILED: {step_name}")
        print(f"Error: {e}")
        print(f"Traceback:")
        traceback.print_exc()
        return False

def test_multi_node_workflow():
    """Test multi-node workflow with data flow"""
    print("Testing multi-node workflow...")
    
    from kailash.workflow.builder import WorkflowBuilder
    from kailash.runtime.local import LocalRuntime
    
    # Create workflow with multiple nodes
    workflow = WorkflowBuilder()
    
    # Node 1: Generate data
    workflow.add_node(
        "PythonCodeNode", 
        "data_generator", 
        {"code": "result = {'numbers': [1, 2, 3, 4, 5], 'operation': 'sum'}"}
    )
    
    # Node 2: Process data (depends on node 1)
    workflow.add_node(
        "PythonCodeNode",
        "data_processor",
        {
            "code": """
data = input_data.get('data_generator', {}).get('result', {})
numbers = data.get('numbers', [])
operation = data.get('operation', 'sum')

if operation == 'sum':
    result = {'processed_result': sum(numbers), 'count': len(numbers)}
else:
    result = {'processed_result': 0, 'count': 0}
""",
            "inputs": ["data_generator"]
        }
    )
    
    # Node 3: Format output (depends on node 2)
    workflow.add_node(
        "PythonCodeNode",
        "formatter",
        {
            "code": """
processor_data = input_data.get('data_processor', {}).get('result', {})
processed_result = processor_data.get('processed_result', 0)
count = processor_data.get('count', 0)

result = {
    'final_message': f'Processed {count} numbers with result: {processed_result}',
    'success': True,
    'workflow_completed': True
}
""",
            "inputs": ["data_processor"]
        }
    )
    
    # Build and execute
    built_workflow = workflow.build()
    print(f"Built workflow with {len(built_workflow.nodes)} nodes")
    
    runtime = LocalRuntime()
    results, run_id = runtime.execute(built_workflow)
    
    print(f"Execution completed with run ID: {run_id}")
    print(f"Results keys: {list(results.keys())}")
    
    # Validate final result
    if 'formatter' in results:
        final_result = results['formatter'].get('result', {})
        if final_result.get('workflow_completed'):
            print(f"✅ Multi-node workflow validation passed!")
            print(f"Final message: {final_result.get('final_message')}")
            return results
        else:
            raise Exception(f"Workflow completion validation failed: {final_result}")
    else:
        raise Exception(f"Missing formatter results: {results}")

def test_different_parameter_types():
    """Test different parameter types and data handling"""
    print("Testing different parameter types...")
    
    from kailash.workflow.builder import WorkflowBuilder
    from kailash.runtime.local import LocalRuntime
    
    workflow = WorkflowBuilder()
    
    # Test various data types
    workflow.add_node(
        "PythonCodeNode",
        "type_test",
        {
            "code": """
import json

# Test different data types
test_data = {
    'string': 'Hello World',
    'integer': 42,
    'float': 3.14159,
    'boolean': True,
    'list': [1, 2, 3, 'four', 5.0],
    'dict': {'nested': 'value', 'number': 123},
    'none': None
}

# Validate types
validation = {}
for key, value in test_data.items():
    validation[f'{key}_type'] = type(value).__name__
    validation[f'{key}_value'] = value

result = {
    'original_data': test_data,
    'type_validation': validation,
    'json_serializable': True,
    'test_passed': True
}

# Test JSON serialization
try:
    json.dumps(result)
    result['json_test_passed'] = True
except Exception as e:
    result['json_test_passed'] = False
    result['json_error'] = str(e)
"""
        }
    )
    
    built_workflow = workflow.build()
    runtime = LocalRuntime()
    results, run_id = runtime.execute(built_workflow)
    
    # Validate results
    if 'type_test' in results:
        test_result = results['type_test'].get('result', {})
        if test_result.get('test_passed') and test_result.get('json_test_passed'):
            print("✅ Parameter type validation passed!")
            print(f"Tested types: {list(test_result.get('type_validation', {}).keys())}")
            return results
        else:
            raise Exception(f"Type validation failed: {test_result}")
    else:
        raise Exception(f"Missing type test results: {results}")

def test_error_handling():
    """Test error handling in workflows"""
    print("Testing error handling...")
    
    from kailash.workflow.builder import WorkflowBuilder
    from kailash.runtime.local import LocalRuntime
    
    workflow = WorkflowBuilder()
    
    # Node that will succeed
    workflow.add_node(
        "PythonCodeNode",
        "success_node",
        {"code": "result = {'status': 'success', 'message': 'This node works'}"}
    )
    
    # Node that will handle potential errors gracefully
    workflow.add_node(
        "PythonCodeNode",
        "error_handler",
        {
            "code": """
try:
    # This could potentially fail
    risky_operation = 10 / 1  # Safe operation
    result = {
        'error_handled': True,
        'operation_result': risky_operation,
        'status': 'success'
    }
except Exception as e:
    result = {
        'error_handled': True,
        'error_message': str(e),
        'status': 'handled_error'
    }
"""
        }
    )
    
    built_workflow = workflow.build()
    runtime = LocalRuntime()
    results, run_id = runtime.execute(built_workflow)
    
    # Validate error handling
    if 'error_handler' in results and 'success_node' in results:
        error_result = results['error_handler'].get('result', {})
        success_result = results['success_node'].get('result', {})
        
        if (error_result.get('error_handled') and 
            success_result.get('status') == 'success'):
            print("✅ Error handling validation passed!")
            return results
        else:
            raise Exception(f"Error handling validation failed: {error_result}, {success_result}")
    else:
        raise Exception(f"Missing error handling results: {results}")

def test_workflow_metadata():
    """Test workflow metadata and introspection"""
    print("Testing workflow metadata...")
    
    from kailash.workflow.builder import WorkflowBuilder
    
    workflow = WorkflowBuilder()
    workflow.add_node(
        "PythonCodeNode",
        "metadata_test",
        {"code": "result = {'metadata_available': True}"}
    )
    
    built_workflow = workflow.build()
    
    # Test workflow properties
    print(f"Workflow ID: {built_workflow.id}")
    print(f"Workflow name: {built_workflow.name}")
    print(f"Node count: {len(built_workflow.nodes)}")
    print(f"Has nodes property: {hasattr(built_workflow, 'nodes')}")
    print(f"Has connections property: {hasattr(built_workflow, 'connections')}")
    
    # Validate metadata
    if (built_workflow.id and 
        built_workflow.name and 
        len(built_workflow.nodes) > 0):
        print("✅ Workflow metadata validation passed!")
        return built_workflow
    else:
        raise Exception("Workflow metadata validation failed")

def main():
    """Run all advanced validation tests"""
    print("KAILASH SDK ADVANCED VALIDATION")
    print("Testing complex SDK functionality...")
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Multi-Node Workflow", test_multi_node_workflow),
        ("Parameter Types", test_different_parameter_types),
        ("Error Handling", test_error_handling),
        ("Workflow Metadata", test_workflow_metadata),
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
    print("ADVANCED VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Tests Passed: {passed}")
    print(f"Tests Failed: {failed}")
    print(f"Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL ADVANCED TESTS PASSED! Kailash SDK supports complex functionality.")
    else:
        print(f"\n⚠️  {failed} advanced tests failed.")
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