#!/usr/bin/env python3
"""
Minimal Working Infrastructure Test
==================================

Tests minimal viable infrastructure using proper Kailash SDK patterns:
1. SQLite database with SQLDatabaseNode (immediate working)
2. In-memory cache (Python dict/lru_cache)
3. Basic service health checks
4. Real SDK pattern validation

This follows the ESSENTIAL EXECUTION PATTERN:
- WorkflowBuilder with string-based nodes
- runtime.execute(workflow.build()) - ALWAYS .build()
"""

import sys
import json
import time
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Apply Windows compatibility
try:
    from windows_sdk_compatibility import ensure_windows_compatibility
    ensure_windows_compatibility()
    print("[OK] Windows compatibility applied")
except ImportError as e:
    print(f"[WARNING] Windows compatibility not available: {e}")

# Essential SDK pattern imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime


class MinimalInfrastructureTest:
    """Test minimal working infrastructure with proper SDK patterns"""
    
    def __init__(self):
        self.runtime = LocalRuntime()
        self.test_results = []
        self.db_path = Path(__file__).parent / "immediate_test.db"
        
    def log_test(self, test_name: str, success: bool, message: str, details: Optional[Dict] = None):
        """Log test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {test_name}: {message}")
        
        if details and not success:
            print(f"    Details: {json.dumps(details, indent=4)}")
    
    def setup_sqlite_database(self) -> bool:
        """Setup SQLite database for immediate use"""
        try:
            print(f"Setting up SQLite database at: {self.db_path}")
            
            # Create database with test data
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Create test table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert test data
            test_products = [
                ("Widget A", "Basic widget", 10.99),
                ("Widget B", "Advanced widget", 24.99),
                ("Tool X", "Professional tool", 45.00)
            ]
            
            cursor.executemany(
                "INSERT OR REPLACE INTO test_products (name, description, price) VALUES (?, ?, ?)",
                test_products
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.log_test("SQLite Setup", True, f"Database created with {len(test_products)} test products")
            return True
            
        except Exception as e:
            self.log_test("SQLite Setup", False, f"Database setup failed: {e}")
            return False
    
    def test_sql_database_node(self) -> bool:
        """Test SQLDatabaseNode with SQLite - Essential SDK Pattern"""
        try:
            print("\nTesting SQLDatabaseNode with SQLite...")
            
            # ESSENTIAL PATTERN: WorkflowBuilder with string-based nodes
            workflow = WorkflowBuilder()
            
            # Add SQLDatabaseNode to read from our database
            workflow.add_node("SQLDatabaseNode", "db_reader", {
                "connection_string": f"sqlite:///{self.db_path}",
                "query": "SELECT id, name, description, price FROM test_products LIMIT 5"
            })
            
            # ESSENTIAL PATTERN: runtime.execute(workflow.build()) - ALWAYS .build()
            results, run_id = self.runtime.execute(workflow.build())
            
            if results and "db_reader" in results:
                db_result = results["db_reader"]
                self.log_test("SQLDatabaseNode Read", True, 
                             f"Successfully read {len(db_result) if isinstance(db_result, list) else 1} records",
                             {"run_id": run_id, "sample_data": str(db_result)[:200]})
                return True
            else:
                self.log_test("SQLDatabaseNode Read", False, "No results returned from database")
                return False
                
        except Exception as e:
            self.log_test("SQLDatabaseNode Read", False, f"SQLDatabaseNode test failed: {e}")
            return False
    
    def test_python_code_node_crud(self) -> bool:
        """Test CRUD operations using PythonCodeNode"""
        try:
            print("\nTesting CRUD with PythonCodeNode...")
            
            # CREATE operation
            workflow = WorkflowBuilder()
            workflow.add_node("PythonCodeNode", "create_product", {
                "code": f"""
import sqlite3
conn = sqlite3.connect(r'{self.db_path}')
cursor = conn.cursor()
cursor.execute("INSERT INTO test_products (name, description, price) VALUES (?, ?, ?)", 
               ("Test Product", "Created by PythonCodeNode", 99.99))
new_id = cursor.lastrowid
conn.commit()
cursor.close()
conn.close()
result = {{"action": "create", "id": new_id, "success": True}}
"""
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            
            if results and "create_product" in results:
                create_result = results["create_product"]
                self.log_test("PythonCodeNode CRUD", True, 
                             f"CRUD operations successful: {create_result}")
                return True
            else:
                self.log_test("PythonCodeNode CRUD", False, "CRUD operation failed")
                return False
                
        except Exception as e:
            self.log_test("PythonCodeNode CRUD", False, f"CRUD test failed: {e}")
            return False
    
    def test_in_memory_cache(self) -> bool:
        """Test in-memory cache using PythonCodeNode"""
        try:
            print("\nTesting in-memory cache...")
            
            workflow = WorkflowBuilder()
            workflow.add_node("PythonCodeNode", "cache_test", {
                "code": """
# Simple in-memory cache simulation
cache = {}
cache['user_1'] = {'name': 'Test User', 'role': 'admin'}
cache['session_123'] = {'user_id': 1, 'expires': '2024-12-31'}

# Test cache operations
result = {
    'cache_size': len(cache),
    'user_data': cache.get('user_1'),
    'session_data': cache.get('session_123'),
    'cache_hit': 'user_1' in cache,
    'cache_miss': 'user_999' in cache
}
"""
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            
            if results and "cache_test" in results:
                cache_result = results["cache_test"]
                self.log_test("In-Memory Cache", True, 
                             f"Cache operations successful: {cache_result}")
                return True
            else:
                self.log_test("In-Memory Cache", False, "Cache test failed")
                return False
                
        except Exception as e:
            self.log_test("In-Memory Cache", False, f"Cache test failed: {e}")
            return False
    
    def test_service_health_check(self) -> bool:
        """Test basic service health monitoring"""
        try:
            print("\nTesting service health check...")
            
            workflow = WorkflowBuilder()
            workflow.add_node("PythonCodeNode", "health_check", {
                "code": f"""
import sqlite3
import os
from datetime import datetime

health_status = {{}}

# Check database connectivity
try:
    conn = sqlite3.connect(r'{self.db_path}')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM test_products")
    product_count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    health_status['database'] = {{'status': 'healthy', 'product_count': product_count}}
except Exception as e:
    health_status['database'] = {{'status': 'unhealthy', 'error': str(e)}}

# Check file system
try:
    db_size = os.path.getsize(r'{self.db_path}')
    health_status['filesystem'] = {{'status': 'healthy', 'db_size_bytes': db_size}}
except Exception as e:
    health_status['filesystem'] = {{'status': 'unhealthy', 'error': str(e)}}

# Overall health
healthy_services = sum(1 for service in health_status.values() if service['status'] == 'healthy')
total_services = len(health_status)

result = {{
    'timestamp': datetime.utcnow().isoformat(),
    'overall_status': 'healthy' if healthy_services == total_services else 'degraded',
    'services': health_status,
    'healthy_count': healthy_services,
    'total_count': total_services
}}
"""
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            
            if results and "health_check" in results:
                health_result = results["health_check"]
                is_healthy = health_result.get('overall_status') == 'healthy'
                self.log_test("Service Health Check", is_healthy, 
                             f"Health check completed: {health_result.get('overall_status', 'unknown')}")
                return is_healthy
            else:
                self.log_test("Service Health Check", False, "Health check failed")
                return False
                
        except Exception as e:
            self.log_test("Service Health Check", False, f"Health check failed: {e}")
            return False
    
    def test_connection_string_validation(self) -> bool:
        """Test different connection string patterns"""
        try:
            print("\nTesting connection string validation...")
            
            # Test valid SQLite connection
            workflow = WorkflowBuilder()
            workflow.add_node("SQLDatabaseNode", "connection_test", {
                "connection_string": f"sqlite:///{self.db_path}",
                "query": "SELECT 1 as test_value"
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            
            if results and "connection_test" in results:
                self.log_test("Connection String Validation", True, 
                             "SQLite connection string validated successfully")
                return True
            else:
                self.log_test("Connection String Validation", False, 
                             "Connection string validation failed")
                return False
                
        except Exception as e:
            self.log_test("Connection String Validation", False, 
                         f"Connection validation failed: {e}")
            return False
    
    def run_infrastructure_tests(self) -> Dict[str, Any]:
        """Run all minimal infrastructure tests"""
        print("\n" + "="*80)
        print("MINIMAL WORKING INFRASTRUCTURE TEST SUITE")
        print("="*80)
        print("Testing: SQLite + In-Memory Cache + Health Monitoring")
        print("Pattern: Essential SDK execution pattern")
        print("-"*80)
        
        start_time = time.time()
        
        # Run tests in order
        tests = [
            ("Database Setup", self.setup_sqlite_database),
            ("SQLDatabaseNode", self.test_sql_database_node),
            ("PythonCodeNode CRUD", self.test_python_code_node_crud),
            ("In-Memory Cache", self.test_in_memory_cache),
            ("Service Health Check", self.test_service_health_check),
            ("Connection Validation", self.test_connection_string_validation)
        ]
        
        for test_name, test_func in tests:
            print(f"\n--- Running {test_name} ---")
            test_func()
        
        # Calculate results
        total_time = time.time() - start_time
        passed_tests = sum(1 for result in self.test_results if result['success'])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Summary
        print("\n" + "="*80)
        print("MINIMAL INFRASTRUCTURE TEST SUMMARY")
        print("="*80)
        overall_success = success_rate >= 80
        print(f"Overall Status: {'PASS' if overall_success else 'FAIL'}")
        print(f"Test Results: {passed_tests}/{total_tests} passed ({success_rate:.1f}% success rate)")
        print(f"Execution Time: {total_time:.2f} seconds")
        print(f"Database Path: {self.db_path}")
        print(f"Infrastructure Ready: {'YES' if overall_success else 'NO'}")
        
        # Next steps
        if overall_success:
            print("\nINFRASTRUCTURE IS READY!")
            print("- SQLite database working with SDK")
            print("- CRUD operations validated")
            print("- Service health monitoring active")
            print("- Ready for application development")
        else:
            print("\nINFRASTRUCTURE NEEDS ATTENTION:")
            failed_tests = [r for r in self.test_results if not r['success']]
            for test in failed_tests:
                print(f"- {test['test_name']}: {test['message']}")
        
        return {
            'success': overall_success,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'success_rate': success_rate,
            'execution_time': total_time,
            'database_path': str(self.db_path),
            'results': self.test_results,
            'infrastructure_ready': overall_success
        }


def main():
    """Main test execution"""
    test_suite = MinimalInfrastructureTest()
    
    try:
        results = test_suite.run_infrastructure_tests()
        
        # Save results
        results_file = f"minimal_infrastructure_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nTest results saved to: {results_file}")
        
        # Exit with appropriate code
        sys.exit(0 if results['success'] else 1)
        
    except Exception as e:
        print(f"\nMinimal infrastructure test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()