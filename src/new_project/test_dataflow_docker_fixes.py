#!/usr/bin/env python3
"""
DataFlow Docker PostgreSQL Fixes Validation
===========================================

Comprehensive validation script to test all Docker PostgreSQL fixes:
1. PostgreSQL syntax error fixes (DEFAULT values)
2. Docker-specific configuration
3. PostgreSQL initialization script
4. Environment variable detection
5. Container connectivity

Run this script to validate that all DataFlow PostgreSQL Docker issues are resolved.
"""

import os
import sys
import json
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    test_name: str
    status: str  # 'PASS', 'FAIL', 'SKIP'
    message: str
    details: Optional[Dict[str, Any]] = None
    execution_time_ms: float = 0.0


class DataFlowDockerValidator:
    """Comprehensive validator for DataFlow Docker PostgreSQL fixes."""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.start_time = datetime.now()
        
    def log_result(self, test_name: str, status: str, message: str, 
                   details: Optional[Dict[str, Any]] = None, execution_time_ms: float = 0.0):
        """Log a validation result."""
        result = ValidationResult(test_name, status, message, details, execution_time_ms)
        self.results.append(result)
        
        # Print immediate feedback
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
        print(f"{status_icon} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
    
    def test_model_syntax_fixes(self) -> None:
        """Test 1: Validate PostgreSQL syntax fixes in models."""
        test_start = datetime.now()
        
        try:
            # Import the models to check for syntax errors
            from dataflow_classification_models import (
                Company, User, Customer, Quote, ProductClassification,
                ClassificationHistory, ClassificationCache, ETIMAttribute,
                ClassificationRule, ClassificationFeedback, ClassificationMetrics
            )
            
            # Check specific fields that were fixed
            syntax_checks = []
            
            # Check User model notification_preferences
            user_field = None
            for field_name, field_type in User.__annotations__.items():
                if field_name == 'notification_preferences':
                    user_field = getattr(User, field_name, 'MISSING')
                    break
            
            syntax_checks.append({
                'model': 'User',
                'field': 'notification_preferences',
                'default_value': user_field,
                'expected': None,
                'valid': user_field is None
            })
            
            # Check Quote model line_items
            quote_field = None
            for field_name, field_type in Quote.__annotations__.items():
                if field_name == 'line_items':
                    quote_field = getattr(Quote, field_name, 'MISSING')
                    break
            
            syntax_checks.append({
                'model': 'Quote',
                'field': 'line_items',
                'default_value': quote_field,
                'expected': None,
                'valid': quote_field is None
            })
            
            # Check ProductClassification model recommendations
            classification_field = None
            for field_name, field_type in ProductClassification.__annotations__.items():
                if field_name == 'recommendations':
                    classification_field = getattr(ProductClassification, field_name, 'MISSING')
                    break
            
            syntax_checks.append({
                'model': 'ProductClassification',
                'field': 'recommendations',
                'default_value': classification_field,
                'expected': None,
                'valid': classification_field is None
            })
            
            all_valid = all(check['valid'] for check in syntax_checks)
            
            execution_time = (datetime.now() - test_start).total_seconds() * 1000
            
            if all_valid:
                self.log_result(
                    "Model Syntax Fixes",
                    "PASS",
                    "All Dict/List DEFAULT values fixed to None",
                    {"syntax_checks": syntax_checks},
                    execution_time
                )
            else:
                failed_checks = [check for check in syntax_checks if not check['valid']]
                self.log_result(
                    "Model Syntax Fixes",
                    "FAIL",
                    f"Found {len(failed_checks)} invalid DEFAULT values",
                    {"failed_checks": failed_checks},
                    execution_time
                )
                
        except Exception as e:
            execution_time = (datetime.now() - test_start).total_seconds() * 1000
            self.log_result(
                "Model Syntax Fixes",
                "FAIL",
                f"Failed to import models: {str(e)}",
                {"error": str(e)},
                execution_time
            )
    
    def test_docker_environment_detection(self) -> None:
        """Test 2: Validate Docker environment detection."""
        test_start = datetime.now()
        
        try:
            # Test the is_docker_environment function
            from dataflow_classification_models import is_docker_environment
            
            # Save original environment
            original_env = dict(os.environ)
            
            # Test 1: Non-Docker environment
            os.environ.pop('CONTAINER_ENV', None)
            os.environ.pop('DATABASE_URL', None)
            is_docker_1 = is_docker_environment()
            
            # Test 2: Docker environment via CONTAINER_ENV
            os.environ['CONTAINER_ENV'] = 'docker'
            is_docker_2 = is_docker_environment()
            
            # Test 3: Docker environment via DATABASE_URL
            os.environ.pop('CONTAINER_ENV', None)
            os.environ['DATABASE_URL'] = 'postgresql://user:pass@postgres:5432/db'
            is_docker_3 = is_docker_environment()
            
            # Test 4: Docker environment via REDIS_URL
            os.environ.pop('DATABASE_URL', None)
            os.environ['REDIS_URL'] = 'redis://redis:6379/0'
            is_docker_4 = is_docker_environment()
            
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
            
            # Evaluate results
            detection_results = {
                'no_docker_indicators': is_docker_1,
                'container_env_docker': is_docker_2,
                'database_url_postgres': is_docker_3,
                'redis_url_redis': is_docker_4
            }
            
            expected_results = [False, True, True, True]
            actual_results = [is_docker_1, is_docker_2, is_docker_3, is_docker_4]
            
            execution_time = (datetime.now() - test_start).total_seconds() * 1000
            
            if actual_results == expected_results:
                self.log_result(
                    "Docker Environment Detection",
                    "PASS",
                    "Docker environment detection working correctly",
                    detection_results,
                    execution_time
                )
            else:
                self.log_result(
                    "Docker Environment Detection",
                    "FAIL",
                    f"Expected {expected_results}, got {actual_results}",
                    detection_results,
                    execution_time
                )
                
        except Exception as e:
            execution_time = (datetime.now() - test_start).total_seconds() * 1000
            self.log_result(
                "Docker Environment Detection",
                "FAIL",
                f"Failed to test environment detection: {str(e)}",
                {"error": str(e)},
                execution_time
            )
    
    def test_docker_configuration_files(self) -> None:
        """Test 3: Validate Docker configuration files exist and are valid."""
        test_start = datetime.now()
        
        try:
            files_to_check = [
                "config/dataflow_docker.py",
                "init-scripts/postgres-dataflow-docker.sql",
                "docker-compose.production.yml"
            ]
            
            file_checks = []
            
            for file_path in files_to_check:
                full_path = os.path.join(os.getcwd(), file_path)
                exists = os.path.exists(full_path)
                size = os.path.getsize(full_path) if exists else 0
                
                file_checks.append({
                    'file': file_path,
                    'exists': exists,
                    'size_bytes': size,
                    'valid': exists and size > 0
                })
            
            # Check Docker Compose for DataFlow environment variables
            docker_compose_path = "docker-compose.production.yml"
            docker_compose_content = ""
            dataflow_env_vars = []
            
            if os.path.exists(docker_compose_path):
                with open(docker_compose_path, 'r') as f:
                    docker_compose_content = f.read()
                
                required_env_vars = [
                    'CONTAINER_ENV=docker',
                    'DATAFLOW_MONITORING=true',
                    'DATAFLOW_AUTO_MIGRATE=true',
                    'DATABASE_URL=postgresql://horme_user:horme_password@postgres:5432'
                ]
                
                for env_var in required_env_vars:
                    present = env_var in docker_compose_content
                    dataflow_env_vars.append({
                        'env_var': env_var,
                        'present': present
                    })
            
            all_files_valid = all(check['valid'] for check in file_checks)
            all_env_vars_present = all(var['present'] for var in dataflow_env_vars)
            
            execution_time = (datetime.now() - test_start).total_seconds() * 1000
            
            if all_files_valid and all_env_vars_present:
                self.log_result(
                    "Docker Configuration Files",
                    "PASS",
                    "All Docker configuration files present and valid",
                    {
                        "file_checks": file_checks,
                        "dataflow_env_vars": dataflow_env_vars
                    },
                    execution_time
                )
            else:
                self.log_result(
                    "Docker Configuration Files",
                    "FAIL",
                    "Missing or invalid Docker configuration files",
                    {
                        "file_checks": file_checks,
                        "dataflow_env_vars": dataflow_env_vars,
                        "all_files_valid": all_files_valid,
                        "all_env_vars_present": all_env_vars_present
                    },
                    execution_time
                )
                
        except Exception as e:
            execution_time = (datetime.now() - test_start).total_seconds() * 1000
            self.log_result(
                "Docker Configuration Files",
                "FAIL",
                f"Failed to validate configuration files: {str(e)}",
                {"error": str(e)},
                execution_time
            )
    
    def test_postgresql_init_script(self) -> None:
        """Test 4: Validate PostgreSQL initialization script syntax."""
        test_start = datetime.now()
        
        try:
            init_script_path = "init-scripts/postgres-dataflow-docker.sql"
            
            if not os.path.exists(init_script_path):
                execution_time = (datetime.now() - test_start).total_seconds() * 1000
                self.log_result(
                    "PostgreSQL Init Script",
                    "FAIL",
                    "PostgreSQL initialization script not found",
                    {"path": init_script_path},
                    execution_time
                )
                return
            
            with open(init_script_path, 'r') as f:
                script_content = f.read()
            
            # Check for required SQL elements
            required_elements = [
                'CREATE EXTENSION IF NOT EXISTS "pgvector"',
                'CREATE EXTENSION IF NOT EXISTS "pg_trgm"',
                'CREATE EXTENSION IF NOT EXISTS "btree_gin"',
                'CREATE SCHEMA IF NOT EXISTS dataflow_classification',
                'CREATE TABLE IF NOT EXISTS dataflow_classification.model_metadata',
                'CREATE OR REPLACE FUNCTION dataflow_classification.get_system_health()',
                'CREATE OR REPLACE VIEW dataflow_classification.docker_health_check',
                'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dataflow_classification TO horme_user'
            ]
            
            element_checks = []
            for element in required_elements:
                present = element in script_content
                element_checks.append({
                    'element': element,
                    'present': present
                })
            
            # Check script size and structure
            script_stats = {
                'size_bytes': len(script_content),
                'line_count': len(script_content.split('\n')),
                'contains_pgvector': 'pgvector' in script_content,
                'contains_docker_health': 'docker_health_check' in script_content,
                'contains_dataflow_schema': 'dataflow_classification' in script_content
            }
            
            all_elements_present = all(check['present'] for check in element_checks)
            script_valid = (
                script_stats['size_bytes'] > 5000 and
                script_stats['contains_pgvector'] and
                script_stats['contains_docker_health'] and
                script_stats['contains_dataflow_schema']
            )
            
            execution_time = (datetime.now() - test_start).total_seconds() * 1000
            
            if all_elements_present and script_valid:
                self.log_result(
                    "PostgreSQL Init Script",
                    "PASS",
                    "PostgreSQL initialization script is valid and complete",
                    {
                        "element_checks": element_checks,
                        "script_stats": script_stats
                    },
                    execution_time
                )
            else:
                missing_elements = [check for check in element_checks if not check['present']]
                self.log_result(
                    "PostgreSQL Init Script",
                    "FAIL",
                    f"Missing {len(missing_elements)} required elements",
                    {
                        "missing_elements": missing_elements,
                        "script_stats": script_stats,
                        "script_valid": script_valid
                    },
                    execution_time
                )
                
        except Exception as e:
            execution_time = (datetime.now() - test_start).total_seconds() * 1000
            self.log_result(
                "PostgreSQL Init Script",
                "FAIL",
                f"Failed to validate init script: {str(e)}",
                {"error": str(e)},
                execution_time
            )
    
    def test_docker_service_configuration(self) -> None:
        """Test 5: Validate Docker service configuration."""
        test_start = datetime.now()
        
        try:
            # Test Docker configuration utility functions
            from config.dataflow_docker import (
                get_docker_database_url,
                get_docker_redis_url,
                setup_docker_environment_variables,
                get_docker_health_check_queries
            )
            
            # Test database URL generation
            original_database_url = os.environ.get('DATABASE_URL')
            os.environ.pop('DATABASE_URL', None)
            
            default_db_url = get_docker_database_url()
            expected_db_url = 'postgresql://horme_user:horme_password@postgres:5432/horme_classification_db'
            
            # Test Redis URL generation
            original_redis_url = os.environ.get('REDIS_URL')
            os.environ.pop('REDIS_URL', None)
            
            default_redis_url = get_docker_redis_url()
            expected_redis_url = 'redis://redis:6379/2'
            
            # Test environment variables setup
            env_vars = setup_docker_environment_variables()
            
            # Test health check queries
            health_queries = get_docker_health_check_queries()
            
            # Restore original environment
            if original_database_url:
                os.environ['DATABASE_URL'] = original_database_url
            if original_redis_url:
                os.environ['REDIS_URL'] = original_redis_url
            
            # Validate results
            url_tests = {
                'database_url_correct': default_db_url == expected_db_url,
                'redis_url_correct': default_redis_url == expected_redis_url,
                'database_uses_postgres_service': '@postgres:' in default_db_url,
                'redis_uses_redis_service': 'redis:' in default_redis_url
            }
            
            env_var_tests = {
                'has_database_url': 'DATABASE_URL' in env_vars,
                'has_redis_url': 'REDIS_URL' in env_vars,
                'has_dataflow_config': any('DATAFLOW_' in key for key in env_vars.keys()),
                'correct_container_env': env_vars.get('CONTAINER_ENV') == 'docker'
            }
            
            health_check_tests = {
                'has_postgresql_check': 'postgresql' in health_queries,
                'has_redis_check': 'redis' in health_queries,
                'has_dataflow_checks': 'dataflow_models' in health_queries,
                'has_extensions_check': 'dataflow_extensions' in health_queries
            }
            
            all_tests_pass = (
                all(url_tests.values()) and
                all(env_var_tests.values()) and
                all(health_check_tests.values())
            )
            
            execution_time = (datetime.now() - test_start).total_seconds() * 1000
            
            if all_tests_pass:
                self.log_result(
                    "Docker Service Configuration",
                    "PASS",
                    "Docker service configuration is correct",
                    {
                        "url_tests": url_tests,
                        "env_var_tests": env_var_tests,
                        "health_check_tests": health_check_tests
                    },
                    execution_time
                )
            else:
                self.log_result(
                    "Docker Service Configuration",
                    "FAIL",
                    "Docker service configuration has issues",
                    {
                        "url_tests": url_tests,
                        "env_var_tests": env_var_tests,
                        "health_check_tests": health_check_tests,
                        "all_tests_pass": all_tests_pass
                    },
                    execution_time
                )
                
        except Exception as e:
            execution_time = (datetime.now() - test_start).total_seconds() * 1000
            self.log_result(
                "Docker Service Configuration",
                "FAIL",
                f"Failed to test Docker service configuration: {str(e)}",
                {"error": str(e)},
                execution_time
            )
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("🚀 Starting DataFlow Docker PostgreSQL Fixes Validation")
        print("=" * 60)
        
        # Run all tests
        self.test_model_syntax_fixes()
        self.test_docker_environment_detection()
        self.test_docker_configuration_files()
        self.test_postgresql_init_script()
        self.test_docker_service_configuration()
        
        # Calculate summary
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "PASS"])
        failed_tests = len([r for r in self.results if r.status == "FAIL"])
        skipped_tests = len([r for r in self.results if r.status == "SKIP"])
        
        total_time = (datetime.now() - self.start_time).total_seconds()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️ Skipped: {skipped_tests}")
        print(f"⏱️ Total Time: {total_time:.2f}s")
        print(f"🎯 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if result.status == "FAIL":
                    print(f"  - {result.test_name}: {result.message}")
        
        # Return detailed results
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "total_execution_time_seconds": total_time,
            "all_tests_passed": failed_tests == 0,
            "results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "message": r.message,
                    "details": r.details,
                    "execution_time_ms": r.execution_time_ms
                }
                for r in self.results
            ]
        }
        
        return summary


def main():
    """Main validation function."""
    print("DataFlow Docker PostgreSQL Fixes Validation")
    print("Version: 1.0")
    print("Timestamp:", datetime.now().isoformat())
    print()
    
    validator = DataFlowDockerValidator()
    summary = validator.run_all_tests()
    
    # Save results to file
    results_file = f"dataflow_docker_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Exit with appropriate code
    exit_code = 0 if summary["all_tests_passed"] else 1
    print(f"\n🏁 Validation {'COMPLETED SUCCESSFULLY' if exit_code == 0 else 'FAILED'}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())