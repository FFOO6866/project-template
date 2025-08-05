#!/usr/bin/env python3
"""
Simple Test Runner - Standalone execution without external pytest
===============================================================

This runner imports and executes our test cases directly to validate 
SDK compliance without requiring complex test infrastructure.
"""

import sys
import os
import traceback
import time
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent.parent))

# Apply Windows compatibility patch
import platform
if platform.system() == 'Windows':
    import windows_patch

def run_test_function(test_func, test_name):
    """Run a single test function and return results"""
    print(f"Running {test_name}...")
    
    try:
        start_time = time.time()
        
        # Execute the test function
        test_func()
        
        execution_time = time.time() - start_time
        print(f"  PASSED ({execution_time:.3f}s)")
        return {"status": "passed", "time": execution_time, "error": None}
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = str(e)
        print(f"  FAILED ({execution_time:.3f}s): {error_msg}")
        if "NodeParameter" in error_msg or "register_node" in error_msg:
            print(f"    --> SDK compliance violation detected")
        return {"status": "failed", "time": execution_time, "error": error_msg}

def main():
    """Main test execution"""
    print("Simple Test Runner - SDK Compliance Validation")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    errors = []
    
    try:
        # Import our test classes
        from tests.unit.test_classification_nodes_sdk_compliance import (
            TestParameterDefinitionCompliance,
            TestRegisterNodeDecoratorCompliance,
            TestMethodInterfaceCompliance
        )
        
        # Test parameter definition compliance
        print("\n1. Testing Parameter Definition Compliance...")
        param_test = TestParameterDefinitionCompliance()
        
        param_tests = [
            (param_test.test_unspsc_node_uses_node_parameter_objects, "UNSPSC Node Parameter Objects"),
            (param_test.test_etim_node_uses_node_parameter_objects, "ETIM Node Parameter Objects"),
            (param_test.test_dual_classification_node_uses_node_parameter_objects, "Dual Classification Parameter Objects"),
            (param_test.test_no_deprecated_dict_parameter_definitions, "No Deprecated Dict Definitions")
        ]
        
        for test_func, test_name in param_tests:
            result = run_test_function(test_func, test_name)
            total_tests += 1
            if result["status"] == "passed":
                passed_tests += 1
            else:
                failed_tests += 1
                errors.append((test_name, result["error"]))
        
        # Test register_node decorator compliance
        print("\n2. Testing @register_node Decorator Compliance...")
        decorator_test = TestRegisterNodeDecoratorCompliance()
        
        decorator_tests = [
            (decorator_test.test_unspsc_node_has_register_node_decorator, "UNSPSC @register_node Decorator"),
            (decorator_test.test_etim_node_has_register_node_decorator, "ETIM @register_node Decorator"),
            (decorator_test.test_dual_classification_node_has_register_node_decorator, "Dual Classification @register_node Decorator"),
            (decorator_test.test_register_node_decorator_supports_sdk_patterns, "SDK Pattern Support")
        ]
        
        for test_func, test_name in decorator_tests:
            result = run_test_function(test_func, test_name)
            total_tests += 1
            if result["status"] == "passed":
                passed_tests += 1
            else:
                failed_tests += 1
                errors.append((test_name, result["error"]))
        
        # Test method interface compliance
        print("\n3. Testing Method Interface Compliance...")
        interface_test = TestMethodInterfaceCompliance()
        
        interface_tests = [
            (interface_test.test_nodes_implement_run_as_primary_interface, "Primary run() Interface"),
            (interface_test.test_run_method_accepts_dict_inputs, "Dict Input Acceptance"),
            (interface_test.test_run_method_with_minimal_required_params, "Minimal Parameter Handling")
        ]
        
        for test_func, test_name in interface_tests:
            result = run_test_function(test_func, test_name)
            total_tests += 1
            if result["status"] == "passed":
                passed_tests += 1
            else:
                failed_tests += 1
                errors.append((test_name, result["error"]))
    
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Cannot import classification nodes - they may not be properly implemented yet")
        return 1
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        return 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success rate: {(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%")
    
    if errors:
        print(f"\nFAILED TESTS ({len(errors)}):")
        for test_name, error in errors:
            print(f"  - {test_name}: {error}")
        
        print("\nCRITICAL SDK COMPLIANCE VIOLATIONS DETECTED:")
        print("1. Parameter definitions using deprecated dict format instead of NodeParameter objects")
        print("2. Missing @register_node decorators on classification node classes")
        print("3. Method interface compliance issues with run() method")
    
    print("=" * 60)
    
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    sys.exit(main())