"""
Simple Infrastructure Validation Test
====================================

Test that all key infrastructure components work without complex workflows.
"""

import sys
import os
from pathlib import Path

# Apply Windows patch
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
from windows_patch import mock_resource

# Add src to path
src_dir = project_root.parent.parent / "src"
sys.path.insert(0, str(src_dir))
print(f"Added src path: {src_dir}")
print(f"Src exists: {src_dir.exists()}")
if src_dir.exists():
    print(f"Files in src: {list(src_dir.glob('*.py'))[:5]}")

def main():
    """Test all infrastructure components"""
    print("Infrastructure Validation Test")
    print("=" * 35)
    
    try:
        # Test 1: Kailash Core SDK imports
        print("\n1. Testing Kailash Core SDK...")
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        print("OK Kailash core imports successful")
        
        # Test basic workflow creation (without execution)
        workflow = WorkflowBuilder()
        runtime = LocalRuntime()
        print("OK Workflow and runtime instances created")
        
        # Test 2: DataFlow package
        print("\n2. Testing DataFlow package...")
        from dataflow import DataFlow
        print("OK DataFlow class imported")
        
        # Test 3: DataFlow models
        print("\n3. Testing DataFlow models...")
        from dataflow_models import db
        print("OK dataflow_models imported")
        
        # Test decorator availability
        assert hasattr(db, 'model'), "@db.model decorator missing"
        assert callable(db.model), "@db.model decorator not callable"
        print("OK @db.model decorator available")
        
        # Test model classes
        from dataflow_models import Company, User, Customer, Quote
        print("OK Model classes imported: Company, User, Customer, Quote")
        
        # Test 4: Python environment
        print("\n4. Testing Python environment...")
        import subprocess
        result = subprocess.run(['python', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"OK Python command available: {result.stdout.strip()}")
        else:
            result = subprocess.run(['py', '--version'], capture_output=True, text=True, timeout=5)
            print(f"OK Python via 'py' command: {result.stdout.strip()}")
        
        print("\n" + "=" * 35)
        print("SUCCESS: All infrastructure components working!")
        print("\nInfrastructure Status:")
        print("- Windows compatibility: WORKING")
        print("- Kailash SDK: WORKING") 
        print("- DataFlow package: WORKING")
        print("- Model definitions: WORKING")
        print("- Python environment: WORKING")
        print("\nReady for DATA-001 implementation!")
        
        return True
        
    except Exception as e:
        print(f"\nFAILED: Infrastructure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)