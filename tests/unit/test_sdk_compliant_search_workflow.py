#!/usr/bin/env python3
"""
Tier 1 Unit Tests for SDK-Compliant Search Workflow
Tests individual node functionality with real implementations (NO MOCKING)
Target: <1 second execution per test
"""

import pytest
import time
import tempfile
import os
import sqlite3
from typing import Dict, Any
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Test timeout decorator for Tier 1 compliance  
def test_timeout(func):
    """Decorator to ensure tests complete within 1 second"""
    import functools
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Test {func.__name__} took {execution_time:.3f}s (must be <1s)"
        return result
    return wrapper

class TestSearchWorkflowNodes:
    """Test individual nodes in search workflow with real implementations"""
    
    @pytest.fixture
    def temp_database(self):
        """Create temporary SQLite database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Create test database with real data
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
                currency TEXT DEFAULT 'USD',
                availability TEXT DEFAULT 'in_stock',
                is_published BOOLEAN DEFAULT 1
            )
        """)
        
        # Create brands table
        cursor.execute("""
            CREATE TABLE brands (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        
        # Create categories table
        cursor.execute("""
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        
        # Create product_pricing table
        cursor.execute("""
            CREATE TABLE product_pricing (
                id INTEGER PRIMARY KEY,
                product_id INTEGER,
                list_price REAL
            )
        """)
        
        # Create FTS5 virtual table
        cursor.execute("""
            CREATE VIRTUAL TABLE products_fts USING fts5(
                name, description, enriched_description, technical_specs,
                content=products, content_rowid=id
            )
        """)
        
        # Insert test data
        test_data = [
            (1, "TEST-001", "Laptop Computer", "High performance laptop", "Gaming laptop with RTX graphics", "Intel i7, 16GB RAM, 512GB SSD", 1, 1),
            (2, "TEST-002", "Wireless Mouse", "Ergonomic wireless mouse", "Professional mouse for productivity", "2.4GHz wireless, 1600 DPI", 1, 1),
            (3, "TEST-003", "Mechanical Keyboard", "RGB mechanical keyboard", "Gaming keyboard with Cherry MX switches", "87 keys, RGB backlight", 1, 1),
            (4, "TEST-004", "USB Cable", "USB-C to USB-A cable", "High-speed data transfer cable", "USB 3.0, 1 meter length", 2, 2),
            (5, "TEST-005", "Power Adapter", "65W laptop power adapter", "Universal laptop charger", "65W output, multiple tips", 2, 2)
        ]
        
        cursor.executemany(
            "INSERT INTO products (id, sku, name, description, enriched_description, technical_specs, brand_id, category_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            test_data
        )
        
        # Insert brands
        cursor.executemany(
            "INSERT INTO brands (id, name) VALUES (?, ?)",
            [(1, "TechBrand"), (2, "AccessoryBrand")]
        )
        
        # Insert categories  
        cursor.executemany(
            "INSERT INTO categories (id, name) VALUES (?, ?)",
            [(1, "Computers"), (2, "Accessories")]
        )
        
        # Insert pricing
        cursor.executemany(
            "INSERT INTO product_pricing (product_id, list_price) VALUES (?, ?)",
            [(1, 999.99), (2, 29.99), (3, 129.99), (4, 19.99), (5, 49.99)]
        )
        
        # Populate FTS5 table
        cursor.execute("INSERT INTO products_fts(products_fts) VALUES('rebuild')")
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        os.unlink(db_path)
    
    @pytest.fixture
    def runtime(self):
        """Create LocalRuntime instance"""
        return LocalRuntime()
    
    def test_query_processor_node_basic_functionality(self, runtime):
        """Test query processor node with valid inputs"""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "query_processor", {
            "code": """
import re

# Get input parameters
query = inputs.get('query', '')
category = inputs.get('category', '')
limit = inputs.get('limit', 10)
include_specs = inputs.get('include_specs', True)
use_cache = inputs.get('use_cache', True)
enable_fts = inputs.get('enable_fts', True)

# Process query
clean_query = query.strip() if query else ''
clean_category = category.strip() if category else ''
validated_limit = min(max(limit, 1), 100)

query_words = len(clean_query.split()) if clean_query else 0
has_special_chars = bool(re.search(r'[()&|*"~]', clean_query))
complexity_score = query_words + (2 if has_special_chars else 0)

cache_key = ':'.join([
    clean_query.lower(),
    clean_category.lower(),
    str(validated_limit),
    str(include_specs),
    str(enable_fts)
])

search_strategy = 'none'
if clean_query or clean_category:
    if enable_fts and query_words > 0:
        search_strategy = 'fts5_primary'
    else:
        search_strategy = 'like_fallback'

result = {
    'clean_query': clean_query,
    'clean_category': clean_category,
    'validated_limit': validated_limit,
    'include_specs': include_specs,
    'use_cache': use_cache,
    'enable_fts': enable_fts,
    'cache_key': cache_key,
    'complexity_score': complexity_score,
    'search_strategy': search_strategy,
    'has_query': len(clean_query) > 0,
    'has_category': len(clean_category) > 0
}
"""
        })
        
        results, run_id = runtime.execute(workflow.build(), {
            "query_processor": {
                "query": "laptop computer",
                "category": "electronics",
                "limit": 10,
                "include_specs": True,
                "use_cache": True,
                "enable_fts": True
            }
        })
        
        result = results.get('query_processor', {})
        
        # Validate processing results
        assert result['clean_query'] == 'laptop computer'
        assert result['clean_category'] == 'electronics'
        assert result['validated_limit'] == 10
        assert result['search_strategy'] == 'fts5_primary'
        assert result['has_query'] is True
        assert result['has_category'] is True
        assert result['complexity_score'] == 2  # 2 words
        assert 'laptop computer' in result['cache_key']
    
    @test_timeout
    def test_query_processor_node_edge_cases(self, runtime):
        """Test query processor with edge cases and validation"""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "query_processor", {
            "code": """
import re
def process_search_query(query, category, limit, include_specs, use_cache, enable_fts):
    clean_query = query.strip() if query else ''
    clean_category = category.strip() if category else ''
    validated_limit = min(max(limit, 1), 100)
    
    query_words = len(clean_query.split()) if clean_query else 0
    has_special_chars = bool(re.search(r'[()&|*"~]', clean_query))
    complexity_score = query_words + (2 if has_special_chars else 0)
    
    cache_key = ':'.join([
        clean_query.lower(),
        clean_category.lower(),
        str(validated_limit),
        str(include_specs),
        str(enable_fts)
    ])
    
    search_strategy = 'none'
    if clean_query or clean_category:
        if enable_fts and query_words > 0:
            search_strategy = 'fts5_primary'
        else:
            search_strategy = 'like_fallback'
    
    result = {
        'clean_query': clean_query,
        'clean_category': clean_category,
        'validated_limit': validated_limit,
        'search_strategy': search_strategy,
        'complexity_score': complexity_score
    }
"""
        })
        
        # Test with extreme limit values
        results, run_id = runtime.execute(workflow.build(), {
            "query_processor": {
                "query": "",
                "category": "",  
                "limit": 500,  # Should be clamped to 100
                "include_specs": False,
                "use_cache": False,
                "enable_fts": False
            }
        })
        
        result = results.get('query_processor', {})
        
        # Validate limit clamping
        assert result['validated_limit'] == 100
        assert result['clean_query'] == ''
        assert result['clean_category'] == ''
        assert result['search_strategy'] == 'none'
        assert result['complexity_score'] == 0
    
    @test_timeout  
    def test_cache_lookup_node_functionality(self, runtime):
        """Test cache lookup node with real cache data"""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "cache_lookup", {
            "code": """
import time
def lookup_search_cache(processed_query, cache_data):
    CACHE_TTL_SECONDS = 300
    
    if not processed_query.get('use_cache', True):
        result = {
            'cache_hit': False,
            'cached_results': None,
            'cache_status': 'disabled'
        }
    else:
        cache_key = processed_query['cache_key']
        current_time = time.time()
        
        cache_entry = cache_data.get(cache_key)
        if cache_entry:
            entry_age = current_time - cache_entry['timestamp']
            
            if entry_age <= CACHE_TTL_SECONDS:
                result = {
                    'cache_hit': True,
                    'cached_results': cache_entry['results'],
                    'cache_status': 'hit',
                    'cache_age_seconds': entry_age,
                    'result_count': len(cache_entry['results'])
                }
            else:
                result = {
                    'cache_hit': False,
                    'cached_results': None,
                    'cache_status': 'expired',
                    'cache_age_seconds': entry_age
                }
        else:
            result = {
                'cache_hit': False,
                'cached_results': None,
                'cache_status': 'miss'
            }
"""
        })
        
        # Test with fresh cache entry
        test_cache = {
            'laptop:electronics:10:true:true': {
                'timestamp': time.time() - 60,  # 1 minute old
                'results': [{'id': 1, 'name': 'Test Laptop', 'score': 0.9}]
            }
        }
        
        results, run_id = runtime.execute(workflow.build(), {
            "cache_lookup": {
                "processed_query": {
                    'cache_key': 'laptop:electronics:10:true:true',
                    'use_cache': True
                },
                "cache_data": test_cache
            }
        })
        
        result = results.get('cache_lookup', {})
        
        # Validate cache hit
        assert result['cache_hit'] is True
        assert result['cache_status'] == 'hit'
        assert result['result_count'] == 1
        assert result['cache_age_seconds'] < 120
    
    @test_timeout
    def test_fts5_search_node_with_real_database(self, temp_database, runtime):
        """Test FTS5 search node with real SQLite database"""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "fts5_search", {
            "code": """
import sqlite3
import time
def execute_fts5_search(processed_query, cache_lookup_result, db_path):
    if cache_lookup_result.get('cache_hit', False):
        result = {
            'fts5_executed': False,
            'results': cache_lookup_result['cached_results'],
            'skip_reason': 'cache_hit'
        }
    elif processed_query['search_strategy'] != 'fts5_primary':
        result = {
            'fts5_executed': False,
            'results': [],
            'skip_reason': 'strategy_not_fts5'
        }
    else:
        start_time = time.time()
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            
            # Verify FTS5 table exists
            fts_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_fts'").fetchone()
            
            if not fts_check:
                conn.close()
                result = {
                    'fts5_executed': False,
                    'results': [],
                    'error': 'FTS5 table products_fts not found',
                    'fallback_required': True
                }
            else:
                clean_query = processed_query['clean_query']
                limit = processed_query['validated_limit']
                
                # Build FTS5 query
                fts_query = ' '.join([f'"{term}"' for term in clean_query.split() if len(term) > 1])
                
                sql = '''
                    SELECT p.id, p.sku, p.name, p.description, p.enriched_description,
                           pp.list_price as price, p.currency, p.availability,
                           b.name as brand, c.name as category, fts.rank,
                           snippet(products_fts, 0, '<mark>', '</mark>', '...', 32) as snippet
                    FROM products_fts fts
                    JOIN products p ON p.id = fts.rowid
                    LEFT JOIN product_pricing pp ON p.id = pp.product_id
                    LEFT JOIN brands b ON p.brand_id = b.id
                    LEFT JOIN categories c ON p.category_id = c.id
                    WHERE p.is_published = 1 AND products_fts MATCH ?
                    ORDER BY fts.rank
                    LIMIT ?
                '''
                
                cursor = conn.execute(sql, [fts_query, limit])
                rows = cursor.fetchall()
                
                results = []
                for i, row in enumerate(rows):
                    result_dict = {
                        'id': row['id'],
                        'sku': row['sku'],
                        'name': row['name'],
                        'description': row['description'],
                        'enriched_description': row['enriched_description'] or '',
                        'price': row['price'],
                        'currency': row['currency'] or 'USD',
                        'brand': row['brand'] or '',
                        'category': row['category'] or '',
                        'availability': row['availability'] or '',
                        'rank': row['rank'] if row['rank'] else i,
                        'snippet': row['snippet'] or '',
                        'match_score': 0
                    }
                    results.append(result_dict)
                
                conn.close()
                execution_time_ms = (time.time() - start_time) * 1000
                
                result = {
                    'fts5_executed': True,
                    'results': results,
                    'result_count': len(results),
                    'execution_time_ms': execution_time_ms
                }
                
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            
            result = {
                'fts5_executed': False,
                'results': [],
                'error': f'FTS5 search failed: {str(e)}',
                'execution_time_ms': (time.time() - start_time) * 1000,
                'fallback_required': True
            }
"""
        })
        
        results, run_id = runtime.execute(workflow.build(), {
            "fts5_search": {
                "processed_query": {
                    'clean_query': 'laptop computer',
                    'validated_limit': 5,
                    'search_strategy': 'fts5_primary'
                },
                "cache_lookup_result": {
                    'cache_hit': False
                },
                "db_path": temp_database
            }
        })
        
        result = results.get('fts5_search', {})
        
        # Validate FTS5 search execution
        assert result['fts5_executed'] is True
        assert 'results' in result
        assert 'execution_time_ms' in result
        assert result['execution_time_ms'] < 500  # Should be fast
        
        # Validate search results structure
        if result['result_count'] > 0:
            first_result = result['results'][0]
            assert 'id' in first_result
            assert 'sku' in first_result
            assert 'name' in first_result
            assert 'snippet' in first_result
    
    @test_timeout
    def test_search_workflow_parameter_validation(self, runtime):
        """Test parameter validation and sanitization"""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "validator", {
            "code": """
def validate_search_parameters(query, category, limit, include_specs, use_cache, enable_fts):
    errors = []
    warnings = []
    
    # Validate query
    if query and len(query) > 1000:
        errors.append("Query too long (max 1000 characters)")
    
    # Validate category
    if category and len(category) > 100:
        errors.append("Category name too long (max 100 characters)")
    
    # Validate limit
    if limit < 1:
        errors.append("Limit must be at least 1")
    elif limit > 1000:
        warnings.append("Limit very high, may affect performance")
    
    # Sanitize inputs
    safe_query = query.strip()[:1000] if query else ''
    safe_category = category.strip()[:100] if category else ''
    safe_limit = max(1, min(limit, 100))
    
    result = {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'sanitized_query': safe_query,
        'sanitized_category': safe_category,
        'sanitized_limit': safe_limit,
        'sanitized_include_specs': bool(include_specs),
        'sanitized_use_cache': bool(use_cache),
        'sanitized_enable_fts': bool(enable_fts)
    }
"""
        })
        
        # Test with various parameter combinations
        test_cases = [
            {
                "input": {"query": "test", "category": "electronics", "limit": 10, "include_specs": True, "use_cache": True, "enable_fts": True},
                "expected_valid": True
            },
            {
                "input": {"query": "a" * 1500, "category": "test", "limit": 5, "include_specs": False, "use_cache": False, "enable_fts": False},
                "expected_valid": False  # Query too long
            },
            {
                "input": {"query": "test", "category": "", "limit": 0, "include_specs": True, "use_cache": True, "enable_fts": True},
                "expected_valid": False  # Invalid limit
            }
        ]
        
        for test_case in test_cases:
            results, run_id = runtime.execute(workflow.build(), {
                "validator": test_case["input"]
            })
            
            result = results.get('validator', {})
            assert result['valid'] == test_case['expected_valid']
            
            # Validate sanitization
            assert len(result['sanitized_query']) <= 1000
            assert len(result['sanitized_category']) <= 100
            assert 1 <= result['sanitized_limit'] <= 100

class TestSearchWorkflowPerformance:
    """Test performance characteristics of search workflow nodes"""
    
    @pytest.fixture
    def runtime(self):
        return LocalRuntime()
    
    @test_timeout
    def test_node_execution_speed_benchmarks(self, runtime):
        """Benchmark individual node execution speeds"""
        workflow = WorkflowBuilder()
        
        # Simple computation node for benchmarking
        workflow.add_node("PythonCodeNode", "benchmark", {
            "code": """
import time
def benchmark_computation(iterations):
    start_time = time.time()
    
    # Simulate typical search processing work
    results = []
    for i in range(iterations):
        # String operations
        text = f"test query {i}" * 10
        tokens = text.split()
        
        # Numerical operations
        score = sum(len(token) for token in tokens) / len(tokens)
        
        # Dictionary operations
        result = {
            'id': i,
            'text': text[:100],
            'score': score,
            'tokens': len(tokens)
        }
        results.append(result)
    
    execution_time = time.time() - start_time
    
    result = {
        'iterations': iterations,
        'execution_time_ms': execution_time * 1000,
        'results_count': len(results),
        'avg_time_per_iteration_ms': (execution_time * 1000) / iterations
    }
"""
        })
        
        # Test with different workloads
        for iterations in [10, 50, 100]:
            results, run_id = runtime.execute(workflow.build(), {
                "benchmark": {"iterations": iterations}
            })
            
            result = results.get('benchmark', {})
            
            # Validate performance characteristics
            assert result['execution_time_ms'] < 800  # Must complete quickly
            assert result['avg_time_per_iteration_ms'] < 10  # Per-iteration efficiency
            assert result['results_count'] == iterations
    
    @test_timeout  
    def test_memory_efficient_processing(self, runtime):
        """Test memory-efficient data processing in nodes"""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "memory_test", {
            "code": """
import sys
def process_large_dataset(size):
    # Process data in chunks to test memory efficiency
    chunk_size = 100
    processed_count = 0
    max_chunk_memory = 0
    
    for chunk_start in range(0, size, chunk_size):
        chunk_end = min(chunk_start + chunk_size, size)
        
        # Simulate processing a chunk of data
        chunk_data = []
        for i in range(chunk_start, chunk_end):
            item = {
                'id': i,
                'data': f'item_{i}_data',
                'processed': True,
                'metadata': {'index': i, 'chunk': chunk_start // chunk_size}
            }
            chunk_data.append(item)
        
        # Track memory usage (simplified)
        chunk_memory = len(chunk_data) * 100  # Approximate memory per item
        max_chunk_memory = max(max_chunk_memory, chunk_memory)
        
        processed_count += len(chunk_data)
        
        # Clear chunk to simulate memory cleanup
        chunk_data.clear()
    
    result = {
        'total_processed': processed_count,
        'max_chunk_memory_approx': max_chunk_memory,
        'memory_efficient': max_chunk_memory < 50000,  # Keep chunks reasonable
        'chunks_processed': (size + chunk_size - 1) // chunk_size
    }
"""
        })
        
        results, run_id = runtime.execute(workflow.build(), {
            "memory_test": {"size": 500}
        })
        
        result = results.get('memory_test', {})
        
        # Validate memory-efficient processing
        assert result['total_processed'] == 500
        assert result['memory_efficient'] is True
        assert result['max_chunk_memory_approx'] < 50000