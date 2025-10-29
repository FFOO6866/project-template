#!/usr/bin/env python3
"""
Tier 3 End-to-End Tests - Complete Business Process Validation
Tests complete user workflows from upload to quotation with REAL infrastructure
Target: <10 seconds execution per test, REQUIRES full Docker stack
"""

import pytest
import time
import tempfile
import os
import json
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from typing import Dict, Any, List
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Test timeout decorator for Tier 3 compliance
def test_timeout(func):
    """Decorator to ensure tests complete within 10 seconds"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        assert execution_time < 10.0, f"Test {func.__name__} took {execution_time:.3f}s (must be <10s)"
        return result
    return wrapper

@pytest.fixture(scope="module")
def full_infrastructure():
    """Verify all required services are available - NO MOCKING"""
    services = {
        'postgres': {'host': 'localhost', 'port': 5434, 'db': 'horme_test', 'user': 'test_user', 'password': 'test_password'},
        'redis': {'host': 'localhost', 'port': 6380, 'db': 0}
    }
    
    # Test PostgreSQL
    try:
        conn = psycopg2.connect(**services['postgres'])
        conn.close()
    except psycopg2.Error as e:
        pytest.skip(f"PostgreSQL not available: {e}")
    
    # Test Redis
    try:
        r = redis.Redis(**services['redis'])
        r.ping()
    except redis.ConnectionError as e:
        pytest.skip(f"Redis not available: {e}")
    
    return services

@pytest.fixture
def runtime():
    """LocalRuntime for executing complex workflows"""
    return LocalRuntime()

@pytest.fixture
def temp_upload_directory():
    """Temporary directory for file upload testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

class TestCompleteUploadToQuotationWorkflow:
    """End-to-end test of complete upload-to-quotation business process"""
    
    @test_timeout
    def test_complete_document_processing_pipeline(self, full_infrastructure, runtime, temp_upload_directory):
        """Test complete document upload -> processing -> product matching -> quotation workflow"""
        workflow = WorkflowBuilder()
        
        # Step 1: Document upload and storage
        workflow.add_node("PythonCodeNode", "document_upload", {
            "code": """
import os
import hashlib
import time
import json

def process_document_upload(documents, upload_dir, user_id):
    '''Process document uploads with real file operations'''
    
    uploaded_files = []
    upload_errors = []
    
    # Create user-specific directory
    user_dir = os.path.join(upload_dir, f'user_{user_id}')
    os.makedirs(user_dir, exist_ok=True)
    
    for doc in documents:
        try:
            # Generate unique filename
            timestamp = int(time.time() * 1000)
            file_id = f"doc_{timestamp}_{hash(doc['name']) % 10000}"
            filename = f"{file_id}_{doc['name'].replace(' ', '_')}"
            file_path = os.path.join(user_dir, filename)
            
            # Write file content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(doc['content'])
            
            # Calculate checksum
            checksum = hashlib.sha256(doc['content'].encode()).hexdigest()
            
            uploaded_files.append({
                'id': file_id,
                'original_name': doc['name'],
                'stored_path': file_path,
                'size': len(doc['content'].encode()),
                'mime_type': doc.get('mime_type', 'text/plain'),
                'checksum': checksum,
                'user_id': user_id
            })
            
        except Exception as e:
            upload_errors.append(f"Failed to upload {doc['name']}: {str(e)}")
    
    result = {
        'success': len(upload_errors) == 0,
        'uploaded_files': uploaded_files,
        'upload_errors': upload_errors,
        'files_uploaded': len(uploaded_files)
    }
"""
        })
        
        # Step 2: Document content analysis and item extraction
        workflow.add_node("PythonCodeNode", "content_analysis", {
            "code": """
import re
import os

def analyze_document_content(upload_result):
    '''Analyze uploaded documents and extract purchasable items'''
    
    if not upload_result.get('success', False):
        result = {
            'success': False,
            'error': 'Document upload failed',
            'items_extracted': []
        }
        return result
    
    extracted_items = []
    analysis_errors = []
    
    for file_info in upload_result['uploaded_files']:
        try:
            with open(file_info['stored_path'], 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract items using various patterns
            patterns = [
                # Pattern 1: Item: Description - $Price
                r'(?i)(item\\s*\\d+\\s*:?\\s*)([^$\\n]+)\\s*-\\s*\\$([\\d,.]+)',
                # Pattern 2: Product Name $Price
                r'(?i)([a-zA-Z][a-zA-Z0-9\\s]+)\\s+\\$([\\d,.]+)(?=\\s|$|\\n)',
                # Pattern 3: Quantity x Description @ $Price
                r'(?i)(\\d+)\\s*x\\s*([^@\\n]+)\\s*@\\s*\\$([\\d,.]+)',
                # Pattern 4: Description: $Price
                r'(?i)([^:\\n]+):\\s*\\$([\\d,.]+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if len(match) >= 2:
                        if len(match) == 3 and match[0].isdigit():
                            # Quantity x Description @ Price
                            quantity = int(match[0])
                            description = match[1].strip()
                            price = float(match[2].replace(',', ''))
                        elif len(match) == 3:
                            # Item: Description - Price  
                            description = match[1].strip()
                            price = float(match[2].replace(',', ''))
                            quantity = 1
                        else:
                            # Description: Price
                            description = match[0].strip()
                            price = float(match[1].replace(',', ''))
                            quantity = 1
                        
                        if description and price > 0 and len(description) > 3:
                            item = {
                                'description': description,
                                'price': price,
                                'quantity': quantity,
                                'source_file': file_info['original_name'],
                                'confidence': 0.8
                            }
                            
                            # Avoid duplicates
                            if not any(existing['description'].lower() == description.lower() 
                                     for existing in extracted_items):
                                extracted_items.append(item)
            
        except Exception as e:
            analysis_errors.append(f"Failed to analyze {file_info['original_name']}: {str(e)}")
    
    result = {
        'success': len(analysis_errors) == 0,
        'items_extracted': extracted_items,
        'total_items': len(extracted_items),
        'analysis_errors': analysis_errors,
        'files_analyzed': len(upload_result['uploaded_files'])
    }
"""
        })
        
        # Step 3: Product matching with database search
        workflow.add_node("PythonCodeNode", "product_matching", {
            "code": """
import psycopg2
from psycopg2.extras import RealDictCursor
import difflib

def match_items_to_products(analysis_result, postgres_params):
    '''Match extracted items to products in database'''
    
    if not analysis_result.get('success', False):
        result = {
            'success': False,
            'error': 'Content analysis failed',
            'matched_products': []
        }
        return result
    
    matched_products = []
    matching_errors = []
    
    try:
        conn = psycopg2.connect(**postgres_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all available products for matching
        products_sql = '''
            SELECT p.id, p.sku, p.name, p.description, pp.list_price, p.currency
            FROM horme.products p
            LEFT JOIN horme.product_pricing pp ON p.id = pp.product_id
            WHERE p.is_published = true
            ORDER BY p.id
        '''
        
        cursor.execute(products_sql)
        available_products = cursor.fetchall()
        
        for item in analysis_result['items_extracted']:
            best_match = None
            best_score = 0
            
            # Try to match against product names and descriptions
            for product in available_products:
                # Calculate similarity scores
                name_score = difflib.SequenceMatcher(None, 
                    item['description'].lower(), 
                    product['name'].lower()).ratio()
                
                desc_score = difflib.SequenceMatcher(None,
                    item['description'].lower(),
                    (product['description'] or '').lower()).ratio()
                
                combined_score = max(name_score, desc_score * 0.8)
                
                if combined_score > best_score and combined_score > 0.3:
                    best_score = combined_score
                    best_match = product
            
            if best_match:
                matched_products.append({
                    'original_item': item,
                    'matched_product': {
                        'id': best_match['id'],
                        'sku': best_match['sku'], 
                        'name': best_match['name'],
                        'description': best_match['description'],
                        'list_price': float(best_match['list_price']) if best_match['list_price'] else None,
                        'currency': best_match['currency']
                    },
                    'match_score': best_score,
                    'quantity': item['quantity'],
                    'estimated_total': (float(best_match['list_price']) if best_match['list_price'] else item['price']) * item['quantity']
                })
            else:
                # No match found - could be added as custom item
                matched_products.append({
                    'original_item': item,
                    'matched_product': None,
                    'match_score': 0,
                    'quantity': item['quantity'],
                    'estimated_total': item['price'] * item['quantity'],
                    'custom_item': True
                })
        
        cursor.close()
        conn.close()
        
        result = {
            'success': True,
            'matched_products': matched_products,
            'total_matches': len([m for m in matched_products if m['matched_product']]),
            'custom_items': len([m for m in matched_products if not m['matched_product']]),
            'estimated_total_value': sum(m['estimated_total'] for m in matched_products)
        }
        
    except Exception as e:
        result = {
            'success': False,
            'error': str(e),
            'matched_products': []
        }
"""
        })
        
        # Step 4: Quotation generation
        workflow.add_node("PythonCodeNode", "quotation_generation", {
            "code": """
import psycopg2
from psycopg2.extras import RealDictCursor
import time

def generate_quotation(matching_result, user_id, postgres_params):
    '''Generate quotation from matched products'''
    
    if not matching_result.get('success', False):
        result = {
            'success': False,
            'error': 'Product matching failed',
            'quotation': None
        }
        return result
    
    try:
        conn = psycopg2.connect(**postgres_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Calculate totals
        total_amount = matching_result['estimated_total_value']
        
        # Generate quote number
        timestamp = int(time.time())
        quote_number = f'E2E-{timestamp}'
        
        # Create quotation record
        quotation_sql = '''
            INSERT INTO horme.quotations 
            (quote_number, user_id, status, total_amount, currency, valid_until, notes, metadata)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP + INTERVAL '30 days', %s, %s)
            RETURNING id, quote_number, status, total_amount, created_at
        '''
        
        notes = f'Generated from document analysis. {matching_result["total_matches"]} matched products, {matching_result["custom_items"]} custom items.'
        metadata = {
            'generated_from': 'e2e_test',
            'total_matches': matching_result['total_matches'],
            'custom_items': matching_result['custom_items'],
            'processing_pipeline': 'upload_analysis_matching'
        }
        
        cursor.execute(quotation_sql, [
            quote_number, user_id, 'draft', total_amount, 'USD', notes,
            psycopg2.extras.Json(metadata)
        ])
        
        quotation = cursor.fetchone()
        quotation_id = quotation['id']
        
        # Add quotation items
        items_added = 0
        for match in matching_result['matched_products']:
            if match['matched_product']:  # Only add matched products
                item_sql = '''
                    INSERT INTO horme.quotation_items 
                    (quotation_id, product_id, quantity, unit_price, total_price, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                '''
                
                product = match['matched_product']
                quantity = match['quantity']
                unit_price = product['list_price'] or match['original_item']['price']
                total_price = unit_price * quantity
                
                notes = f"Matched from: {match['original_item']['description']} (score: {match['match_score']:.2f})"
                
                cursor.execute(item_sql, [
                    quotation_id, product['id'], quantity, unit_price, total_price, notes
                ])
                
                items_added += 1
        
        cursor.close()
        conn.close()
        
        result = {
            'success': True,
            'quotation': {
                'id': quotation_id,
                'quote_number': quote_number,
                'status': quotation['status'],
                'total_amount': float(quotation['total_amount']),
                'created_at': quotation['created_at'].isoformat(),
                'items_count': items_added
            },
            'pipeline_summary': {
                'documents_processed': matching_result.get('files_analyzed', 0),
                'items_extracted': len(matching_result['matched_products']),
                'products_matched': matching_result['total_matches'],
                'quotation_items': items_added,
                'estimated_value': total_amount
            }
        }
        
    except Exception as e:
        result = {
            'success': False,
            'error': str(e),
            'quotation': None
        }
"""
        })
        
        # Connect all workflow nodes
        workflow.add_connection("document_upload", "result", "content_analysis", "upload_result")
        workflow.add_connection("content_analysis", "result", "product_matching", "analysis_result")
        workflow.add_connection("product_matching", "result", "quotation_generation", "matching_result")
        
        # Prepare test documents with realistic content
        test_documents = [
            {
                'name': 'rfp_electronics.txt',
                'content': '''Request for Proposal - Electronics Equipment
                
Item 1: Laptop Computer - $999.99
Item 2: Wireless Mouse - $29.99
Item 3: Mechanical Keyboard - $129.99
Item 4: USB Cable - $19.99
Item 5: Power Adapter - $49.99

Additional Requirements:
- 2x Monitor Stands @ $89.99
- External Hard Drive: $149.99
- Webcam: $79.99

Total estimated budget: $1,549.91''',
                'mime_type': 'text/plain'
            },
            {
                'name': 'parts_list.txt',
                'content': '''Parts and Components List
                
Test Product 1: $10.50
Test Product 2 - $25.75  
Test Product 3: $15.25
Component A @ $35.00
Component B: $45.50

Notes: All prices subject to availability''',
                'mime_type': 'text/plain'
            }
        ]
        
        # Execute complete end-to-end workflow
        postgres_params = full_infrastructure['postgres']
        
        results, run_id = runtime.execute(workflow.build(), {
            "document_upload": {
                "documents": test_documents,
                "upload_dir": temp_upload_directory,
                "user_id": 1
            },
            "product_matching": {
                "postgres_params": postgres_params
            },
            "quotation_generation": {
                "user_id": 1,
                "postgres_params": postgres_params
            }
        })
        
        # Validate complete workflow execution
        upload_result = results.get('document_upload', {})
        assert upload_result['success'] is True
        assert upload_result['files_uploaded'] == 2
        
        analysis_result = results.get('content_analysis', {})
        assert analysis_result['success'] is True
        assert analysis_result['total_items'] > 0  # Should extract items
        
        matching_result = results.get('product_matching', {})
        assert matching_result['success'] is True
        assert len(matching_result['matched_products']) > 0
        
        quotation_result = results.get('quotation_generation', {})
        assert quotation_result['success'] is True
        
        quotation = quotation_result['quotation']
        assert quotation['id'] > 0
        assert quotation['quote_number'].startswith('E2E-')
        assert quotation['status'] == 'draft'
        assert quotation['total_amount'] > 0
        assert quotation['items_count'] >= 0
        
        # Validate pipeline summary
        summary = quotation_result['pipeline_summary']
        assert summary['documents_processed'] == 2
        assert summary['items_extracted'] > 0
        assert summary['estimated_value'] > 0
        
        # Performance validation
        assert all(key in results for key in ['document_upload', 'content_analysis', 'product_matching', 'quotation_generation'])

class TestCompleteSearchAndAnalyticsWorkflow:
    """End-to-end test of search, caching, and analytics workflow"""
    
    @test_timeout
    def test_search_analytics_pipeline(self, full_infrastructure, runtime):
        """Test complete search -> cache -> analytics -> reporting workflow"""
        workflow = WorkflowBuilder()
        
        # Step 1: Multi-criteria product search
        workflow.add_node("PythonCodeNode", "advanced_search", {
            "code": """
import psycopg2
from psycopg2.extras import RealDictCursor
import time

def execute_advanced_product_search(search_criteria, postgres_params):
    '''Execute advanced product search with multiple criteria'''
    
    start_time = time.time()
    
    try:
        conn = psycopg2.connect(**postgres_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build dynamic search query
        base_sql = '''
            SELECT p.id, p.sku, p.name, p.description, p.enriched_description,
                   pp.list_price, p.currency, p.availability,
                   b.name as brand, c.name as category,
                   CASE WHEN %s != '' THEN
                       ts_rank(to_tsvector('english', 
                           COALESCE(p.name, '') || ' ' || 
                           COALESCE(p.description, '') || ' ' ||
                           COALESCE(p.enriched_description, '')
                       ), plainto_tsquery('english', %s))
                   ELSE 1
                   END as relevance_score
            FROM horme.products p
            LEFT JOIN horme.product_pricing pp ON p.id = pp.product_id
            LEFT JOIN horme.brands b ON p.brand_id = b.id
            LEFT JOIN horme.categories c ON p.category_id = c.id
            WHERE p.is_published = true
        '''
        
        params = [search_criteria.get('query', ''), search_criteria.get('query', '')]
        
        # Add filters
        if search_criteria.get('query'):
            base_sql += ''' AND to_tsvector('english', 
                COALESCE(p.name, '') || ' ' || 
                COALESCE(p.description, '') || ' ' ||
                COALESCE(p.enriched_description, '')
            ) @@ plainto_tsquery('english', %s) '''
            params.append(search_criteria['query'])
        
        if search_criteria.get('category'):
            base_sql += ' AND LOWER(c.name) LIKE LOWER(%s) '
            params.append(f"%{search_criteria['category']}%")
        
        if search_criteria.get('min_price'):
            base_sql += ' AND pp.list_price >= %s '
            params.append(search_criteria['min_price'])
        
        if search_criteria.get('max_price'):
            base_sql += ' AND pp.list_price <= %s '
            params.append(search_criteria['max_price'])
        
        # Order and limit
        base_sql += ' ORDER BY relevance_score DESC, p.id LIMIT %s'
        params.append(search_criteria.get('limit', 20))
        
        cursor.execute(base_sql, params)
        rows = cursor.fetchall()
        
        # Convert to list format
        search_results = []
        for row in rows:
            search_results.append({
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
                'relevance_score': float(row['relevance_score']) if row['relevance_score'] else 0.0
            })
        
        cursor.close()
        conn.close()
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        result = {
            'success': True,
            'results': search_results,
            'total_results': len(search_results),
            'search_criteria': search_criteria,
            'execution_time_ms': execution_time_ms,
            'performance_metrics': {
                'search_time_ms': execution_time_ms,
                'results_per_second': len(search_results) / (execution_time_ms / 1000) if execution_time_ms > 0 else 0
            }
        }
        
    except Exception as e:
        result = {
            'success': False,
            'results': [],
            'error': str(e),
            'search_criteria': search_criteria
        }
"""
        })
        
        # Step 2: Search result caching and analytics
        workflow.add_node("PythonCodeNode", "cache_and_analytics", {
            "code": """
import redis
import json
import time
import hashlib

def cache_results_and_generate_analytics(search_result, redis_params):
    '''Cache search results and generate search analytics'''
    
    if not search_result.get('success', False):
        result = {
            'success': False,
            'error': 'Search failed',
            'analytics': None
        }
        return result
    
    try:
        r = redis.Redis(**redis_params)
        current_time = time.time()
        
        # Generate cache key
        search_criteria = search_result['search_criteria']
        cache_key_data = json.dumps(search_criteria, sort_keys=True)
        cache_key = f"search:{hashlib.md5(cache_key_data.encode()).hexdigest()}"
        
        # Cache the results
        cache_data = {
            'results': search_result['results'],
            'metadata': {
                'total_results': search_result['total_results'],
                'execution_time_ms': search_result['execution_time_ms'],
                'cached_at': current_time,
                'search_criteria': search_criteria
            }
        }
        
        # Cache for 10 minutes
        r.setex(cache_key, 600, json.dumps(cache_data))
        
        # Generate analytics data
        results = search_result['results']
        
        # Price analytics
        prices = [r['price'] for r in results if r['price'] is not None]
        price_analytics = {
            'avg_price': sum(prices) / len(prices) if prices else 0,
            'min_price': min(prices) if prices else 0,
            'max_price': max(prices) if prices else 0,
            'price_range': max(prices) - min(prices) if prices else 0
        }
        
        # Category distribution
        categories = {}
        for r in results:
            cat = r['category'] or 'Unknown'
            categories[cat] = categories.get(cat, 0) + 1
        
        # Brand distribution
        brands = {}
        for r in results:
            brand = r['brand'] or 'Unknown'
            brands[brand] = brands.get(brand, 0) + 1
        
        # Performance metrics
        performance = {
            'search_time_ms': search_result['execution_time_ms'],
            'cache_time_ms': (time.time() - current_time) * 1000,
            'results_per_ms': search_result['total_results'] / search_result['execution_time_ms'] if search_result['execution_time_ms'] > 0 else 0
        }
        
        # Store analytics in Redis
        analytics_key = f"analytics:search:{int(current_time)}"
        analytics_data = {
            'timestamp': current_time,
            'search_criteria': search_criteria,
            'results_count': search_result['total_results'],
            'price_analytics': price_analytics,
            'category_distribution': categories,
            'brand_distribution': brands,
            'performance_metrics': performance
        }
        
        r.setex(analytics_key, 3600, json.dumps(analytics_data))  # 1 hour
        
        result = {
            'success': True,
            'cache_key': cache_key,
            'analytics_key': analytics_key,
            'analytics': analytics_data,
            'cache_stored': True
        }
        
    except Exception as e:
        result = {
            'success': False,
            'error': str(e),
            'analytics': None
        }
"""
        })
        
        # Step 3: Performance monitoring and alerting
        workflow.add_node("PythonCodeNode", "performance_monitoring", {
            "code": """
import redis
import json
import time

def monitor_search_performance(analytics_result, performance_thresholds, redis_params):
    '''Monitor search performance and generate alerts'''
    
    if not analytics_result.get('success', False):
        result = {
            'success': False,
            'error': 'Analytics generation failed',
            'alerts': []
        }
        return result
    
    try:
        r = redis.Redis(**redis_params)
        analytics = analytics_result['analytics']
        
        alerts = []
        performance_status = 'healthy'
        
        # Check search time performance
        search_time = analytics['performance_metrics']['search_time_ms']
        if search_time > performance_thresholds.get('max_search_time_ms', 1000):
            alerts.append({
                'type': 'performance',
                'severity': 'warning',
                'message': f'Search time {search_time:.2f}ms exceeds threshold {performance_thresholds["max_search_time_ms"]}ms',
                'metric': 'search_time_ms',
                'value': search_time
            })
            performance_status = 'degraded'
        
        # Check results efficiency
        results_per_ms = analytics['performance_metrics']['results_per_ms']
        min_efficiency = performance_thresholds.get('min_results_per_ms', 0.1)
        if results_per_ms < min_efficiency:
            alerts.append({
                'type': 'efficiency',
                'severity': 'info',
                'message': f'Search efficiency {results_per_ms:.3f} results/ms below optimal {min_efficiency}',
                'metric': 'results_per_ms',
                'value': results_per_ms
            })
        
        # Check result diversity
        categories = analytics['category_distribution']
        if len(categories) == 1 and analytics['results_count'] > 5:
            alerts.append({
                'type': 'diversity',
                'severity': 'info', 
                'message': f'Low result diversity: all {analytics["results_count"]} results from single category',
                'metric': 'category_diversity',
                'value': len(categories)
            })
        
        # Store performance data
        perf_key = f"performance:search:{int(time.time())}"
        performance_data = {
            'timestamp': time.time(),
            'performance_status': performance_status,
            'alerts': alerts,
            'metrics': {
                'search_time_ms': search_time,
                'results_count': analytics['results_count'],
                'results_per_ms': results_per_ms,
                'category_count': len(categories)
            },
            'thresholds': performance_thresholds
        }
        
        r.setex(perf_key, 3600, json.dumps(performance_data))
        
        result = {
            'success': True,
            'performance_key': perf_key,
            'performance_status': performance_status,
            'alerts': alerts,
            'metrics_summary': {
                'search_time_healthy': search_time <= performance_thresholds.get('max_search_time_ms', 1000),
                'efficiency_adequate': results_per_ms >= min_efficiency,
                'total_alerts': len(alerts)
            }
        }
        
    except Exception as e:
        result = {
            'success': False,
            'error': str(e),
            'alerts': []
        }
"""
        })
        
        # Connect workflow nodes
        workflow.add_connection("advanced_search", "result", "cache_and_analytics", "search_result")
        workflow.add_connection("cache_and_analytics", "result", "performance_monitoring", "analytics_result")
        
        # Execute complete search and analytics workflow
        postgres_params = full_infrastructure['postgres']
        redis_params = full_infrastructure['redis']
        
        # Test search criteria
        search_criteria = {
            'query': 'test product',
            'category': '',
            'min_price': 10.0,
            'max_price': 1000.0,
            'limit': 15
        }
        
        performance_thresholds = {
            'max_search_time_ms': 3000,  # 3 seconds
            'min_results_per_ms': 0.05,
            'min_category_diversity': 2
        }
        
        results, run_id = runtime.execute(workflow.build(), {
            "advanced_search": {
                "search_criteria": search_criteria,
                "postgres_params": postgres_params
            },
            "cache_and_analytics": {
                "redis_params": redis_params
            },
            "performance_monitoring": {
                "performance_thresholds": performance_thresholds,
                "redis_params": redis_params
            }
        })
        
        # Validate complete search analytics workflow
        search_result = results.get('advanced_search', {})
        assert search_result['success'] is True
        assert 'results' in search_result
        assert search_result['execution_time_ms'] < 5000  # Should be fast
        
        analytics_result = results.get('cache_and_analytics', {})
        assert analytics_result['success'] is True
        assert analytics_result['cache_stored'] is True
        
        analytics = analytics_result['analytics']
        assert 'price_analytics' in analytics
        assert 'category_distribution' in analytics
        assert 'brand_distribution' in analytics
        assert 'performance_metrics' in analytics
        
        monitoring_result = results.get('performance_monitoring', {})
        assert monitoring_result['success'] is True
        assert monitoring_result['performance_status'] in ['healthy', 'degraded', 'critical']
        assert isinstance(monitoring_result['alerts'], list)
        
        # Validate performance metrics
        metrics_summary = monitoring_result['metrics_summary']
        assert isinstance(metrics_summary['search_time_healthy'], bool)
        assert isinstance(metrics_summary['efficiency_adequate'], bool)
        assert metrics_summary['total_alerts'] >= 0

class TestRealTimeQuotationUpdates:
    """End-to-end test of real-time quotation updates and notifications"""
    
    @test_timeout
    def test_quotation_lifecycle_workflow(self, full_infrastructure, runtime):
        """Test complete quotation lifecycle with real-time updates"""
        workflow = WorkflowBuilder()
        
        # Step 1: Create initial quotation
        workflow.add_node("PythonCodeNode", "create_initial_quotation", {
            "code": """
import psycopg2
from psycopg2.extras import RealDictCursor
import time

def create_quotation_with_items(quotation_data, postgres_params):
    '''Create quotation with initial items'''
    
    try:
        conn = psycopg2.connect(**postgres_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Create quotation
        quote_sql = '''
            INSERT INTO horme.quotations 
            (quote_number, user_id, status, total_amount, currency, valid_until, notes, metadata)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP + INTERVAL '30 days', %s, %s)
            RETURNING id, quote_number, created_at
        '''
        
        timestamp = int(time.time())
        quote_number = f'LC-{timestamp}'
        
        cursor.execute(quote_sql, [
            quote_number, quotation_data['user_id'], 'draft', 0, 'USD',
            'Lifecycle test quotation', psycopg2.extras.Json({'test': 'lifecycle'})
        ])
        
        quotation = cursor.fetchone()
        quotation_id = quotation['id']
        
        # Add initial items
        total_amount = 0
        items_added = 0
        
        for item in quotation_data['items']:
            # Get product for pricing
            product_sql = 'SELECT id, name FROM horme.products WHERE sku = %s LIMIT 1'
            cursor.execute(product_sql, [item['sku']])
            product = cursor.fetchone()
            
            if product:
                unit_price = item['unit_price']
                quantity = item['quantity']
                total_price = unit_price * quantity
                
                item_sql = '''
                    INSERT INTO horme.quotation_items 
                    (quotation_id, product_id, quantity, unit_price, total_price, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                '''
                
                cursor.execute(item_sql, [
                    quotation_id, product['id'], quantity, unit_price, total_price, 
                    f"Initial item: {product['name']}"
                ])
                
                total_amount += total_price
                items_added += 1
        
        # Update quotation total
        update_sql = 'UPDATE horme.quotations SET total_amount = %s WHERE id = %s'
        cursor.execute(update_sql, [total_amount, quotation_id])
        
        cursor.close()
        conn.close()
        
        result = {
            'success': True,
            'quotation': {
                'id': quotation_id,
                'quote_number': quote_number,
                'total_amount': total_amount,
                'items_count': items_added,
                'created_at': quotation['created_at'].isoformat()
            }
        }
        
    except Exception as e:
        result = {
            'success': False,
            'error': str(e),
            'quotation': None
        }
"""
        })
        
        # Step 2: Process quotation updates
        workflow.add_node("PythonCodeNode", "process_updates", {
            "code": """
import psycopg2
from psycopg2.extras import RealDictCursor
import time

def process_quotation_updates(initial_result, updates, postgres_params):
    '''Process series of quotation updates'''
    
    if not initial_result.get('success', False):
        result = {
            'success': False,
            'error': 'Initial quotation creation failed'
        }
        return result
    
    try:
        conn = psycopg2.connect(**postgres_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        quotation_id = initial_result['quotation']['id']
        update_history = []
        
        for update in updates:
            update_start = time.time()
            
            if update['type'] == 'add_item':
                # Add new quotation item
                product_sql = 'SELECT id, name FROM horme.products WHERE sku = %s LIMIT 1'
                cursor.execute(product_sql, [update['sku']])
                product = cursor.fetchone()
                
                if product:
                    unit_price = update['unit_price']
                    quantity = update['quantity']
                    total_price = unit_price * quantity
                    
                    item_sql = '''
                        INSERT INTO horme.quotation_items 
                        (quotation_id, product_id, quantity, unit_price, total_price, notes)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    '''
                    
                    cursor.execute(item_sql, [
                        quotation_id, product['id'], quantity, unit_price, total_price,
                        f"Added via update: {product['name']}"
                    ])
                    
                    item_id = cursor.fetchone()['id']
                    
                    update_history.append({
                        'type': 'add_item',
                        'item_id': item_id,
                        'sku': update['sku'],
                        'success': True,
                        'processing_time_ms': (time.time() - update_start) * 1000
                    })
                else:
                    update_history.append({
                        'type': 'add_item',
                        'sku': update['sku'],
                        'success': False,
                        'error': 'Product not found'
                    })
            
            elif update['type'] == 'update_status':
                # Update quotation status
                status_sql = 'UPDATE horme.quotations SET status = %s WHERE id = %s'
                cursor.execute(status_sql, [update['status'], quotation_id])
                
                update_history.append({
                    'type': 'update_status',
                    'new_status': update['status'],
                    'success': True,
                    'processing_time_ms': (time.time() - update_start) * 1000
                })
        
        # Recalculate total
        total_sql = '''
            SELECT COALESCE(SUM(total_price), 0) as total 
            FROM horme.quotation_items 
            WHERE quotation_id = %s
        '''
        cursor.execute(total_sql, [quotation_id])
        new_total = float(cursor.fetchone()['total'])
        
        # Update quotation total
        update_total_sql = 'UPDATE horme.quotations SET total_amount = %s WHERE id = %s'
        cursor.execute(update_total_sql, [new_total, quotation_id])
        
        # Get final quotation state
        final_sql = '''
            SELECT quote_number, status, total_amount, 
                   (SELECT COUNT(*) FROM horme.quotation_items WHERE quotation_id = %s) as items_count
            FROM horme.quotations WHERE id = %s
        '''
        cursor.execute(final_sql, [quotation_id, quotation_id])
        final_quotation = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        result = {
            'success': True,
            'quotation_id': quotation_id,
            'update_history': update_history,
            'updates_processed': len([u for u in update_history if u.get('success', False)]),
            'final_quotation': {
                'quote_number': final_quotation['quote_number'],
                'status': final_quotation['status'],
                'total_amount': float(final_quotation['total_amount']),
                'items_count': final_quotation['items_count']
            }
        }
        
    except Exception as e:
        result = {
            'success': False,
            'error': str(e),
            'quotation_id': quotation_id if 'quotation_id' in locals() else None
        }
"""
        })
        
        # Connect workflow nodes  
        workflow.add_connection("create_initial_quotation", "result", "process_updates", "initial_result")
        
        # Execute quotation lifecycle workflow
        postgres_params = full_infrastructure['postgres']
        
        # Initial quotation data
        initial_quotation = {
            'user_id': 1,
            'items': [
                {'sku': 'TEST-000001', 'quantity': 2, 'unit_price': 50.00},
                {'sku': 'TEST-000002', 'quantity': 1, 'unit_price': 25.00}
            ]
        }
        
        # Series of updates to process
        quotation_updates = [
            {'type': 'add_item', 'sku': 'TEST-000003', 'quantity': 1, 'unit_price': 75.00},
            {'type': 'update_status', 'status': 'sent'},
            {'type': 'add_item', 'sku': 'TEST-000004', 'quantity': 3, 'unit_price': 15.00}
        ]
        
        results, run_id = runtime.execute(workflow.build(), {
            "create_initial_quotation": {
                "quotation_data": initial_quotation,
                "postgres_params": postgres_params
            },
            "process_updates": {
                "updates": quotation_updates,
                "postgres_params": postgres_params
            }
        })
        
        # Validate quotation lifecycle
        initial_result = results.get('create_initial_quotation', {})
        assert initial_result['success'] is True
        
        initial_quotation_data = initial_result['quotation']
        assert initial_quotation_data['quote_number'].startswith('LC-')
        assert initial_quotation_data['total_amount'] >= 0
        
        updates_result = results.get('process_updates', {})
        assert updates_result['success'] is True
        assert updates_result['updates_processed'] >= 0
        
        final_quotation = updates_result['final_quotation']
        assert final_quotation['quote_number'] == initial_quotation_data['quote_number']
        assert final_quotation['items_count'] >= initial_quotation_data['items_count']
        
        # Validate update history
        update_history = updates_result['update_history']
        assert len(update_history) == len(quotation_updates)
        
        # Should have processed status update
        status_updates = [u for u in update_history if u['type'] == 'update_status']
        assert len(status_updates) >= 1
        assert any(u.get('success', False) for u in status_updates)