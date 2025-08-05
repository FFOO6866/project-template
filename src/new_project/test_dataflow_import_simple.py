"""
Simple test to validate DataFlow imports with Windows patch
"""

import sys
import os

# Apply Windows patch first
sys.path.insert(0, os.path.dirname(__file__))
from windows_patch import mock_resource  # This applies the patch

# Now try the imports
try:
    from dataflow import DataFlow
    print("SUCCESS: DataFlow imported from kailash-dataflow package")
    
    # Test creating a DataFlow instance
    db = DataFlow(database_url="sqlite:///test.db")
    print("SUCCESS: DataFlow instance created")
    
    # Test the @db.model decorator exists
    assert hasattr(db, 'model'), "@db.model decorator should exist"
    assert callable(db.model), "@db.model should be callable"
    print("SUCCESS: DataFlow @db.model decorator available")
    
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()

# Now test importing dataflow_models
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from dataflow_models import db
    print("SUCCESS: dataflow_models imported successfully")
    
    # Test that we can access the db instance
    assert db is not None, "db instance should not be None"
    print("SUCCESS: dataflow_models.db instance is available")
    
except Exception as e:
    print(f"FAILED dataflow_models import: {e}")
    import traceback
    traceback.print_exc()

print("\nInfrastructure validation complete!")