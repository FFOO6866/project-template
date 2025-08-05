"""
Windows SDK Import Diagnostic Script
=====================================

This script identifies specific SDK import failures on Windows
to guide the compatibility implementation.
"""

import sys
import traceback
import platform
import os
from pathlib import Path

def diagnose_import_failures():
    """Identify specific import failures and their root causes"""
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print(f"Architecture: {platform.architecture()}")
    print(f"Working Directory: {os.getcwd()}")
    print("=" * 60)
    
    # Critical SDK imports to test
    critical_imports = [
        'kailash.workflow.builder',
        'kailash.runtime.local', 
        'kailash.nodes.base',
        'kailash.nodes.core',
        'kailash.workflow',
        'kailash.runtime',
        'kailash.nodes',
        'kailash'
    ]
    
    # Additional modules that might be problematic
    system_modules = [
        'resource',
        'fcntl',
        'termios',
        'pwd',
        'grp',
        'signal'
    ]
    
    results = {
        "platform_info": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "python_executable": sys.executable
        },
        "sdk_imports": {},
        "system_modules": {},
        "path_info": {
            "python_path": sys.path,
            "working_dir": os.getcwd(),
            "environment_path": os.environ.get('PATH', '').split(os.pathsep)
        }
    }
    
    print("\n[DIAG] Testing Critical SDK Imports:")
    print("-" * 40)
    
    for module in critical_imports:
        try:
            imported_module = __import__(module, fromlist=[''])
            print(f"[PASS] {module}")
            results["sdk_imports"][module] = {
                "status": "SUCCESS",
                "location": getattr(imported_module, '__file__', 'Built-in'),
                "version": getattr(imported_module, '__version__', 'Unknown')
            }
        except Exception as e:
            print(f"[FAIL] {module}: {e}")
            tb = traceback.format_exc()
            results["sdk_imports"][module] = {
                "status": "FAILED",
                "error": str(e),
                "traceback": tb,
                "error_type": type(e).__name__
            }
    
    print("\n[DIAG] Testing System Modules (Unix-specific):")
    print("-" * 40)
    
    for module in system_modules:
        try:
            imported_module = __import__(module)
            print(f"[PASS] {module}")
            results["system_modules"][module] = {
                "status": "SUCCESS",
                "location": getattr(imported_module, '__file__', 'Built-in')
            }
        except Exception as e:
            print(f"[FAIL] {module}: {e}")
            results["system_modules"][module] = {
                "status": "FAILED",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    # Check for existing compatibility patches
    print("\n[DIAG] Checking Existing Compatibility:")
    print("-" * 40)
    
    compatibility_modules = [
        'windows_patch',
        'windows_resource_compat',
        'cross_platform_paths'
    ]
    
    results["compatibility_modules"] = {}
    
    for module in compatibility_modules:
        try:
            # Try to import from current directory
            sys.path.insert(0, '.')
            imported_module = __import__(module)
            print(f"[AVAIL] {module} (available)")
            results["compatibility_modules"][module] = {
                "status": "AVAILABLE",
                "location": getattr(imported_module, '__file__', 'Unknown')
            }
        except Exception as e:
            print(f"[MISS] {module} (not available): {e}")
            results["compatibility_modules"][module] = {
                "status": "NOT_AVAILABLE",
                "error": str(e)
            }
    
    return results

def generate_compatibility_plan(results):
    """Generate a compatibility implementation plan based on diagnostic results"""
    print("\n[PLAN] Compatibility Implementation Plan:")
    print("=" * 50)
    
    failed_sdk_imports = [
        module for module, result in results["sdk_imports"].items() 
        if result["status"] == "FAILED"
    ]
    
    failed_system_modules = [
        module for module, result in results["system_modules"].items() 
        if result["status"] == "FAILED"
    ]
    
    if failed_sdk_imports:
        print("\n[CRITICAL] SDK Import Failures:")
        for module in failed_sdk_imports:
            error_info = results["sdk_imports"][module]
            print(f"  - {module}: {error_info['error_type']} - {error_info['error']}")
    
    if failed_system_modules:
        print("\n[WARNING] System Module Compatibility Needed:")
        for module in failed_system_modules:
            print(f"  - {module}")
    
    print("\n[ACTION] Recommended Actions:")
    if failed_system_modules:
        print("  1. Enhance resource module compatibility in windows_resource_compat.py")
        print("  2. Add compatibility shims for missing Unix-specific modules")
    
    if failed_sdk_imports:
        print("  3. Fix SDK import chain issues")
        print("  4. Ensure proper module discovery and loading")
    
    print("  5. Implement cross-platform path handling")
    print("  6. Create comprehensive validation suite")
    
    return {
        "failed_sdk_imports": failed_sdk_imports,
        "failed_system_modules": failed_system_modules,
        "needs_resource_compat": 'resource' in failed_system_modules,
        "needs_sdk_fixes": len(failed_sdk_imports) > 0
    }

def main():
    """Run complete diagnostic and generate implementation plan"""
    print("Windows SDK Compatibility Diagnostic")
    print("=" * 60)
    
    try:
        # Run diagnostics
        results = diagnose_import_failures()
        
        # Generate implementation plan
        plan = generate_compatibility_plan(results)
        
        # Calculate success metrics
        total_sdk_imports = len(results["sdk_imports"])
        successful_sdk_imports = sum(
            1 for result in results["sdk_imports"].values() 
            if result["status"] == "SUCCESS"
        )
        
        success_rate = (successful_sdk_imports / total_sdk_imports) * 100 if total_sdk_imports > 0 else 0
        
        print(f"\n[METRIC] Current SDK Import Success Rate: {success_rate:.1f}% ({successful_sdk_imports}/{total_sdk_imports})")
        
        if success_rate < 100:
            print("[RESULT] Windows SDK compatibility implementation required")
            return 1
        else:
            print("[RESULT] Windows SDK compatibility already working")
            return 0
            
    except Exception as e:
        print(f"\n[ERROR] Diagnostic failed: {e}")
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    exit(main())