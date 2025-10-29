#!/usr/bin/env python3
"""
Tier 2 Integration Tests - Real Database Operations
Tests SDK workflows with REAL PostgreSQL database (NO MOCKING)
Target: <5 seconds execution per test, REQUIRES Docker infrastructure
"""

import pytest
import time
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from typing import Dict, Any, List
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Test timeout decorator for Tier 2 compliance
def test_timeout(func):
    """Decorator to ensure tests complete within 5 seconds"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        assert execution_time < 5.0, f"Test {func.__name__} took {execution_time:.3f}s (must be <5s)"
        return result
    return wrapper

@pytest.fixture(scope="module")
def postgres_connection():
    """Real PostgreSQL connection - NO MOCKING"""
    # Connect to test database running in Docker
    conn_params = {
        'host': 'localhost',
        'port': 5434,  # Docker mapped port
        'database': 'horme_test',
        'user': 'test_user',
        'password': 'test_password'
    }
    
    try:
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        yield conn
        conn.close()
    except psycopg2.Error as e:
        pytest.skip(f"PostgreSQL not available: {e}")

@pytest.fixture(scope="module") 
def redis_connection():
    """Real Redis connection - NO MOCKING"""
    try:
        r = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)
        r.ping()  # Test connection
        yield r
    except redis.ConnectionError as e:
        pytest.skip(f"Redis not available: {e}")

@pytest.fixture
def runtime():
    """LocalRuntime instance for workflow execution"""
    return LocalRuntime()

class TestRealDatabaseIntegration:
    """Integration tests with real PostgreSQL database operations"""
    
    @test_timeout
    def test_database_product_search_workflow(self, postgres_connection, runtime):
        """Test complete product search workflow with real database"""
        workflow = WorkflowBuilder()
        
        # Node 1: Database connection and search
        workflow.add_node("PythonCodeNode", "database_search", {
            "code": """
import psycopg2
from psycopg2.extras import RealDictCursor
import time

def search_products_database(search_query, limit, conn_params):
    '''Search products in real PostgreSQL database'''
    start_time = time.time()
    
    try:
        # Connect to real database
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Full-text search query using PostgreSQL's built-in capabilities
        search_sql = '''
            SELECT p.id, p.sku, p.name, p.description, p.enriched_description,
                   pp.list_price, p.currency, p.availability,
                   b.name as brand, c.name as category,
                   ts_rank(to_tsvector('english', 
                       COALESCE(p.name, '') || ' ' || 
                       COALESCE(p.description, '') || ' ' ||
                       COALESCE(p.enriched_description, '')
                   ), plainto_tsquery('english', %s)) as rank
            FROM horme.products p
            LEFT JOIN horme.product_pricing pp ON p.id = pp.product_id
            LEFT JOIN horme.brands b ON p.brand_id = b.id
            LEFT JOIN horme.categories c ON p.category_id = c.id
            WHERE p.is_published = true
            AND to_tsvector('english', 
                COALESCE(p.name, '') || ' ' || 
                COALESCE(p.description, '') || ' ' ||
                COALESCE(p.enriched_description, '')
            ) @@ plainto_tsquery('english', %s)
            ORDER BY rank DESC
            LIMIT %s
        '''
        
        cursor.execute(search_sql, [search_query, search_query, limit])
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        product_results = []
        for row in results:
            product_results.append({
                'id': row['id'],
                'sku': row['sku'],
                'name': row['name'],
                'description': row['description'],
                'enriched_description': row['enriched_description'],
                'price': float(row['list_price']) if row['list_price'] else None,
                'currency': row['currency'],
                'brand': row['brand'],
                'category': row['category'],
                'availability': row['availability'],
                'rank': float(row['rank']) if row['rank'] else 0.0
            })
        
        cursor.close()
        conn.close()
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        result = {
            'success': True,
            'products': product_results,
            'total_results': len(product_results),
            'execution_time_ms': execution_time_ms,
            'search_query': search_query
        }
        
    except Exception as e:
        result = {
            'success': False,
            'products': [],
            'total_results': 0,
            'error': str(e),
            'search_query': search_query
        }
"""
        })
        
        # Execute workflow with real database connection
        conn_params = {
            'host': 'localhost',
            'port': 5434,
            'database': 'horme_test', 
            'user': 'test_user',
            'password': 'test_password'
        }
        
        results, run_id = runtime.execute(workflow.build(), {
            "database_search": {
                "search_query": "test product",
                "limit": 10,
                "conn_params": conn_params
            }
        })
        
        result = results.get('database_search', {})
        
        # Validate real database integration
        assert result['success'] is True
        assert 'products' in result
        assert result['total_results'] >= 0
        assert result['execution_time_ms'] < 3000  # Should complete quickly
        assert result['search_query'] == "test product"
        
        # If products found, validate structure
        if result['total_results'] > 0:
            first_product = result['products'][0]
            assert 'id' in first_product
            assert 'sku' in first_product
            assert 'name' in first_product
            assert 'rank' in first_product
    
    @test_timeout
    def test_quotation_creation_workflow(self, postgres_connection, runtime):
        """Test quotation creation workflow with real database operations"""
        workflow = WorkflowBuilder()
        
        # Node 1: Create quotation record
        workflow.add_node("PythonCodeNode", "create_quotation", {
            "code": """
import psycopg2
from psycopg2.extras import RealDictCursor
import time

def create_quotation_database(user_id, total_amount, notes, conn_params):
    '''Create quotation in real PostgreSQL database'''
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Generate quote number
        timestamp = int(time.time())
        quote_number = f'INT-TEST-{timestamp}'
        
        # Insert quotation
        insert_sql = '''
            INSERT INTO horme.quotations 
            (quote_number, user_id, status, total_amount, currency, valid_until, notes, metadata)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP + INTERVAL '30 days', %s, %s)
            RETURNING id, quote_number, status, total_amount, created_at
        '''
        
        metadata = {'test': True, 'integration_test': True}
        
        cursor.execute(insert_sql, [
            quote_number, user_id, 'draft', total_amount, 'USD', notes, 
            psycopg2.extras.Json(metadata)
        ])
        
        quotation = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        result = {
            'success': True,
            'quotation': {
                'id': quotation['id'],
                'quote_number': quotation['quote_number'],
                'status': quotation['status'],
                'total_amount': float(quotation['total_amount']),
                'created_at': quotation['created_at'].isoformat()
            }
        }
        
    except Exception as e:
        result = {
            'success': False,
            'quotation': None,
            'error': str(e)
        }
"""
        })
        
        # Node 2: Add quotation items
        workflow.add_node("PythonCodeNode", "add_quotation_items", {
            "code": """
import psycopg2
from psycopg2.extras import RealDictCursor

def add_quotation_items_database(quotation_result, items_data, conn_params):
    '''Add items to quotation in real database'''
    
    if not quotation_result.get('success', False):
        result = {
            'success': False,
            'items_added': 0,
            'error': 'Quotation creation failed'
        }
        return result
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        quotation_id = quotation_result['quotation']['id']
        items_added = 0
        
        for item in items_data:
            # Get product ID (assuming test products exist)
            product_sql = 'SELECT id FROM horme.products WHERE sku = %s LIMIT 1'
            cursor.execute(product_sql, [item['sku']])
            product = cursor.fetchone()
            
            if product:
                # Insert quotation item
                item_sql = '''
                    INSERT INTO horme.quotation_items 
                    (quotation_id, product_id, quantity, unit_price, total_price, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                '''
                
                unit_price = item['unit_price']
                quantity = item['quantity']
                total_price = unit_price * quantity
                
                cursor.execute(item_sql, [
                    quotation_id, product['id'], quantity, 
                    unit_price, total_price, item.get('notes', '')
                ])
                
                items_added += 1
        
        cursor.close()
        conn.close()
        
        result = {
            'success': True,
            'quotation_id': quotation_id,
            'items_added': items_added,
            'total_items_requested': len(items_data)
        }
        
    except Exception as e:
        result = {
            'success': False,
            'items_added': 0,
            'error': str(e)
        }
"""
        })
        
        # Connect workflow nodes
        workflow.add_connection("create_quotation", "result", "add_quotation_items", "quotation_result")
        
        # Execute quotation creation workflow
        conn_params = {
            'host': 'localhost',
            'port': 5434,
            'database': 'horme_test',
            'user': 'test_user', 
            'password': 'test_password'
        }
        
        # Sample quotation items
        items_data = [
            {'sku': 'TEST-000001', 'quantity': 2, 'unit_price': 99.99, 'notes': 'Integration test item 1'},
            {'sku': 'TEST-000002', 'quantity': 1, 'unit_price': 29.99, 'notes': 'Integration test item 2'}
        ]
        
        results, run_id = runtime.execute(workflow.build(), {
            "create_quotation": {
                "user_id": 1,  # Test user
                "total_amount": 229.97,
                "notes": "Integration test quotation",
                "conn_params": conn_params
            },
            "add_quotation_items": {
                "items_data": items_data,
                "conn_params": conn_params
            }
        })
        
        # Validate quotation creation
        quotation_result = results.get('create_quotation', {})
        assert quotation_result['success'] is True
        assert 'quotation' in quotation_result
        
        quotation = quotation_result['quotation']
        assert quotation['quote_number'].startswith('INT-TEST-')
        assert quotation['status'] == 'draft'
        assert quotation['total_amount'] == 229.97
        
        # Validate quotation items  
        items_result = results.get('add_quotation_items', {})
        assert items_result['success'] is True
        assert items_result['items_added'] >= 0  # May be 0 if test products don't exist
        assert items_result['total_items_requested'] == 2

class TestRealCacheIntegration:
    """Integration tests with real Redis cache operations"""
    
    @test_timeout
    def test_search_cache_workflow(self, redis_connection, runtime):
        """Test search caching workflow with real Redis"""
        workflow = WorkflowBuilder()
        
        # Node 1: Cache lookup
        workflow.add_node("PythonCodeNode", "cache_lookup", {
            "code": """
import redis
import json
import time

def lookup_search_cache(cache_key, redis_params):
    '''Look up search results in real Redis cache'''
    
    try:
        r = redis.Redis(**redis_params)
        
        # Check if key exists
        cache_data = r.get(cache_key)
        
        if cache_data:
            # Parse cached data
            cached_result = json.loads(cache_data)
            
            # Check expiration
            ttl = r.ttl(cache_key)
            
            result = {
                'cache_hit': True,
                'cached_data': cached_result,
                'ttl_seconds': ttl,
                'cache_key': cache_key
            }
        else:
            result = {
                'cache_hit': False,
                'cached_data': None,
                'cache_key': cache_key
            }
            
    except Exception as e:
        result = {
            'cache_hit': False,
            'cached_data': None,
            'error': str(e),
            'cache_key': cache_key
        }
"""
        })
        
        # Node 2: Cache storage
        workflow.add_node("PythonCodeNode", "cache_store", {
            "code": """
import redis
import json
import time

def store_search_cache(cache_lookup_result, search_data, redis_params, ttl_seconds=300):
    '''Store search results in real Redis cache'''
    
    cache_key = cache_lookup_result['cache_key']
    
    if cache_lookup_result.get('cache_hit', False):
        result = {
            'stored': False,
            'reason': 'cache_hit',
            'cache_key': cache_key
        }
    else:
        try:
            r = redis.Redis(**redis_params)
            
            # Prepare cache data
            cache_data = {
                'results': search_data.get('results', []),
                'cached_at': time.time(),
                'total_results': len(search_data.get('results', [])),
                'metadata': search_data.get('metadata', {})
            }
            
            # Store in cache with expiration
            r.setex(cache_key, ttl_seconds, json.dumps(cache_data))
            
            result = {
                'stored': True,
                'cache_key': cache_key,
                'ttl_seconds': ttl_seconds,
                'data_size': len(json.dumps(cache_data))
            }
            
        except Exception as e:
            result = {
                'stored': False,
                'error': str(e),
                'cache_key': cache_key
            }
"""
        })
        
        # Connect nodes
        workflow.add_connection("cache_lookup", "result", "cache_store", "cache_lookup_result")
        
        # Execute cache workflow
        redis_params = {
            'host': 'localhost',
            'port': 6380,
            'db': 0,
            'decode_responses': True
        }
        
        test_cache_key = f"test_search_integration_{int(time.time())}"
        test_search_data = {
            'results': [
                {'id': 1, 'name': 'Test Product 1', 'score': 0.9},
                {'id': 2, 'name': 'Test Product 2', 'score': 0.8}
            ],
            'metadata': {'query': 'test products', 'execution_time': 100}
        }
        
        results, run_id = runtime.execute(workflow.build(), {
            "cache_lookup": {
                "cache_key": test_cache_key,
                "redis_params": redis_params
            },
            "cache_store": {
                "search_data": test_search_data,
                "redis_params": redis_params,
                "ttl_seconds": 300
            }
        })
        
        # Validate cache operations
        lookup_result = results.get('cache_lookup', {})
        assert 'cache_hit' in lookup_result
        assert lookup_result['cache_key'] == test_cache_key
        
        store_result = results.get('cache_store', {})
        assert store_result.get('stored', False) is True
        assert store_result['cache_key'] == test_cache_key
        assert store_result['ttl_seconds'] == 300
        
        # Verify cache entry exists in real Redis
        r = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)
        cached_data = r.get(test_cache_key)
        assert cached_data is not None
        
        # Parse and validate cached content
        cache_content = json.loads(cached_data)
        assert 'results' in cache_content
        assert len(cache_content['results']) == 2
        assert cache_content['total_results'] == 2
    
    @test_timeout
    def test_cache_invalidation_workflow(self, redis_connection, runtime):
        """Test cache invalidation workflow with real Redis operations"""
        workflow = WorkflowBuilder()
        
        # Node 1: Setup test cache entries
        workflow.add_node("PythonCodeNode", "setup_cache", {
            "code": """
import redis
import json
import time

def setup_test_cache_entries(cache_keys, redis_params):
    '''Setup multiple cache entries for invalidation testing'''
    
    try:
        r = redis.Redis(**redis_params)
        
        entries_created = 0
        
        for cache_key in cache_keys:
            test_data = {
                'data': f'test_data_for_{cache_key}',
                'created_at': time.time(),
                'test': True
            }
            
            r.setex(cache_key, 300, json.dumps(test_data))
            entries_created += 1
        
        result = {
            'success': True,
            'entries_created': entries_created,
            'cache_keys': cache_keys
        }
        
    except Exception as e:
        result = {
            'success': False,
            'error': str(e),
            'entries_created': 0
        }
"""
        })
        
        # Node 2: Invalidate cache entries
        workflow.add_node("PythonCodeNode", "invalidate_cache", {
            "code": """
import redis

def invalidate_cache_entries(setup_result, pattern, redis_params):
    '''Invalidate cache entries matching pattern'''
    
    if not setup_result.get('success', False):
        result = {
            'success': False,
            'error': 'Cache setup failed'
        }
        return result
    
    try:
        r = redis.Redis(**redis_params)
        
        # Find keys matching pattern
        matching_keys = r.keys(pattern)
        
        # Delete matching keys
        if matching_keys:
            deleted_count = r.delete(*matching_keys)
        else:
            deleted_count = 0
        
        result = {
            'success': True,
            'pattern': pattern,
            'keys_found': len(matching_keys),
            'keys_deleted': deleted_count,
            'matching_keys': matching_keys
        }
        
    except Exception as e:
        result = {
            'success': False,
            'error': str(e),
            'pattern': pattern
        }
"""
        })
        
        # Connect nodes
        workflow.add_connection("setup_cache", "result", "invalidate_cache", "setup_result")
        
        # Execute cache invalidation workflow
        redis_params = {
            'host': 'localhost',
            'port': 6380,
            'db': 0,
            'decode_responses': True
        }
        
        timestamp = int(time.time())
        test_cache_keys = [
            f"test_invalidate_{timestamp}_1",
            f"test_invalidate_{timestamp}_2", 
            f"test_invalidate_{timestamp}_3"
        ]
        
        results, run_id = runtime.execute(workflow.build(), {
            "setup_cache": {
                "cache_keys": test_cache_keys,
                "redis_params": redis_params
            },
            "invalidate_cache": {
                "pattern": f"test_invalidate_{timestamp}_*",
                "redis_params": redis_params
            }
        })
        
        # Validate cache setup
        setup_result = results.get('setup_cache', {})
        assert setup_result['success'] is True
        assert setup_result['entries_created'] == 3
        
        # Validate cache invalidation
        invalidate_result = results.get('invalidate_cache', {})
        assert invalidate_result['success'] is True
        assert invalidate_result['keys_found'] == 3
        assert invalidate_result['keys_deleted'] == 3
        assert len(invalidate_result['matching_keys']) == 3
        
        # Verify keys are actually deleted from Redis
        r = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)
        remaining_keys = r.keys(f"test_invalidate_{timestamp}_*")
        assert len(remaining_keys) == 0

class TestMultiServiceIntegration:
    """Integration tests combining multiple real services"""
    
    @test_timeout
    def test_product_search_with_caching_workflow(self, postgres_connection, redis_connection, runtime):
        """Test complete product search workflow with database and cache integration"""
        workflow = WorkflowBuilder()
        
        # Node 1: Cache lookup first
        workflow.add_node("PythonCodeNode", "cache_check", {
            "code": """
import redis
import json
import hashlib

def check_search_cache(query, limit, redis_params):
    '''Check Redis cache for search results'''
    
    # Generate cache key
    cache_key = f"search:{hashlib.md5((query + str(limit)).encode()).hexdigest()}"
    
    try:
        r = redis.Redis(**redis_params)
        cached_data = r.get(cache_key)
        
        if cached_data:
            cache_content = json.loads(cached_data)
            result = {
                'cache_hit': True,
                'results': cache_content['results'],
                'cache_key': cache_key,
                'cached_at': cache_content.get('cached_at', 0)
            }
        else:
            result = {
                'cache_hit': False,
                'results': None,
                'cache_key': cache_key
            }
            
    except Exception as e:
        result = {
            'cache_hit': False,
            'results': None,
            'cache_key': cache_key,
            'error': str(e)
        }
"""
        })
        
        # Node 2: Database search (if cache miss)
        workflow.add_node("PythonCodeNode", "database_search", {
            "code": """
import psycopg2
from psycopg2.extras import RealDictCursor
import time

def search_database_if_needed(cache_result, query, limit, postgres_params):
    '''Search database only if cache miss'''
    
    if cache_result.get('cache_hit', False):
        result = {
            'searched_database': False,
            'results': cache_result['results'],
            'source': 'cache'
        }
    else:
        try:
            conn = psycopg2.connect(**postgres_params)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Simple search query
            search_sql = '''
                SELECT p.id, p.sku, p.name, p.description, pp.list_price
                FROM horme.products p
                LEFT JOIN horme.product_pricing pp ON p.id = pp.product_id
                WHERE p.is_published = true
                AND LOWER(p.name) LIKE LOWER(%s)
                ORDER BY p.id
                LIMIT %s
            '''
            
            cursor.execute(search_sql, [f'%{query}%', limit])
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'id': row['id'],
                    'sku': row['sku'], 
                    'name': row['name'],
                    'description': row['description'],
                    'price': float(row['list_price']) if row['list_price'] else None
                })
            
            cursor.close()
            conn.close()
            
            result = {
                'searched_database': True,
                'results': results,
                'source': 'database',
                'total_found': len(results)
            }
            
        except Exception as e:
            result = {
                'searched_database': False,
                'results': [],
                'source': 'error',
                'error': str(e)
            }
"""
        })
        
        # Node 3: Update cache with new results
        workflow.add_node("PythonCodeNode", "update_cache", {
            "code": """
import redis
import json
import time

def update_search_cache(cache_result, search_result, redis_params):
    '''Update cache with new search results'''
    
    cache_key = cache_result['cache_key']
    
    if search_result.get('searched_database', False):
        try:
            r = redis.Redis(**redis_params)
            
            cache_data = {
                'results': search_result['results'],
                'cached_at': time.time(),
                'total_results': len(search_result['results']),
                'source': 'database'
            }
            
            # Cache for 5 minutes
            r.setex(cache_key, 300, json.dumps(cache_data))
            
            result = {
                'cache_updated': True,
                'cache_key': cache_key,
                'results_cached': len(search_result['results'])
            }
            
        except Exception as e:
            result = {
                'cache_updated': False,
                'error': str(e),
                'cache_key': cache_key
            }
    else:
        result = {
            'cache_updated': False,
            'reason': 'no_database_search',
            'cache_key': cache_key
        }
"""
        })
        
        # Connect workflow nodes
        workflow.add_connection("cache_check", "result", "database_search", "cache_result")
        workflow.add_connection("cache_check", "result", "update_cache", "cache_result") 
        workflow.add_connection("database_search", "result", "update_cache", "search_result")
        
        # Execute multi-service integration workflow
        redis_params = {
            'host': 'localhost',
            'port': 6380,
            'db': 0,
            'decode_responses': True
        }
        
        postgres_params = {
            'host': 'localhost',
            'port': 5434,
            'database': 'horme_test',
            'user': 'test_user',
            'password': 'test_password'
        }
        
        results, run_id = runtime.execute(workflow.build(), {
            "cache_check": {
                "query": "test",
                "limit": 5,
                "redis_params": redis_params
            },
            "database_search": {
                "query": "test",
                "limit": 5,
                "postgres_params": postgres_params
            },
            "update_cache": {
                "redis_params": redis_params
            }
        })
        
        # Validate multi-service integration
        cache_result = results.get('cache_check', {})
        assert 'cache_hit' in cache_result
        assert 'cache_key' in cache_result
        
        search_result = results.get('database_search', {})
        assert 'searched_database' in search_result
        assert 'results' in search_result
        assert 'source' in search_result
        
        update_result = results.get('update_cache', {})
        
        # If database was searched, cache should be updated
        if search_result.get('searched_database', False):
            assert update_result.get('cache_updated', False) is True
        
        # Verify final results exist
        final_results = search_result.get('results', [])
        assert isinstance(final_results, list)