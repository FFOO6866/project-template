#!/usr/bin/env python3
"""
Minimal DataFlow functionality test.

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

# Test environment setup
test_dir = Path(__file__).parent
db_path = test_dir / "test_dataflow.db"

def cleanup_test_db():
    """Clean up test database"""
    if db_path.exists():
        db_path.unlink()

def test_sqlite_baseline():
    """Test baseline SQLite functionality"""
    print("=== SQLite Baseline Test ===")
    
    # Remove existing test db
    cleanup_test_db()
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute("""
            CREATE TABLE test_products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                active BOOLEAN DEFAULT 1
            )
        """)
        
        # Insert test data
        cursor.execute("""
            INSERT INTO test_products (name, price, active) 
            VALUES (?, ?, ?)
        """, ("Test Product", 99.99, True))
        
        # Read test data
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

def test_dataflow_import():
    """Test DataFlow import capabilities"""
    print("\n=== DataFlow Import Test ===")
    
    try:
        # Try DataFlow import
        from kailash.dataflow import DataFlow
        print("✅ DataFlow imported successfully")
        return True
        
    except ImportError as e:
        print(f"❌ DataFlow import failed: {e}")
        
        # Try alternative import paths
        alternatives = [
            "dataflow",
            "kailash_dataflow", 
            "kailash.apps.dataflow"
        ]
        
        for alt in alternatives:
            try:
                __import__(alt)
                print(f"✅ Alternative import {alt} succeeded")
                return True
            except ImportError:
                continue
                
        print("❌ No DataFlow import path available")
        return False
        
    except Exception as e:
        print(f"❌ DataFlow import error: {e}")
        return False

def test_workflow_foundation():
    """Test basic workflow foundation"""
    print("\n=== Workflow Foundation Test ===")
    
    try:
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        
        # Create minimal workflow
        workflow = WorkflowBuilder()
        workflow.add_node("TestNode", "test_id", {"message": "test"})
        
        # Test workflow build
        built_workflow = workflow.build()
        print("✅ Workflow foundation working")
        return True
        
    except Exception as e:
        print(f"❌ Workflow foundation failed: {e}")
        return False

def test_dataflow_minimal():
    """Test minimal DataFlow functionality"""
    print("\n=== DataFlow Minimal Test ===")
    
    try:
        # Import DataFlow
        from kailash.dataflow import DataFlow
        
        # Initialize with SQLite (minimal config)
        db = DataFlow(database_url=f"sqlite:///{db_path}")
        
        # Define minimal model
        @db.model
        class Product:
            name: str
            price: float
            active: bool = True
            
        print("✅ DataFlow model definition successful")
        
        # Initialize database
        db.initialize()
        print("✅ DataFlow database initialization successful")
        
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
        
        print(f"✅ DataFlow CRUD operation successful: {results}")
        return True
        
    except Exception as e:
        print(f"❌ DataFlow minimal test failed: {e}")
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
        ("DataFlow Import", test_dataflow_import), 
        ("Workflow Foundation", test_workflow_foundation),
        ("DataFlow Minimal", test_dataflow_minimal)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
            
        # Stop on first failure for incremental approach
        if not results[test_name]:
            print(f"\n⚠️  Stopping at first failure: {test_name}")
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
        print("Some tests failed - incremental approach working")
    
    return results

if __name__ == "__main__":
    results = run_incremental_tests()
    
    # Exit with error code if any tests failed
    if not all(results.values()):
        sys.exit(1)