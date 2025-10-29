"""Unit test configuration and fixtures for Horme POV system.

This module provides test fixtures and configuration for Tier 1 unit testing
following the 3-tier testing strategy with isolated components.
"""

import pytest
import tempfile
import sqlite3
import os
from pathlib import Path
from typing import Dict, Any
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime


@pytest.fixture(scope="function")
def runtime():
    """Provide LocalRuntime instance for testing individual nodes."""
    return LocalRuntime()


@pytest.fixture(scope="function")
def temp_directory():
    """Provide temporary directory for file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(scope="function")
def temp_database():
    """Create temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Create test database with sample data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            sku TEXT UNIQUE,
            name TEXT,
            description TEXT,
            enriched_description TEXT,
            technical_specs TEXT,
            brand_id INTEGER,
            category_id INTEGER,
            status TEXT DEFAULT 'active',
            is_published INTEGER DEFAULT 1,
            availability TEXT DEFAULT 'in_stock'
        )
    """)
    
    # Create categories table
    cursor.execute("""
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY,
            name TEXT,
            parent_id INTEGER
        )
    """)
    
    # Create brands table
    cursor.execute("""
        CREATE TABLE brands (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """)
    
    # Insert test data
    cursor.execute("INSERT INTO categories (id, name) VALUES (1, 'Tools')")
    cursor.execute("INSERT INTO categories (id, name) VALUES (2, 'Hardware')")
    cursor.execute("INSERT INTO brands (id, name) VALUES (1, 'DeWalt')")
    cursor.execute("INSERT INTO brands (id, name) VALUES (2, 'Milwaukee')")
    
    # Insert test products
    test_products = [
        (1, 'TOOL001', 'Power Drill', 'High-power cordless drill', 'Professional drill with advanced features', 'Battery: 18V, Chuck: 1/2 inch', 1, 1),
        (2, 'TOOL002', 'Circular Saw', 'Precision circular saw', 'Professional cutting tool for wood and metal', 'Blade: 7.25 inch, Power: 15A', 2, 1),
        (3, 'HARD001', 'Steel Screws', 'Galvanized steel screws', 'Corrosion-resistant fasteners', 'Material: Galvanized Steel, Size: Various', 1, 2),
    ]
    
    cursor.executemany("""
        INSERT INTO products (id, sku, name, description, enriched_description, technical_specs, brand_id, category_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, test_products)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture(scope="function")
def sample_workflow():
    """Provide a basic WorkflowBuilder instance for testing."""
    return WorkflowBuilder()


@pytest.fixture(scope="function")
def test_files():
    """Provide sample test files for document processing."""
    test_files = {}
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document for processing.")
        test_files['text_file'] = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"test": "data", "type": "json"}')
        test_files['json_file'] = f.name
    
    yield test_files
    
    # Cleanup
    for filepath in test_files.values():
        try:
            os.unlink(filepath)
        except:
            pass


@pytest.fixture(scope="function")
def mock_cache():
    """Provide simple in-memory cache for testing."""
    cache = {}
    
    def get(key):
        return cache.get(key)
    
    def set(key, value):
        cache[key] = value
        return True
    
    def delete(key):
        if key in cache:
            del cache[key]
        return True
    
    def clear():
        cache.clear()
        return True
    
    mock_cache_obj = type('MockCache', (), {
        'get': get,
        'set': set,
        'delete': delete,
        'clear': clear
    })()
    
    return mock_cache_obj


@pytest.fixture(scope="function")
def test_query_data():
    """Provide sample query data for search testing."""
    return {
        'simple_queries': [
            'drill',
            'power tool',
            'cordless drill',
            'cutting tool'
        ],
        'complex_queries': [
            'cordless drill with battery',
            'professional grade circular saw',
            'galvanized steel fasteners'
        ],
        'edge_case_queries': [
            '',
            '   ',
            'nonexistent_product_xyz',
            '!@#$%^&*()',
            'a' * 1000  # Very long query
        ],
        'expected_results': {
            'drill': ['TOOL001'],
            'power tool': ['TOOL001', 'TOOL002'],
            'circular saw': ['TOOL002'],
            'screws': ['HARD001']
        }
    }


@pytest.fixture(scope="function")
def performance_timer():
    """Provide timer for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            
        def start(self):
            self.start_time = time.time()
            
        def stop(self):
            self.end_time = time.time()
            
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
            
        def __enter__(self):
            self.start()
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.stop()
    
    return Timer


@pytest.fixture(scope="function")
def validation_data():
    """Provide data for validation testing."""
    return {
        'valid_files': {
            'test.txt': {'size': 1024, 'type': 'text/plain'},
            'test.pdf': {'size': 2048, 'type': 'application/pdf'},
            'test.json': {'size': 512, 'type': 'application/json'}
        },
        'invalid_files': {
            'too_large.txt': {'size': 50 * 1024 * 1024, 'type': 'text/plain'},  # 50MB
            'invalid_type.exe': {'size': 1024, 'type': 'application/x-executable'},
            'empty.txt': {'size': 0, 'type': 'text/plain'}
        },
        'valid_queries': [
            'drill',
            'power tools',
            'construction materials'
        ],
        'invalid_queries': [
            '',  # Empty
            None,  # Null
            '   ',  # Whitespace only
            'a' * 2000,  # Too long
        ]
    }


# Configure pytest markers for unit tests
def pytest_configure(config):
    """Configure pytest markers for unit tests."""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (Tier 1 - isolated)"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance validation"
    )
    config.addinivalue_line(
        "markers", "timeout: mark test as having timeout requirements"
    )
    config.addinivalue_line(
        "markers", "node_test: mark test as testing individual nodes"
    )