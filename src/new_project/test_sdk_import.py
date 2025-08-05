#!/usr/bin/env python3
"""Test SDK imports to verify claims."""

import sys
import traceback

# CRITICAL: Apply Windows compatibility BEFORE any SDK imports
try:
    from windows_sdk_compatibility import ensure_windows_compatibility
    ensure_windows_compatibility()
    print("[OK] Windows compatibility applied")
except ImportError as e:
    print(f"[WARNING] Windows compatibility not available: {e}")

def test_sdk_imports():
    """Test if SDK imports are actually working"""
    print("Testing Kailash SDK imports...")
    
    # Test basic Python
    print("[OK] Python working")
    
    # Test SDK imports
    try:
        from kailash.workflow.builder import WorkflowBuilder
        print("[OK] WorkflowBuilder import SUCCESS")
    except Exception as e:
        print(f"[FAIL] WorkflowBuilder import FAILED: {e}")
        traceback.print_exc()
        return False
    
    try:
        from kailash.runtime.local import LocalRuntime
        print("[OK] LocalRuntime import SUCCESS")
    except Exception as e:
        print(f"[FAIL] LocalRuntime import FAILED: {e}")
        traceback.print_exc()
        return False
    
    try:
        from kailash.nodes.base import Node
        print("[OK] Node import SUCCESS")
    except Exception as e:
        print(f"[FAIL] Node import FAILED: {e}")
        traceback.print_exc()
        return False
    
    # Test basic workflow creation
    try:
        workflow = WorkflowBuilder()
        runtime = LocalRuntime()
        print("[OK] Basic SDK instantiation SUCCESS")
        return True
    except Exception as e:
        print(f"[FAIL] Basic SDK instantiation FAILED: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sdk_imports()
    exit(0 if success else 1)