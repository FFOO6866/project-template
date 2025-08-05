#!/usr/bin/env python3
"""
Basic DataFlow Functionality Test
=================================

Tests actual DataFlow functionality with manually installed PostgreSQL.
This test focuses on basic functionality verification without complex setups.

Prerequisites:
- PostgreSQL manually installed and running
- Basic database setup completed
- Core dependencies available

Usage:
    python test_dataflow_basic_functionality.py
"""

import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional

def test_postgresql_connection():
    """Test basic PostgreSQL connection using psycopg2"""
    print("\n" + "="*60)
    print("TESTING POSTGRESQL CONNECTION")
    print("="*60)
    
    try:
        import psycopg2
        
        # Try to connect with basic parameters
        connection_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'postgres',  # Default database
            'user': 'postgres',      # Default user
            'password': 'postgres'   # Default password (may need adjustment)
        }
        
        print(f"Attempting connection to PostgreSQL...")
        print(f"Host: {connection_params['host']}:{connection_params['port']}")
        print(f"Database: {connection_params['database']}")
        print(f"User: {connection_params['user']}")
        
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print(f"[PASS] PostgreSQL connection successful")
        print(f"[INFO] Version: {version[0]}")
        return True
        
    except ImportError:
        print(f"[FAIL] psycopg2 not available - PostgreSQL driver not installed")
        print(f"[INFO] Install with: pip install psycopg2-binary")
        return False
        
    except psycopg2.OperationalError as e:
        print(f"[FAIL] PostgreSQL connection failed: {e}")
        print(f"[INFO] Ensure PostgreSQL is running and credentials are correct")
        return False
        
    except Exception as e:
        print(f"[FAIL] PostgreSQL test failed: {e}")
        return False


def test_sdk_availability():
    """Test if Core SDK components are available"""
    print("\n" + "="*60)
    print("TESTING CORE SDK AVAILABILITY")
    print("="*60)
    
    test_results = {}
    
    # Test Core SDK imports
    try:
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        print("[PASS] Core SDK imports successful")
        test_results['core_sdk'] = True
    except ImportError as e:
        print(f"[FAIL] Core SDK not available: {e}")
        print("[INFO] Install with: pip install kailash")
        test_results['core_sdk'] = False
    
    # Test DataFlow imports
    try:
        from dataflow import DataFlow
        print("[PASS] DataFlow import successful")
        test_results['dataflow'] = True
    except ImportError as e:
        print(f"[FAIL] DataFlow not available: {e}")
        print("[INFO] Install with: pip install kailash[dataflow]")
        test_results['dataflow'] = False
    
    return test_results


def test_basic_workflow_creation():
    """Test basic workflow creation without database operations"""
    print("\n" + "="*60)
    print("TESTING BASIC WORKFLOW CREATION")
    print("="*60)
    
    try:
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        
        # Create basic workflow
        workflow = WorkflowBuilder()
        
        # Add a simple test node (not database-related)
        workflow.add_node("TestNode", "test_operation", {
            "test_parameter": "test_value",
            "timestamp": datetime.now().isoformat()
        })
        
        # Build workflow (don't execute yet)
        built_workflow = workflow.build()
        
        print("[PASS] Basic workflow creation successful")
        print(f"[INFO] Workflow contains {len(built_workflow.nodes)} nodes")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Workflow creation failed: {e}")
        return False


def test_simple_dataflow_model():
    """Test simple DataFlow model definition without database execution"""
    print("\n" + "="*60)
    print("TESTING SIMPLE DATAFLOW MODEL DEFINITION")
    print("="*60)
    
    try:
        from dataflow import DataFlow
        
        # Create simple in-memory DataFlow instance for testing
        db = DataFlow(":memory:")  # SQLite in-memory for testing
        
        # Define a simple test model
        @db.model
        class TestProduct:
            id: int
            name: str
            price: float
            is_active: bool = True
        
        print("[PASS] DataFlow model definition successful")
        print(f"[INFO] Model TestProduct defined with @db.model decorator")
        print(f"[INFO] Expected auto-generated nodes:")
        
        node_types = ['Create', 'Read', 'Update', 'Delete', 'List', 
                     'BulkCreate', 'BulkUpdate', 'BulkDelete', 'BulkUpsert']
        
        for node_type in node_types:
            node_name = f"TestProduct{node_type}Node"
            print(f"       - {node_name}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] DataFlow model definition failed: {e}")
        return False


def test_basic_dataflow_operations():
    """Test basic DataFlow operations with in-memory database"""
    print("\n" + "="*60)
    print("TESTING BASIC DATAFLOW OPERATIONS")
    print("="*60)
    
    try:
        from dataflow import DataFlow
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        
        # Create in-memory database for testing
        db = DataFlow(":memory:")
        
        # Define simple model
        @db.model
        class SimpleProduct:
            id: int
            name: str
            price: float
        
        # Initialize database
        db.initialize()
        print("[PASS] DataFlow database initialization successful")
        
        # Create workflow with auto-generated node
        workflow = WorkflowBuilder()
        workflow.add_node("SimpleProductCreateNode", "create_product", {
            "name": "Test Product",
            "price": 99.99
        })
        
        # Execute workflow
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        
        print(f"[PASS] DataFlow operation successful")
        print(f"[INFO] Run ID: {run_id}")
        print(f"[INFO] Results: {results}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] DataFlow operations failed: {e}")
        return False


def run_basic_functionality_tests():
    """Run all basic functionality tests"""
    print("\n" + "="*80)
    print("DATAFLOW BASIC FUNCTIONALITY TEST SUITE")
    print("="*80)
    
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }
    
    # Test 1: PostgreSQL Connection
    postgres_success = test_postgresql_connection()
    test_results['tests']['postgresql_connection'] = postgres_success
    
    # Test 2: SDK Availability
    sdk_results = test_sdk_availability()
    test_results['tests']['sdk_availability'] = sdk_results
    
    # Test 3: Basic Workflow Creation (if SDK available)
    workflow_success = False
    if sdk_results.get('core_sdk', False):
        workflow_success = test_basic_workflow_creation()
    test_results['tests']['workflow_creation'] = workflow_success
    
    # Test 4: DataFlow Model Definition (if DataFlow available)
    model_success = False
    if sdk_results.get('dataflow', False):
        model_success = test_simple_dataflow_model()
    test_results['tests']['dataflow_model'] = model_success
    
    # Test 5: Basic DataFlow Operations (if all available)
    operations_success = False
    if sdk_results.get('core_sdk', False) and sdk_results.get('dataflow', False):
        operations_success = test_basic_dataflow_operations()
    test_results['tests']['dataflow_operations'] = operations_success
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total_tests = len(test_results['tests'])
    passed_tests = 0
    
    for test_name, result in test_results['tests'].items():
        if isinstance(result, bool):
            status = "PASS" if result else "FAIL"
            if result:
                passed_tests += 1
        elif isinstance(result, dict):
            # SDK availability results
            sub_passed = sum(1 for v in result.values() if v)
            sub_total = len(result)
            status = f"PARTIAL ({sub_passed}/{sub_total})"
            if sub_passed > 0:
                passed_tests += 0.5  # Partial credit
        else:
            status = "UNKNOWN"
        
        print(f"{test_name:25}: {status}")
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\nOverall Success Rate: {success_rate:.1f}%")
    
    # Next steps
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    
    if not postgres_success:
        print("1. Install and start PostgreSQL:")
        print("   - Windows: Download from postgresql.org")
        print("   - Install psycopg2: pip install psycopg2-binary")
    
    if not sdk_results.get('core_sdk', False):
        print("2. Install Kailash Core SDK:")
        print("   pip install kailash")
    
    if not sdk_results.get('dataflow', False):
        print("3. Install DataFlow:")
        print("   pip install kailash[dataflow]")
    
    if all([postgres_success, sdk_results.get('core_sdk', False), 
            sdk_results.get('dataflow', False)]):
        print("✅ All dependencies available!")
        print("Next: Test actual PostgreSQL DataFlow operations")
    
    # Save results
    results_file = f"dataflow_basic_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    return success_rate >= 60  # 60% threshold for basic success


def main():
    """Main test execution"""
    try:
        success = run_basic_functionality_tests()
        
        if success:
            print(f"\n[SUCCESS] Basic DataFlow functionality validated!")
            sys.exit(0)
        else:
            print(f"\n[INFO] Basic functionality needs setup - see next steps above")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nTest execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()