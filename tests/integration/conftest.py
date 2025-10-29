"""Integration test configuration and fixtures for Horme POV system.

This module provides test fixtures and configuration for integration testing
following the 3-tier testing strategy with real infrastructure.
"""

import pytest
import sqlite3
import json
import time
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import tempfile
import shutil
import os

# Test Infrastructure Setup
@pytest.fixture(scope="session")
def test_database_path():
    """Path to the real products database with 17,266 products."""
    db_path = Path(__file__).parent.parent.parent / "products.db"
    if not db_path.exists():
        pytest.skip("Products database not found. Run product import first.")
    return str(db_path)

@pytest.fixture(scope="session") 
def test_quotations_db_path():
    """Path to the quotations database."""
    db_path = Path(__file__).parent.parent.parent / "quotations.db"
    return str(db_path)

@pytest.fixture(scope="session")
def test_documents_db_path():
    """Path to the documents database."""
    db_path = Path(__file__).parent.parent.parent / "documents.db"
    return str(db_path)

@pytest.fixture(scope="function")
def database_connection(test_database_path):
    """Real database connection for integration tests - NO MOCKING."""
    conn = sqlite3.connect(test_database_path)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    yield conn
    conn.close()

@pytest.fixture(scope="function")
def quotations_connection(test_quotations_db_path):
    """Real quotations database connection - NO MOCKING."""
    conn = sqlite3.connect(test_quotations_db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()

@pytest.fixture(scope="function")
def documents_connection(test_documents_db_path):
    """Real documents database connection - NO MOCKING."""
    conn = sqlite3.connect(test_documents_db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()

@pytest.fixture(scope="function")
def sample_products(database_connection):
    """Get sample products from real database."""
    cursor = database_connection.cursor()
    cursor.execute("""
        SELECT id, sku, name, description, category_id, brand_id, status, availability
        FROM products 
        WHERE status = 'active' AND is_published = 1
        LIMIT 10
    """)
    return cursor.fetchall()

@pytest.fixture(scope="function")
def test_categories(database_connection):
    """Get categories from real database."""
    cursor = database_connection.cursor()
    cursor.execute("SELECT id, name FROM categories")
    return cursor.fetchall()

@pytest.fixture(scope="function")
def test_brands(database_connection):
    """Get brands from real database."""
    cursor = database_connection.cursor()
    cursor.execute("SELECT id, name FROM brands") 
    return cursor.fetchall()

# Performance Testing Fixtures
@pytest.fixture(scope="function")
def performance_metrics():
    """Track performance metrics during tests."""
    metrics = {
        'start_time': time.time(),
        'memory_usage': [],
        'query_times': [],
        'errors': []
    }
    yield metrics
    metrics['end_time'] = time.time()
    metrics['total_duration'] = metrics['end_time'] - metrics['start_time']

@pytest.fixture(scope="function")
def concurrent_test_data():
    """Data for concurrent user testing."""
    return {
        'user_count': 10,
        'requests_per_user': 5,
        'test_queries': [
            "tools for cement work",
            "cleaning products",
            "power tools",
            "safety equipment",
            "measuring tools"
        ],
        'test_categories': [1, 2, 3]
    }

# RFP Testing Fixtures
@pytest.fixture(scope="function")
def sample_rfp_document():
    """Sample RFP document content for testing."""
    return {
        'title': 'Construction Project RFP - Office Building',
        'content': """
        Project: New Office Building Construction
        Location: Downtown Business District
        Timeline: 12 months
        
        Required Materials:
        - Cement and concrete supplies
        - Power tools for construction
        - Safety equipment for workers
        - Cleaning supplies for maintenance
        - Measuring and surveying tools
        - Electrical components
        
        Budget: $500,000 for materials
        Deadline: Submit proposals by end of month
        """,
        'requirements': [
            'cement supplies',
            'power tools', 
            'safety equipment',
            'cleaning supplies',
            'measuring tools'
        ]
    }

@pytest.fixture(scope="function")
def sample_work_description():
    """Sample work description for recommendation testing."""
    return {
        'work_type': 'Commercial Construction',
        'description': 'Building a 5-story office complex with retail space on ground floor',
        'materials_needed': [
            'concrete and cement',
            'power tools',
            'safety gear',
            'cleaning products',
            'measurement equipment'
        ],
        'budget_range': '100000-500000',
        'timeline': '12 months'
    }

# Error Handling Test Fixtures
@pytest.fixture(scope="function")
def invalid_test_data():
    """Invalid data for error handling tests."""
    return {
        'invalid_product_ids': [-1, 0, 999999, 'invalid'],
        'invalid_categories': [-1, 'nonexistent', None],
        'invalid_search_terms': ['', None, '   ', 'xyzinvalidterm'],
        'malformed_requests': [
            {},
            {'invalid': 'structure'},
            {'missing_required_fields': True}
        ]
    }

# Test Data Cleanup
@pytest.fixture(scope="function", autouse=True)
def cleanup_test_data():
    """Clean up test data after each test - maintains real database integrity."""
    # Setup: Note starting state
    yield
    # Teardown: Clean up any test-specific data if created
    # Note: We don't modify the main products data, only test-specific additions

# Report Generation Fixtures
@pytest.fixture(scope="session")
def test_report_dir():
    """Directory for test reports."""
    report_dir = Path(__file__).parent.parent.parent / "test_output" / "integration_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir

@pytest.fixture(scope="function")
def test_metrics_collector():
    """Collect metrics during test execution."""
    metrics = {
        'test_name': None,
        'start_time': None,
        'end_time': None,
        'duration_ms': None,
        'database_queries': 0,
        'records_processed': 0,
        'errors_encountered': 0,
        'memory_peak_mb': 0,
        'success': True
    }
    
    def start_test(test_name: str):
        metrics['test_name'] = test_name
        metrics['start_time'] = time.time()
    
    def end_test():
        metrics['end_time'] = time.time()
        metrics['duration_ms'] = (metrics['end_time'] - metrics['start_time']) * 1000
    
    def add_query():
        metrics['database_queries'] += 1
    
    def add_records(count: int):
        metrics['records_processed'] += count
    
    def add_error():
        metrics['errors_encountered'] += 1
        metrics['success'] = False
    
    metrics['start_test'] = start_test
    metrics['end_test'] = end_test
    metrics['add_query'] = add_query
    metrics['add_records'] = add_records
    metrics['add_error'] = add_error
    
    return metrics

# API Testing Configuration
@pytest.fixture(scope="session")
def api_test_config():
    """Configuration for API endpoint testing."""
    return {
        'base_url': 'http://localhost:8000',  # Assumes API server running
        'timeout': 30,
        'max_retries': 3,
        'test_endpoints': [
            '/api/products/search',
            '/api/products/{id}',
            '/api/quotations',
            '/api/rfp/analyze',
            '/api/recommendations/work-based'
        ]
    }

# Integration Test Categories
def pytest_configure(config):
    """Configure pytest markers for integration tests."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires real services)"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database access"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance/load test"
    )
    config.addinivalue_line(
        "markers", "error_handling: mark test as error handling validation"
    )
    config.addinivalue_line(
        "markers", "cross_service: mark test as cross-service integration"
    )