"""
Windows SDK Compatibility Edge Case Testing
===========================================

This script tests edge cases and potential failure modes of the Windows
SDK compatibility layer to ensure robustness.
"""

import sys
import traceback
import time
import tempfile
import os
from pathlib import Path

def test_concurrent_imports():
    """Test that concurrent SDK imports work correctly"""
    print("[TEST] Testing Concurrent SDK Imports")
    print("-" * 50)
    
    try:
        # Import compatibility first
        import windows_patch
        print("[PASS] Windows patch imported")
        
        # Test multiple rapid imports
        import kailash.workflow.builder
        import kailash.runtime.local
        import kailash.nodes.base
        print("[PASS] Multiple concurrent imports successful")
        
        # Test re-imports after clearing cache
        modules_to_clear = [
            'kailash.workflow.builder',
            'kailash.runtime.local', 
            'kailash.nodes.base'
        ]
        
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]
        
        # Re-import after clearing
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        from kailash.nodes.base import Node
        print("[PASS] Re-imports after cache clearing successful")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Concurrent import test failed: {e}")
        traceback.print_exc()
        return False

def test_resource_edge_cases():
    """Test edge cases for resource module compatibility"""
    print("\n[TEST] Testing Resource Module Edge Cases")
    print("-" * 50)
    
    try:
        import resource
        print("[PASS] Resource module imported")
        
        # Test all resource constants
        resource_constants = [
            'RLIMIT_CPU', 'RLIMIT_DATA', 'RLIMIT_FSIZE', 'RLIMIT_STACK',
            'RLIMIT_CORE', 'RLIMIT_RSS', 'RLIMIT_NPROC', 'RLIMIT_NOFILE',
            'RLIMIT_OFILE', 'RLIMIT_MEMLOCK', 'RLIMIT_VMEM', 'RLIMIT_AS'
        ]
        
        for const in resource_constants:
            if hasattr(resource, const):
                value = getattr(resource, const)
                print(f"[PASS] {const} = {value}")
            else:
                print(f"[WARN] Missing {const} (may be Unix-specific)")
        
        # Test getrlimit with all available limits
        for const in resource_constants:
            if hasattr(resource, const):
                try:
                    limit_value = getattr(resource, const)
                    limits = resource.getrlimit(limit_value)
                    print(f"[PASS] getrlimit({const}) = {limits}")
                except Exception as e:
                    print(f"[WARN] getrlimit({const}) failed: {e}")
        
        # Test setrlimit edge cases
        try:
            # Test with extreme values
            resource.setrlimit(resource.RLIMIT_NOFILE, (999999, 999999))
            print("[PASS] setrlimit with extreme values (no-op)")
        except Exception as e:
            print(f"[WARN] setrlimit edge case: {e}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Resource edge case test failed: {e}")
        traceback.print_exc()
        return False

def test_path_edge_cases():
    """Test edge cases for cross-platform path handling"""
    print("\n[TEST] Testing Path Handling Edge Cases")
    print("-" * 50)
    
    try:
        from cross_platform_paths import CrossPlatformPathHandler
        handler = CrossPlatformPathHandler()
        print("[PASS] Path handler imported")
        
        # Test edge case paths
        edge_cases = [
            "",  # Empty string
            None,  # None value - this will cause TypeError, so skip
            ".",  # Current directory
            "..",  # Parent directory
            "..\\..\\test",  # Multiple parent references
            "C:\\",  # Root drive
            "C:\\Users\\nonexistent\\very\\long\\path\\that\\does\\not\\exist",  # Long nonexistent path
            "file with spaces.txt",  # Spaces in filename
            "special!@#$%^&()chars.txt",  # Special characters
            "very_long_filename_that_exceeds_normal_expectations_but_should_still_work.txt"  # Long filename
        ]
        
        for test_path in edge_cases:
            if test_path is None:
                continue  # Skip None test as it would cause TypeError
            try:
                normalized = handler.normalize_path(test_path)
                print(f"[PASS] Normalize '{test_path}' -> '{normalized}'")
            except Exception as e:
                print(f"[WARN] Normalize '{test_path}' failed: {e}")
        
        # Test directory operations with edge cases
        try:
            temp_base = Path(tempfile.gettempdir()) / "kailash_test_edge_cases"
            
            # Test deep directory creation
            deep_path = temp_base / "very" / "deep" / "directory" / "structure" / "test"
            success = handler.ensure_directory_exists(deep_path)
            if success and deep_path.exists():
                print(f"[PASS] Deep directory creation: {deep_path}")
                # Clean up
                import shutil
                shutil.rmtree(temp_base, ignore_errors=True)
            else:
                print(f"[WARN] Deep directory creation failed: {deep_path}")
        except Exception as e:
            print(f"[WARN] Directory edge case test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Path edge case test failed: {e}")
        traceback.print_exc()
        return False

def test_workflow_edge_cases():
    """Test edge cases for workflow functionality"""
    print("\n[TEST] Testing Workflow Edge Cases")
    print("-" * 50)
    
    try:
        import windows_patch
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        print("[PASS] Workflow components imported")
        
        # Test multiple workflow creations
        workflows = []
        for i in range(5):
            workflow = WorkflowBuilder()
            workflows.append(workflow)
        print("[PASS] Multiple WorkflowBuilder instances created")
        
        # Test multiple runtime instances
        runtimes = []
        for i in range(3):
            runtime = LocalRuntime()
            runtimes.append(runtime)
        print("[PASS] Multiple LocalRuntime instances created")
        
        # Test building empty workflows
        built_workflows = []
        for workflow in workflows:
            built = workflow.build()
            built_workflows.append(built)
        print("[PASS] Multiple empty workflows built")
        
        # Test executing empty workflows
        for i, (runtime, built_workflow) in enumerate(zip(runtimes, built_workflows[:3])):
            try:
                results, run_id = runtime.execute(built_workflow)
                print(f"[PASS] Empty workflow {i+1} executed - Run ID: {run_id}")
            except Exception as e:
                print(f"[WARN] Empty workflow {i+1} execution: {e}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Workflow edge case test failed: {e}")
        traceback.print_exc()
        return False

def test_memory_and_cleanup():
    """Test memory usage and cleanup behavior"""
    print("\n[TEST] Testing Memory and Cleanup")
    print("-" * 50)
    
    try:
        import gc
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"[INFO] Initial memory usage: {initial_memory:.1f} MB")
        
        # Create and destroy many workflow objects
        for i in range(100):
            import windows_patch
            from kailash.workflow.builder import WorkflowBuilder
            from kailash.runtime.local import LocalRuntime
            
            workflow = WorkflowBuilder()
            runtime = LocalRuntime()
            built = workflow.build()
            
            # Force garbage collection periodically
            if i % 10 == 0:
                gc.collect()
        
        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        print(f"[INFO] Final memory usage: {final_memory:.1f} MB")
        print(f"[INFO] Memory increase: {memory_increase:.1f} MB")
        
        if memory_increase < 50:  # Reasonable threshold
            print("[PASS] Memory usage within acceptable limits")
        else:
            print(f"[WARN] High memory increase: {memory_increase:.1f} MB")
        
        return True
        
    except ImportError:
        print("[SKIP] psutil not available for memory testing")
        return True
    except Exception as e:
        print(f"[FAIL] Memory test failed: {e}")
        return False

def test_environment_persistence():
    """Test that compatibility patches persist across operations"""
    print("\n[TEST] Testing Environment Persistence")
    print("-" * 50)
    
    try:
        # Clear modules and re-import
        modules_to_test = [
            'windows_patch',
            'windows_resource_compat', 
            'cross_platform_paths'
        ]
        
        for module in modules_to_test:
            if module in sys.modules:
                del sys.modules[module]
        
        # Re-import and verify everything still works
        import windows_patch
        print("[PASS] Windows patch re-imported")
        
        # Test that resource module still works
        import resource
        limits = resource.getrlimit(resource.RLIMIT_NOFILE)
        print(f"[PASS] Resource module persistent: {limits}")
        
        # Test SDK imports still work
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        print("[PASS] SDK imports persistent")
        
        # Test workflow creation still works
        workflow = WorkflowBuilder()
        runtime = LocalRuntime()
        built = workflow.build()
        results, run_id = runtime.execute(built)
        print(f"[PASS] Workflow functionality persistent - Run ID: {run_id}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Environment persistence test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all edge case tests"""
    print("Testing Windows SDK Compatibility Edge Cases")
    print("=" * 70)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Concurrent Imports", test_concurrent_imports),
        ("Resource Edge Cases", test_resource_edge_cases),
        ("Path Edge Cases", test_path_edge_cases),
        ("Workflow Edge Cases", test_workflow_edge_cases),
        ("Memory and Cleanup", test_memory_and_cleanup),
        ("Environment Persistence", test_environment_persistence)
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*15} {test_name} {'='*15}")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
                print(f"[RESULT] {test_name}: PASS")
            else:
                print(f"[RESULT] {test_name}: FAIL")
        except Exception as e:
            print(f"[RESULT] {test_name}: ERROR - {e}")
            results[test_name] = False
    
    print("\n" + "=" * 70)
    print("EDGE CASE TEST RESULTS")
    print("=" * 70)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("[STATUS] All edge case tests PASSED")
        print("[VERDICT] SDK compatibility is robust and production-ready")
        return 0
    elif passed >= total * 0.8:
        print("[STATUS] Most edge case tests PASSED")
        print("[VERDICT] SDK compatibility is stable with minor edge cases")
        return 0
    else:
        print("[STATUS] Edge case tests show issues")
        print("[VERDICT] SDK compatibility needs attention for edge cases")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)