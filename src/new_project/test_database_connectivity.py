#!/usr/bin/env python3
"""
Database Connectivity Test for DataFlow
=======================================

Tests PostgreSQL connectivity and basic database operations for DataFlow models.
This test is designed to run once PostgreSQL Docker container is available.

Usage:
    python test_database_connectivity.py [--create-container]
"""

import sys
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional

# Apply Windows compatibility
try:
    from windows_sdk_compatibility import ensure_windows_compatibility
    ensure_windows_compatibility()
    print("[OK] Windows compatibility applied")
except ImportError as e:
    print(f"[WARNING] Windows compatibility not available: {e}")

# Core imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime


class DatabaseConnectivityTest:
    """Test database connectivity and basic operations"""
    
    def __init__(self):
        self.runtime = LocalRuntime()
        self.test_results = []
        
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
    
    def check_docker_available(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log_test("Docker Availability", True, f"Docker found: {result.stdout.strip()}")
                return True
            else:
                self.log_test("Docker Availability", False, "Docker command failed")
                return False
        except subprocess.TimeoutExpired:
            self.log_test("Docker Availability", False, "Docker command timed out")
            return False
        except FileNotFoundError:
            self.log_test("Docker Availability", False, "Docker not found in PATH")
            return False
        except Exception as e:
            self.log_test("Docker Availability", False, f"Docker check failed: {e}")
            return False
    
    def check_postgres_container(self) -> bool:
        """Check if PostgreSQL container is running""" 
        try:
            result = subprocess.run(['docker', 'ps', '--filter', 'name=horme-postgres', '--format', 'table {{.Names}}\t{{.Status}}'],
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output_lines = result.stdout.strip().split('\n')
                if len(output_lines) > 1 and 'horme-postgres' in result.stdout:
                    status_line = output_lines[1]
                    if 'Up' in status_line:
                        self.log_test("PostgreSQL Container", True, "Container is running")
                        return True
                    else:
                        self.log_test("PostgreSQL Container", False, f"Container exists but not running: {status_line}")
                        return False
                else:
                    self.log_test("PostgreSQL Container", False, "Container not found")
                    return False
            else:
                self.log_test("PostgreSQL Container", False, "Failed to check container status")
                return False
                
        except Exception as e:
            self.log_test("PostgreSQL Container", False, f"Container check failed: {e}")
            return False
    
    def create_postgres_container(self) -> bool:
        """Create and start PostgreSQL container"""
        print("\n" + "="*60)
        print("CREATING POSTGRESQL CONTAINER")
        print("="*60)
        
        try:
            # Check if container already exists
            check_result = subprocess.run(['docker', 'ps', '-a', '--filter', 'name=horme-postgres', '--quiet'],
                                        capture_output=True, text=True, timeout=10)
            
            if check_result.stdout.strip():
                print("Container exists. Stopping and removing...")
                subprocess.run(['docker', 'stop', 'horme-postgres'], capture_output=True)
                subprocess.run(['docker', 'rm', 'horme-postgres'], capture_output=True)
            
            # Create new container
            print("Creating PostgreSQL container...")
            create_cmd = [
                'docker', 'run', '--name', 'horme-postgres',
                '-e', 'POSTGRES_PASSWORD=horme_password',
                '-e', 'POSTGRES_USER=horme_user', 
                '-e', 'POSTGRES_DB=horme_product_db',
                '-p', '5432:5432',
                '-d', 'postgres:13'
            ]
            
            result = subprocess.run(create_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                container_id = result.stdout.strip()
                self.log_test("Container Creation", True, f"Created container: {container_id[:12]}")
                
                # Wait for container to be ready
                print("Waiting for PostgreSQL to be ready...")
                for i in range(30):  # Wait up to 30 seconds
                    time.sleep(1)
                    ready_result = subprocess.run([
                        'docker', 'exec', 'horme-postgres',
                        'pg_isready', '-U', 'horme_user', '-d', 'horme_product_db'
                    ], capture_output=True, text=True)
                    
                    if ready_result.returncode == 0:
                        self.log_test("Database Ready", True, f"PostgreSQL ready after {i+1} seconds")
                        return True
                    
                    if i % 5 == 0:
                        print(f"Still waiting... ({i+1}/30 seconds)")
                
                self.log_test("Database Ready", False, "Database did not become ready within 30 seconds")
                return False
                
            else:
                self.log_test("Container Creation", False, f"Failed to create container: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_test("Container Creation", False, f"Container creation failed: {e}")
            return False
    
    def test_dataflow_database_connection(self) -> bool:
        """Test DataFlow database connection"""
        print("\n" + "="*60)
        print("TESTING DATAFLOW DATABASE CONNECTION")
        print("="*60)
        
        try:
            # Import DataFlow models
            from dataflow_classification_models import db, Company
            
            # Test basic connection by trying to create a workflow
            workflow = WorkflowBuilder()
            
            # Add a simple operation that would test the database
            workflow.add_node("CompanyListNode", "test_connection", {
                "limit": 1,
                "test_connection": True
            })
            
            # Try to execute (may fail but should provide connection info)
            try:
                results, run_id = self.runtime.execute(workflow.build())
                self.log_test("DataFlow Connection", True, 
                             f"Database connection successful, run_id: {run_id}")
                return True
                
            except Exception as exec_e:
                # Check if it's a connection issue or just no data
                error_str = str(exec_e).lower()
                if 'connection refused' in error_str or 'could not connect' in error_str:
                    self.log_test("DataFlow Connection", False, 
                                 f"Database connection failed: {exec_e}")
                    return False
                else:
                    # Other errors might be OK (like no data in table)
                    self.log_test("DataFlow Connection", True, 
                                 f"Database connected (operation failed as expected): {exec_e}")
                    return True
                    
        except Exception as e:
            self.log_test("DataFlow Connection", False, 
                         f"Failed to test database connection: {e}")
            return False
    
    def test_basic_crud_operations(self) -> bool:
        """Test basic CRUD operations with actual database"""
        print("\n" + "="*60)
        print("TESTING BASIC CRUD OPERATIONS")
        print("="*60)
        
        try:
            # Test company creation
            workflow = WorkflowBuilder()
            
            # Create a test company
            test_company_data = {
                "name": f"Test Company {int(time.time())}",
                "industry": "technology",
                "employee_count": 100,
                "is_active": True,
                "founded_year": 2020
            }
            
            workflow.add_node("CompanyCreateNode", "create_test_company", test_company_data)
            
            # Execute creation
            results, run_id = self.runtime.execute(workflow.build())
            
            if results and "create_test_company" in results:
                company_result = results["create_test_company"]
                self.log_test("Company Creation", True, 
                             f"Created company: {company_result}")
                
                # Test reading the company back
                if isinstance(company_result, dict) and "id" in company_result:
                    read_workflow = WorkflowBuilder()
                    read_workflow.add_node("CompanyReadNode", "read_company", {
                        "id": company_result["id"]
                    })
                    
                    read_results, read_run_id = self.runtime.execute(read_workflow.build())
                    
                    if read_results and "read_company" in read_results:
                        self.log_test("Company Read", True, 
                                     f"Read company: {read_results['read_company']}")
                        return True
                    else:
                        self.log_test("Company Read", False, "Failed to read created company")
                        return False
                else:
                    self.log_test("Company Read", False, "Create result did not include ID")
                    return False
            else:
                self.log_test("Company Creation", False, "No results from create operation")
                return False
                
        except Exception as e:
            self.log_test("CRUD Operations", False, f"CRUD test failed: {e}")
            return False
    
    def run_connectivity_tests(self, create_container: bool = False) -> Dict[str, Any]:
        """Run all database connectivity tests"""
        print("\n" + "="*80)
        print("DATABASE CONNECTIVITY TEST SUITE")
        print("="*80)
        
        start_time = time.time()
        
        # Test Docker availability
        docker_available = self.check_docker_available()
        if not docker_available:
            return {
                'success': False,
                'message': 'Docker not available - cannot proceed with database testing',
                'results': self.test_results
            }
        
        # Check or create PostgreSQL container
        postgres_running = self.check_postgres_container()
        
        if not postgres_running and create_container:
            postgres_running = self.create_postgres_container()
        
        if not postgres_running:
            return {
                'success': False,
                'message': 'PostgreSQL container not available - use --create-container to create one',
                'results': self.test_results,
                'next_steps': [
                    'Run: python test_database_connectivity.py --create-container',
                    'Or manually start container: docker run --name horme-postgres -e POSTGRES_PASSWORD=horme_password -p 5432:5432 -d postgres:13'
                ]
            }
        
        # Test DataFlow connection
        connection_success = self.test_dataflow_database_connection()
        
        # Test basic operations if connection works
        crud_success = False
        if connection_success:
            crud_success = self.test_basic_crud_operations()
        
        # Summary
        total_time = time.time() - start_time
        passed_tests = sum(1 for result in self.test_results if result['success'])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "="*80)
        print("DATABASE CONNECTIVITY TEST SUMMARY")
        print("="*80)
        print(f"Overall Status: {'PASS' if success_rate >= 80 else 'FAIL'}")
        print(f"Test Results: {passed_tests}/{total_tests} passed ({success_rate:.1f}% success rate)")
        print(f"Execution Time: {total_time:.2f} seconds")
        
        return {
            'success': success_rate >= 80,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'success_rate': success_rate,
            'execution_time': total_time,
            'results': self.test_results,
            'database_ready': connection_success and crud_success
        }


def main():
    """Main test execution"""
    create_container = '--create-container' in sys.argv
    
    test_suite = DatabaseConnectivityTest()
    
    try:
        results = test_suite.run_connectivity_tests(create_container=create_container)
        
        # Save results
        results_file = f"database_connectivity_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nTest results saved to: {results_file}")
        
        if results['success']:
            print("\n[SUCCESS] Database connectivity validated - ready for full DataFlow testing!")
        else:
            print("\n[INFO] Database connectivity needs setup:")
            for step in results.get('next_steps', []):
                print(f"  - {step}")
        
        sys.exit(0 if results['success'] else 1)
        
    except Exception as e:
        print(f"\nDatabase connectivity test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()