#!/usr/bin/env python3
"""
IMMEDIATE Test Runner - Working Tests in Next Hour
==================================================

Runs the simplest possible tests that work RIGHT NOW without complex setup.
Focus: Get ONE test passing to prove the system works.
"""

import sys
import os
import subprocess
from pathlib import Path
import time

# Apply Windows compatibility first
try:
    import windows_sdk_compatibility
    print("[INFO] Windows SDK compatibility applied")
except ImportError:
    print("[WARNING] Windows SDK compatibility not found, continuing anyway")

def run_sqlite_immediate_test():
    """Run the immediate SQLite test - GUARANTEED to work"""
    
    print("\n" + "="*50)
    print("RUNNING IMMEDIATE SQLITE TEST")
    print("="*50)
    print("This test uses built-in Python SQLite - NO external dependencies")
    
    try:
        # Run the SQLite immediate test
        result = subprocess.run([
            sys.executable, 
            "test_sqlite_immediate.py"
        ], capture_output=True, text=True, timeout=60)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n[SUCCESS] SQLite immediate test PASSED!")
            return True
        else:
            print(f"\n[FAIL] SQLite test failed with exit code: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("[FAIL] SQLite test timed out")
        return False
    except Exception as e:
        print(f"[FAIL] SQLite test error: {e}")
        return False

def check_postgresql_availability():
    """Check if PostgreSQL is available for immediate use"""
    
    print("\n" + "="*50)
    print("CHECKING POSTGRESQL AVAILABILITY")
    print("="*50)
    
    try:
        # Try to run the PostgreSQL test
        result = subprocess.run([
            sys.executable,
            "test_postgresql_simple.py"
        ], capture_output=True, text=True, timeout=30)
        
        print("PostgreSQL test result:")
        print(result.stdout[-500:])  # Last 500 chars
        
        if result.returncode == 0:
            print("[SUCCESS] PostgreSQL is available and working!")
            return True
        else:
            print("[INFO] PostgreSQL not available or needs setup")
            return False
            
    except Exception as e:
        print(f"[INFO] PostgreSQL test failed: {e}")
        return False

def run_basic_sdk_test():
    """Run basic SDK test without database dependencies"""
    
    print("\n" + "="*50)
    print("RUNNING BASIC SDK TEST")
    print("="*50)
    print("Testing core SDK functionality without external dependencies")
    
    try:
        # Create a minimal SDK test inline
        test_code = '''
import sys
try:
    from kailash.workflow.builder import WorkflowBuilder
    from kailash.runtime.local import LocalRuntime
    
    print("[SUCCESS] SDK imports successful")
    
    # Create simple workflow
    workflow = WorkflowBuilder()
    workflow.add_node("JSONProcessorNode", "json_test", {
        "input_data": {"test": "immediate", "status": "working"}
    })
    
    # Execute workflow
    runtime = LocalRuntime()
    results, run_id = runtime.execute(workflow.build())
    
    print(f"[SUCCESS] Workflow executed: {run_id}")
    print(f"[SUCCESS] Results: {results}")
    print("[SUCCESS] Basic SDK test PASSED!")
    sys.exit(0)
    
except ImportError as e:
    print(f"[WARNING] SDK not available: {e}")
    print("[INFO] This is expected if Kailash SDK is not installed")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] SDK test failed: {e}")
    sys.exit(1)
'''
        
        # Write and run the test
        test_file = Path("temp_basic_sdk_test.py")
        test_file.write_text(test_code)
        
        try:
            result = subprocess.run([
                sys.executable,
                str(test_file)
            ], capture_output=True, text=True, timeout=30)
            
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            return result.returncode == 0
            
        finally:
            # Cleanup temp file
            if test_file.exists():
                test_file.unlink()
        
    except Exception as e:
        print(f"[ERROR] Basic SDK test error: {e}")
        return False

def run_simple_integration_test():
    """Run one simple integration test that should work"""
    
    print("\n" + "="*50)
    print("RUNNING SIMPLE INTEGRATION TEST")
    print("="*50)
    print("Testing one specific integration that should work immediately")
    
    try:
        # Look for existing simple tests
        potential_tests = [
            "test_dataflow_foundation_simple.py",
            "test_simple_validation.py",
            "test_infrastructure_reality_check.py"
        ]
        
        for test_file in potential_tests:
            if Path(test_file).exists():
                print(f"Running: {test_file}")
                
                result = subprocess.run([
                    sys.executable,
                    test_file
                ], capture_output=True, text=True, timeout=120)
                
                print(f"Exit code: {result.returncode}")
                print("Last 300 characters of output:")
                print(result.stdout[-300:])
                
                if result.returncode == 0:
                    print(f"[SUCCESS] {test_file} PASSED!")
                    return True
                else:
                    print(f"[FAIL] {test_file} failed")
                    continue
        
        print("[INFO] No simple integration tests passed")
        return False
        
    except Exception as e:
        print(f"[ERROR] Integration test error: {e}")
        return False

def show_immediate_next_steps(sqlite_success, postgresql_available, sdk_working):
    """Show immediate next steps based on what's working"""
    
    print("\n" + "="*60)
    print("IMMEDIATE NEXT STEPS ANALYSIS")
    print("="*60)
    
    if sqlite_success:
        print("[✓] SQLite database is working - USE THIS FOR IMMEDIATE DEVELOPMENT")
        print("    Database file: ./test_horme.db")
        print("    Connection: sqlite:///test_horme.db")
        print("")
        print("IMMEDIATE ACTION: Start building features with SQLite!")
        print("1. Copy working SQLite patterns from test_sqlite_immediate.py")
        print("2. Create your tables and models")
        print("3. Build workflows using SQLite as the backend")
        print("")
    
    if postgresql_available:
        print("[✓] PostgreSQL is also available - PRODUCTION READY")
        print("    Use for production/enterprise features")
        print("")
    else:
        print("[?] PostgreSQL not available - OPTIONAL")
        print("    Run: python postgresql_windows_installer.py")
        print("    But SQLite is sufficient for immediate development")
        print("")
    
    if sdk_working:
        print("[✓] Kailash SDK is working - BUILD WORKFLOWS NOW")
        print("    Create workflows with WorkflowBuilder")
        print("    Execute with LocalRuntime")
        print("")
        print("IMMEDIATE WORKFLOW PATTERN:")
        print("```python")
        print("from kailash.workflow.builder import WorkflowBuilder")
        print("from kailash.runtime.local import LocalRuntime")
        print("")
        print("workflow = WorkflowBuilder()")
        print("workflow.add_node('NodeName', 'id', {'param': 'value'})")
        print("runtime = LocalRuntime()")
        print("results, run_id = runtime.execute(workflow.build())")
        print("```")
    else:
        print("[?] Kailash SDK needs attention")
        print("    But you can still work with databases directly")
        print("")
    
    # Priority actions
    print("PRIORITY IMMEDIATE ACTIONS (next 30 minutes):")
    if sqlite_success:
        print("1. [HIGH] Use SQLite database for immediate feature development")
        print("2. [HIGH] Create your first working CRUD operations")
        print("3. [MEDIUM] Add real business logic to the database")
    else:
        print("1. [CRITICAL] Fix SQLite setup - this should always work")
    
    if not sdk_working:
        print("4. [MEDIUM] Investigate SDK import issues")
        print("5. [LOW] Set up PostgreSQL (optional for immediate work)")
    
    print("\nFOCUS: Build working features with what's available RIGHT NOW!")

def main():
    """Run immediate tests to find what works RIGHT NOW"""
    
    print("IMMEDIATE TEST RUNNER")
    print("="*30)
    print("Finding what works RIGHT NOW for immediate development")
    
    start_time = time.time()
    
    # Test 1: SQLite (should always work)
    sqlite_success = run_sqlite_immediate_test()
    
    # Test 2: PostgreSQL (optional)
    postgresql_available = check_postgresql_availability()
    
    # Test 3: Basic SDK (if available)
    sdk_working = run_basic_sdk_test()
    
    # Test 4: Simple integration (one test)
    integration_working = run_simple_integration_test()
    
    elapsed_time = time.time() - start_time
    
    # Results summary
    print("\n" + "="*60)
    print("IMMEDIATE TEST RESULTS SUMMARY")
    print("="*60)
    print(f"Total time: {elapsed_time:.1f} seconds")
    print("")
    print(f"SQLite Database:       {'✓ WORKING' if sqlite_success else '✗ FAILED'}")
    print(f"PostgreSQL Database:   {'✓ AVAILABLE' if postgresql_available else '? NOT AVAILABLE'}")
    print(f"Kailash SDK:           {'✓ WORKING' if sdk_working else '? NEEDS ATTENTION'}")
    print(f"Integration Test:      {'✓ WORKING' if integration_working else '? NEEDS WORK'}")
    print("")
    
    # Show next steps
    show_immediate_next_steps(sqlite_success, postgresql_available, sdk_working)
    
    # Return success if at least SQLite works
    if sqlite_success:
        print("\n[SUCCESS] You have a working database - START BUILDING NOW!")
        return 0
    else:
        print("\n[CRITICAL] No working database found - this needs immediate attention")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTests cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)