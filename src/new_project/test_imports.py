#!/usr/bin/env python3
"""
Test script to check what Kailash SDK imports are available
"""

import sys

def test_import(module_path, item_name):
    """Test importing a specific item from a module"""
    try:
        module = __import__(module_path, fromlist=[item_name])
        item = getattr(module, item_name)
        print(f"✓ {module_path}.{item_name} - Available")
        return True
    except Exception as e:
        print(f"✗ {module_path}.{item_name} - Error: {e}")
        return False

def test_module(module_path):
    """Test importing an entire module"""
    try:
        __import__(module_path)
        print(f"✓ {module_path} - Available")
        return True
    except Exception as e:
        print(f"✗ {module_path} - Error: {e}")
        return False

print("Testing Kailash SDK imports...")
print("=" * 50)

# Test basic modules
modules_to_test = [
    "kailash",
    "kailash.workflow",
    "kailash.workflow.builder",
    "kailash.runtime",
    "kailash.runtime.local",
    "kailash.nodes",
    "kailash.nodes.base"
]

for module in modules_to_test:
    test_module(module)

print("\nTesting specific imports...")
print("=" * 50)

# Test specific imports
specific_imports = [
    ("kailash.workflow.builder", "WorkflowBuilder"),
    ("kailash.runtime.local", "LocalRuntime"),
    ("kailash.nodes.base", "Node"),
    ("kailash.nodes.base", "NodeParameter"),
    ("kailash.nodes.base", "register_node"),
    ("kailash.nodes.base", "NodeRegistry"),
    ("kailash.nodes.base", "NodeConfigurationError"),
]

available_imports = []
for module_path, item_name in specific_imports:
    if test_import(module_path, item_name):
        available_imports.append(f"{module_path}.{item_name}")

print(f"\nSummary: {len(available_imports)}/{len(specific_imports)} imports available")
print("Available imports:")
for imp in available_imports:
    print(f"  - {imp}")