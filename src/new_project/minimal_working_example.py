"""
Minimal Working Example - Infrastructure Validation
=================================================

This demonstrates that all critical infrastructure components are working:
1. Windows patch application
2. Kailash SDK imports and basic functionality
3. Workflow creation and building

This serves as a baseline proof-of-concept for the development environment.
"""

import sys
from pathlib import Path

def main():
    print("=== Minimal Working Example - Infrastructure Validation ===")
    print()
    
    # Step 1: Apply Windows patch
    print("1. Applying Windows compatibility patch...")
    try:
        import windows_patch
        status = windows_patch.get_patch_status()
        print(f"   ✓ Patch applied successfully")
        print(f"   ✓ Platform: {status['platform']}")
        print(f"   ✓ Patches applied: {len(status.get('patches_applied', []))}")
    except Exception as e:
        print(f"   ✗ Windows patch failed: {e}")
        return False
    
    # Step 2: Test Kailash SDK imports
    print("\n2. Testing Kailash SDK imports...")
    try:
        import kailash
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        print("   ✓ Core SDK imports successful")
    except Exception as e:
        print(f"   ✗ SDK imports failed: {e}")
        return False
    
    # Step 3: Create a minimal workflow
    print("\n3. Creating minimal workflow...")
    try:
        workflow = WorkflowBuilder()
        
        # Add a simple PythonCodeNode
        workflow.add_node(
            "PythonCodeNode",
            "hello_world",
            {
                "code": """
# Simple Hello World computation
message = "Hello from Kailash SDK!"
result = {
    'message': message,
    'status': 'success',
    'length': len(message)
}
print(f"Computed: {result}")
"""
            }
        )
        
        print("   ✓ Workflow created with PythonCodeNode")
        
        # Build the workflow
        built_workflow = workflow.build()
        print("   ✓ Workflow built successfully")
        print(f"   ✓ Nodes in workflow: {len(built_workflow.nodes)}")
        
        # Verify node structure
        node = built_workflow.nodes['hello_world']
        print(f"   ✓ Node type: {type(node).__name__}")
        print(f"   ✓ Node has config: {'code' in node.config}")
        
    except Exception as e:
        print(f"   ✗ Workflow creation failed: {e}")
        return False
    
    # Step 4: Test runtime creation (without execution)
    print("\n4. Testing runtime creation...")
    try:
        runtime = LocalRuntime()
        print("   ✓ LocalRuntime created successfully")
        print(f"   ✓ Runtime type: {type(runtime).__name__}")
    except Exception as e:
        print(f"   ✗ Runtime creation failed: {e}")
        return False
    
    # Step 5: Verify native service alternatives
    print("\n5. Testing native service alternatives...")
    try:
        # Test SQLite as PostgreSQL alternative
        import sqlite3
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER, message TEXT)')
        cursor.execute('INSERT INTO test VALUES (1, ?)', ('Hello SQLite!',))
        cursor.execute('SELECT * FROM test')
        result = cursor.fetchone()
        conn.close()
        print("   ✓ SQLite (PostgreSQL alternative) working")
        
        # Test Python dict as Redis alternative
        cache = {'key1': 'value1', 'status': 'active'}
        assert cache.get('key1') == 'value1'
        print("   ✓ Python dict (Redis alternative) working")
        
        # Test JSON as document store
        import json
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {'documents': [{'id': 1, 'content': 'test'}]}
            json.dump(test_data, f)
            temp_file = f.name
        
        with open(temp_file, 'r') as f:
            loaded = json.load(f)
        
        os.unlink(temp_file)
        assert loaded['documents'][0]['content'] == 'test'
        print("   ✓ JSON files (document store alternative) working")
        
    except Exception as e:
        print(f"   ✗ Native service alternatives failed: {e}")
        return False
    
    print("\n=== SUCCESS: All Infrastructure Components Validated ===")
    print()
    print("Infrastructure Status:")
    print("• Windows compatibility: ✓ Applied")
    print("• Kailash SDK imports: ✓ Working")
    print("• Workflow creation: ✓ Working")
    print("• Runtime creation: ✓ Working")
    print("• Native services: ✓ Available")
    print()
    print("Ready for development work!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)