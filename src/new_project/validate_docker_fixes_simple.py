#!/usr/bin/env python3
"""
Simple DataFlow Docker PostgreSQL Fixes Validation
================================================

Simple validation script to test Docker PostgreSQL fixes without Unicode issues.
"""

import os
import sys
from datetime import datetime

def test_model_imports():
    """Test that models can be imported without syntax errors."""
    print("Testing model imports...")
    try:
        # Test imports with windows compatibility first
        import windows_sdk_compatibility
        from dataflow_classification_models import (
            Company, User, Customer, Quote, ProductClassification,
            ClassificationHistory, ClassificationCache, ETIMAttribute,
            ClassificationRule, ClassificationFeedback, ClassificationMetrics,
            is_docker_environment, db
        )
        print("  PASS: All models imported successfully")
        return True
    except Exception as e:
        print(f"  FAIL: Failed to import models: {e}")
        return False

def test_syntax_fixes():
    """Test that PostgreSQL syntax errors are fixed."""
    print("Testing PostgreSQL syntax fixes...")
    try:
        from dataflow_classification_models import User, Quote, ProductClassification
        
        # Check that Dict/List fields default to None instead of {} or []
        issues = []
        
        # Test User notification_preferences
        if hasattr(User, '__annotations__'):
            for field_name in User.__annotations__:
                if field_name == 'notification_preferences':
                    default_val = getattr(User, field_name, 'NOT_FOUND')
                    if default_val != None and default_val != 'NOT_FOUND':
                        issues.append(f"User.notification_preferences has invalid default: {default_val}")
        
        # Test Quote line_items  
        if hasattr(Quote, '__annotations__'):
            for field_name in Quote.__annotations__:
                if field_name == 'line_items':
                    default_val = getattr(Quote, field_name, 'NOT_FOUND')
                    if default_val != None and default_val != 'NOT_FOUND':
                        issues.append(f"Quote.line_items has invalid default: {default_val}")
        
        if issues:
            print(f"  FAIL: Found syntax issues: {issues}")
            return False
        else:
            print("  PASS: PostgreSQL syntax fixes verified")
            return True
            
    except Exception as e:
        print(f"  FAIL: Error checking syntax fixes: {e}")
        return False

def test_docker_environment_detection():
    """Test Docker environment detection."""
    print("Testing Docker environment detection...")
    try:
        from dataflow_classification_models import is_docker_environment
        
        # Save original environment
        original_env = dict(os.environ)
        
        # Test non-Docker environment
        os.environ.pop('CONTAINER_ENV', None)
        os.environ.pop('DATABASE_URL', None)
        os.environ.pop('REDIS_URL', None)
        
        is_docker_clean = is_docker_environment()
        
        # Test Docker environment
        os.environ['CONTAINER_ENV'] = 'docker'
        is_docker_with_env = is_docker_environment()
        
        # Restore environment
        os.environ.clear()
        os.environ.update(original_env)
        
        if not is_docker_clean and is_docker_with_env:
            print("  PASS: Docker environment detection working")
            return True
        else:
            print(f"  FAIL: Docker detection failed. Clean: {is_docker_clean}, With env: {is_docker_with_env}")
            return False
            
    except Exception as e:
        print(f"  FAIL: Error testing Docker detection: {e}")
        return False

def test_configuration_files():
    """Test that required configuration files exist."""
    print("Testing configuration files...")
    
    required_files = [
        "config/dataflow_docker.py",
        "init-scripts/postgres-dataflow-docker.sql", 
        "docker-compose.production.yml"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"  FAIL: Missing files: {missing_files}")
        return False
    else:
        print("  PASS: All configuration files present")
        return True

def test_docker_compose_configuration():
    """Test Docker Compose configuration."""
    print("Testing Docker Compose configuration...")
    
    try:
        with open("docker-compose.production.yml", 'r') as f:
            content = f.read()
        
        required_items = [
            'postgres:5432',  # Service name usage
            'redis:6379',     # Service name usage  
            'CONTAINER_ENV=docker',  # Docker environment flag
            'postgres-dataflow-docker.sql',  # DataFlow init script
            'DATAFLOW_MONITORING=true',  # DataFlow configuration
        ]
        
        missing_items = []
        for item in required_items:
            if item not in content:
                missing_items.append(item)
        
        if missing_items:
            print(f"  FAIL: Missing Docker Compose items: {missing_items}")
            return False
        else:
            print("  PASS: Docker Compose configuration valid")
            return True
            
    except Exception as e:
        print(f"  FAIL: Error checking Docker Compose: {e}")
        return False

def test_init_script_content():
    """Test PostgreSQL init script content."""
    print("Testing PostgreSQL init script...")
    
    try:
        with open("init-scripts/postgres-dataflow-docker.sql", 'r') as f:
            content = f.read()
        
        required_elements = [
            'CREATE EXTENSION IF NOT EXISTS "pgvector"',
            'CREATE SCHEMA IF NOT EXISTS dataflow_classification',
            'docker_health_check',
            'horme_user'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"  FAIL: Missing init script elements: {missing_elements}")
            return False
        else:
            print("  PASS: PostgreSQL init script valid")
            return True
            
    except Exception as e:
        print(f"  FAIL: Error checking init script: {e}")
        return False

def main():
    """Run all validation tests."""
    print("DataFlow Docker PostgreSQL Fixes Validation")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    tests = [
        test_model_imports,
        test_syntax_fixes,
        test_docker_environment_detection, 
        test_configuration_files,
        test_docker_compose_configuration,
        test_init_script_content
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ERROR: Test failed with exception: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\nSUCCESS: All DataFlow Docker PostgreSQL fixes validated!")
        return 0
    else:
        print(f"\nFAILED: {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())