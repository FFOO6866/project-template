#!/usr/bin/env python3
"""
Simple Master Test Runner for Docker Deployment
"""

import subprocess
import sys
import time
import json
from datetime import datetime

def run_health_check():
    """Run basic health check"""
    print("Running health check...")
    try:
        result = subprocess.run([sys.executable, 'simple_health_check.py'], 
                              capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def run_production_tests():
    """Run production readiness tests"""
    print("Running production readiness tests...")
    try:
        result = subprocess.run([sys.executable, 'production_readiness_tests.py'], 
                              capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception as e:
        print(f"Production tests failed: {e}")
        return False

def main():
    print("Docker Deployment Test Suite")
    print("=" * 40)
    
    start_time = datetime.now()
    
    # Run tests
    tests = [
        ("Health Check", run_health_check),
        ("Production Readiness", run_production_tests)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        try:
            success = test_func()
            results[test_name] = success
            status = "PASSED" if success else "FAILED"
            print(f"{test_name}: {status}")
        except Exception as e:
            results[test_name] = False
            print(f"{test_name}: ERROR - {e}")
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    passed = sum(results.values())
    total = len(results)
    
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    print(f"Duration: {duration:.1f} seconds")
    print(f"Tests: {passed}/{total} passed")
    
    for test_name, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"  {test_name}: {status}")
    
    if passed == total:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print(f"\n{total - passed} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
