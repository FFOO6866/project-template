#!/usr/bin/env python3
"""
Clean DataFlow functionality test.

Tests DataFlow with minimal infrastructure:
- SQLite backend (confirmed working)
- Single simple model
- Basic CRUD operations
- Auto-generated node validation
"""

import sys
import os
import sqlite3
from pathlib import Path

# Windows SDK compatibility patch
if sys.platform == "win32":
    try:
        import resource
    except ImportError:
        # Mock resource module for Windows
        import types
        resource = types.ModuleType('resource')
        resource.RLIMIT_CPU = 0
        resource.getrlimit = lambda x: (float('inf'), float('inf'))
        resource.setrlimit = lambda x, y: None
        sys.modules['resource'] = resource

# Test environment setup
test_dir = Path(__file__).parent
db_path = test_dir / "test_dataflow_clean.db"

def cleanup_test_db():
    """Clean up test database"""
    if db_path.exists():
        db_path.unlink()

def test_sqlite_baseline():
    """Test baseline SQLite functionality"""
    print("=== SQLite Baseline Test ===")
    
    cleanup_test_db()
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE test_products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                active BOOLEAN DEFAULT 1
            )
        """)
        
        cursor.execute("""
            INSERT INTO test_products (name, price, active) 
            VALUES (?, ?, ?)
        """, ("Test Product", 99.99, True))
        
        cursor.execute("SELECT * FROM test_products")
        result = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        print(f"PASS SQLite baseline working: {result}")
        return True
        
    except Exception as e:
        print(f"FAIL SQLite baseline failed: {e}")
        return False
    finally:
        cleanup_test_db()

def test_kailash_core_import():
    """Test Kailash core imports"""
    print("\n=== Kailash Core Import Test ===")
    
    try:
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        print("PASS Kailash core imports successful")
        return True
        
    except Exception as e:
        print(f"FAIL Kailash core import failed: {e}")
        return False

def test_dataflow_import():
    """Test DataFlow import capabilities"""
    print("\n=== DataFlow Import Test ===")
    
    try:
        from kailash.dataflow import DataFlow
        print("PASS DataFlow imported successfully")
        return True
        
    except ImportError as e:
        print(f"FAIL DataFlow import failed: {e}")
        return False
        
    except Exception as e:
        print(f"FAIL DataFlow import error: {e}")
        return False

def test_dataflow_minimal():
    """Test minimal DataFlow functionality"""
    print("\n=== DataFlow Minimal Test ===")
    
    try:
        from kailash.dataflow import DataFlow
        
        # Initialize with SQLite (minimal config)
        db = DataFlow(database_url=f"sqlite:///{db_path}")
        
        # Define minimal model
        @db.model
        class Product:
            name: str
            price: float
            active: bool = True
            
        print("PASS DataFlow model definition successful")
        
        # Initialize database
        db.initialize()
        print("PASS DataFlow database initialization successful")
        
        # Test auto-generated nodes
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        
        workflow = WorkflowBuilder()
        
        # Test ProductCreateNode (auto-generated)
        workflow.add_node("ProductCreateNode", "create_product", {
            "name": "Test DataFlow Product",
            "price": 149.99,
            "active": True
        })
        
        # Execute workflow
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        
        print(f"PASS DataFlow CRUD operation successful: {results}")
        return True
        
    except Exception as e:
        print(f"FAIL DataFlow minimal test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cleanup_test_db()

def run_incremental_tests():
    """Run incremental DataFlow tests"""
    print("Starting Incremental DataFlow Tests")
    print("=" * 50)
    
    tests = [
        ("SQLite Baseline", test_sqlite_baseline),
        ("Kailash Core Import", test_kailash_core_import),
        ("DataFlow Import", test_dataflow_import), 
        ("DataFlow Minimal", test_dataflow_minimal)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"FAIL {test_name} crashed: {e}")
            results[test_name] = False
            
        # Stop on first failure for incremental approach
        if not results[test_name]:
            print(f"\nStopping at first failure: {test_name}")
            break
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("All incremental tests passed!")
    else:
        print("Some tests failed - this is expected for incremental approach")
    
    return results

if __name__ == "__main__":
    results = run_incremental_tests()
    print(f"\nTest completed. Check results above.")