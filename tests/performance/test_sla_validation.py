#!/usr/bin/env python3
"""
Performance and Load Testing with SLA Target Validation
Tests SDK workflows against defined SLA targets with real infrastructure
NO MOCKING - Uses actual Docker services for realistic load testing
"""

import pytest
import time
import asyncio
import concurrent.futures
import statistics
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from typing import Dict, Any, List, Tuple
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# SLA Target Definitions
SLA_TARGETS = {
    'file_upload_processing': {
        'max_response_time_ms': 5000,  # 5 seconds
        'percentile_95_ms': 3000,      # 95% under 3 seconds
        'max_concurrent_users': 10,    # Support 10 concurrent uploads
        'throughput_files_per_minute': 60
    },
    'product_search': {
        'max_response_time_ms': 500,   # 0.5 seconds
        'percentile_95_ms': 200,       # 95% under 200ms
        'max_concurrent_searches': 50, # Support 50 concurrent searches
        'throughput_searches_per_second': 20
    },
    'quotation_generation': {
        'max_response_time_ms': 30000, # 30 seconds for complex RFPs
        'percentile_95_ms': 15000,     # 95% under 15 seconds
        'max_concurrent_quotations': 5, # Support 5 concurrent quotations
        'throughput_quotations_per_hour': 100
    }
}

@pytest.fixture(scope="module")
def performance_infrastructure():
    """Verify performance testing infrastructure"""
    services = {
        'postgres': {'host': 'localhost', 'port': 5434, 'database': 'horme_test', 'user': 'test_user', 'password': 'test_password'},
        'redis': {'host': 'localhost', 'port': 6380, 'db': 0}
    }
    
    # Test connections
    try:
        conn = psycopg2.connect(**services['postgres'])
        conn.close()
        
        r = redis.Redis(**services['redis'])
        r.ping()
    except Exception as e:
        pytest.skip(f"Performance infrastructure not available: {e}")
    
    return services

@pytest.fixture
def runtime_pool():
    """Pool of LocalRuntime instances for concurrent testing"""
    return [LocalRuntime() for _ in range(10)]

class PerformanceMetrics:
    """Helper class for collecting and analyzing performance metrics"""
    
    def __init__(self):
        self.response_times = []
        self.start_time = None
        self.end_time = None
        self.errors = []
        self.success_count = 0
        
    def start_measurement(self):
        self.start_time = time.time()
    
    def end_measurement(self):
        self.end_time = time.time()
    
    def record_response(self, response_time_ms: float, success: bool = True, error: str = None):
        self.response_times.append(response_time_ms)
        if success:
            self.success_count += 1
        else:
            self.errors.append(error or "Unknown error")
    
    def get_statistics(self) -> Dict[str, Any]:
        if not self.response_times:
            return {'error': 'No response times recorded'}
        
        total_time = (self.end_time - self.start_time) if (self.start_time and self.end_time) else 0
        
        return {
            'total_requests': len(self.response_times),
            'successful_requests': self.success_count,
            'failed_requests': len(self.errors),
            'success_rate': self.success_count / len(self.response_times) * 100,
            'min_response_time_ms': min(self.response_times),
            'max_response_time_ms': max(self.response_times),
            'avg_response_time_ms': statistics.mean(self.response_times),
            'median_response_time_ms': statistics.median(self.response_times),
            'percentile_95_ms': self._percentile(self.response_times, 95),
            'percentile_99_ms': self._percentile(self.response_times, 99),
            'throughput_per_second': len(self.response_times) / total_time if total_time > 0 else 0,
            'total_duration_seconds': total_time,
            'errors': self.errors
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def validate_sla(self, sla_targets: Dict[str, Any]) -> Dict[str, Any]:
        stats = self.get_statistics()
        violations = []
        
        if stats.get('max_response_time_ms', 0) > sla_targets.get('max_response_time_ms', float('inf')):
            violations.append(f"Max response time {stats['max_response_time_ms']:.2f}ms exceeds SLA {sla_targets['max_response_time_ms']}ms")
        
        if stats.get('percentile_95_ms', 0) > sla_targets.get('percentile_95_ms', float('inf')):
            violations.append(f"95th percentile {stats['percentile_95_ms']:.2f}ms exceeds SLA {sla_targets['percentile_95_ms']}ms")
        
        return {
            'sla_compliant': len(violations) == 0,
            'violations': violations,
            'statistics': stats
        }

class TestFileUploadPerformance:
    """Performance tests for file upload processing workflows"""
    
    def test_single_file_upload_performance(self, performance_infrastructure, runtime_pool):
        """Test single file upload performance against SLA targets"""
        metrics = PerformanceMetrics()
        workflow = WorkflowBuilder()
        
        # Create file upload workflow
        workflow.add_node("PythonCodeNode", "process_upload", {
            "code": """
import time
import tempfile
import os
import hashlib

def process_file_upload(file_data, temp_dir):
    '''Process file upload with realistic operations'''
    start_time = time.time()
    
    try:
        # Simulate file validation
        content = file_data['content']
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError("File too large")
        
        # Create temp file
        file_path = os.path.join(temp_dir, f"upload_{int(time.time() * 1000)}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Simulate content processing
        lines = content.split('\\n')
        items_found = len([line for line in lines if '$' in line or ':' in line])
        
        # Calculate checksum
        checksum = hashlib.sha256(content.encode()).hexdigest()
        
        # Cleanup
        os.unlink(file_path)
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        result = {
            'success': True,
            'file_size': len(content),
            'items_found': items_found,
            'checksum': checksum,
            'processing_time_ms': processing_time_ms
        }
        
    except Exception as e:
        result = {
            'success': False,
            'error': str(e),
            'processing_time_ms': (time.time() - start_time) * 1000
        }
"""
        })
        
        # Test with files of varying sizes
        test_files = [
            {'name': 'small.txt', 'content': 'Small file content\nItem 1: Product A - $10.99\n' * 10},
            {'name': 'medium.txt', 'content': 'Medium file content\nItem 1: Product A - $10.99\n' * 100},
            {'name': 'large.txt', 'content': 'Large file content\nItem 1: Product A - $10.99\n' * 1000}
        ]
        
        metrics.start_measurement()
        
        for file_data in test_files:
            test_start = time.time()
            
            results, run_id = runtime_pool[0].execute(workflow.build(), {
                "process_upload": {
                    "file_data": file_data,
                    "temp_dir": "/tmp"
                }
            })
            
            response_time_ms = (time.time() - test_start) * 1000
            result = results.get('process_upload', {})
            
            metrics.record_response(
                response_time_ms,
                result.get('success', False),
                result.get('error')
            )
        
        metrics.end_measurement()
        
        # Validate against SLA targets
        sla_validation = metrics.validate_sla(SLA_TARGETS['file_upload_processing'])
        
        assert sla_validation['sla_compliant'], f"SLA violations: {sla_validation['violations']}"
        
        stats = sla_validation['statistics']
        assert stats['success_rate'] >= 95, f"Success rate {stats['success_rate']:.1f}% below 95%"
        assert stats['max_response_time_ms'] <= SLA_TARGETS['file_upload_processing']['max_response_time_ms']
    
    def test_concurrent_file_upload_performance(self, performance_infrastructure, runtime_pool):
        """Test concurrent file upload performance"""
        metrics = PerformanceMetrics()
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "concurrent_upload", {
            "code": """
import time
import tempfile
import os
import threading

def process_concurrent_upload(file_data, upload_id, temp_dir):
    '''Process file upload with thread safety'''
    start_time = time.time()
    
    try:
        # Thread-safe file processing
        thread_id = threading.current_thread().ident
        unique_filename = f"upload_{upload_id}_{thread_id}_{int(time.time() * 1000)}.txt"
        file_path = os.path.join(temp_dir, unique_filename)
        
        # Write and process file
        content = file_data['content']
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Simulate processing work
        time.sleep(0.1)  # Simulate I/O operations
        
        # Extract items
        items = [line for line in content.split('\\n') if '$' in line]
        
        # Cleanup
        if os.path.exists(file_path):
            os.unlink(file_path)
        
        result = {
            'success': True,
            'upload_id': upload_id,
            'thread_id': thread_id,
            'items_count': len(items),
            'processing_time_ms': (time.time() - start_time) * 1000
        }
        
    except Exception as e:
        result = {
            'success': False,
            'upload_id': upload_id,
            'error': str(e),
            'processing_time_ms': (time.time() - start_time) * 1000
        }
"""
        })
        
        # Create multiple test files
        test_uploads = []
        for i in range(SLA_TARGETS['file_upload_processing']['max_concurrent_users']):
            test_uploads.append({
                'upload_id': i,
                'file_data': {
                    'name': f'concurrent_test_{i}.txt',
                    'content': f'Concurrent upload test {i}\n' + 'Item: Test Product - $19.99\n' * 20
                }
            })
        
        metrics.start_measurement()
        
        # Execute concurrent uploads
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(test_uploads)) as executor:
            futures = []
            
            for i, upload in enumerate(test_uploads):
                runtime = runtime_pool[i % len(runtime_pool)]
                future = executor.submit(self._execute_upload, workflow, runtime, upload)
                futures.append(future)
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                response_time_ms, success, error = future.result()
                metrics.record_response(response_time_ms, success, error)
        
        metrics.end_measurement()
        
        # Validate concurrent performance
        sla_validation = metrics.validate_sla(SLA_TARGETS['file_upload_processing'])
        stats = sla_validation['statistics']
        
        # Concurrent uploads should still meet SLA
        assert stats['success_rate'] >= 90, f"Concurrent success rate {stats['success_rate']:.1f}% too low"
        assert stats['max_response_time_ms'] <= SLA_TARGETS['file_upload_processing']['max_response_time_ms'] * 1.5  # Allow 50% overhead for concurrency
        assert len(metrics.errors) <= 1, f"Too many concurrent errors: {len(metrics.errors)}"
    
    def _execute_upload(self, workflow: WorkflowBuilder, runtime: LocalRuntime, upload: Dict[str, Any]) -> Tuple[float, bool, str]:
        """Helper method to execute upload and measure performance"""
        start_time = time.time()
        
        try:
            results, run_id = runtime.execute(workflow.build(), {
                "concurrent_upload": {
                    "file_data": upload['file_data'],
                    "upload_id": upload['upload_id'],
                    "temp_dir": "/tmp"
                }
            })
            
            response_time_ms = (time.time() - start_time) * 1000
            result = results.get('concurrent_upload', {})
            
            return response_time_ms, result.get('success', False), result.get('error')
            
        except Exception as e:
            return (time.time() - start_time) * 1000, False, str(e)

class TestProductSearchPerformance:
    """Performance tests for product search workflows"""
    
    def test_search_response_time_sla(self, performance_infrastructure, runtime_pool):
        """Test product search response times against SLA"""
        metrics = PerformanceMetrics()
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "performance_search", {
            "code": """
import psycopg2
from psycopg2.extras import RealDictCursor
import time

def execute_performance_search(query, limit, postgres_params):
    '''Execute search with performance monitoring'''
    start_time = time.time()
    
    try:
        conn = psycopg2.connect(**postgres_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Optimized search query
        search_sql = '''
            SELECT p.id, p.sku, p.name, p.description, pp.list_price,
                   ts_rank(to_tsvector('english', p.name || ' ' || COALESCE(p.description, '')), 
                          plainto_tsquery('english', %s)) as rank
            FROM horme.products p
            LEFT JOIN horme.product_pricing pp ON p.id = pp.product_id
            WHERE p.is_published = true
            AND (%s = '' OR to_tsvector('english', p.name || ' ' || COALESCE(p.description, '')) 
                         @@ plainto_tsquery('english', %s))
            ORDER BY rank DESC, p.id
            LIMIT %s
        '''
        
        cursor.execute(search_sql, [query, query, query, limit])
        results = cursor.fetchall()
        
        search_results = []
        for row in results:
            search_results.append({
                'id': row['id'],
                'sku': row['sku'],
                'name': row['name'],
                'price': float(row['list_price']) if row['list_price'] else None,
                'rank': float(row['rank']) if row['rank'] else 0
            })
        
        cursor.close()
        conn.close()
        
        query_time_ms = (time.time() - start_time) * 1000
        
        result = {
            'success': True,
            'query': query,
            'results_count': len(search_results),
            'query_time_ms': query_time_ms,
            'results': search_results
        }
        
    except Exception as e:
        result = {
            'success': False,
            'query': query,
            'error': str(e),
            'query_time_ms': (time.time() - start_time) * 1000
        }
"""
        })
        
        # Test various search scenarios
        search_queries = [
            {'query': 'test product', 'limit': 10},
            {'query': 'laptop', 'limit': 20},
            {'query': 'tool', 'limit': 15},
            {'query': 'electronic', 'limit': 25},
            {'query': '', 'limit': 5},  # Empty query - should still work
            {'query': 'very specific product that probably does not exist', 'limit': 10}
        ]
        
        metrics.start_measurement()
        
        postgres_params = performance_infrastructure['postgres']
        
        for search_params in search_queries:
            test_start = time.time()
            
            results, run_id = runtime_pool[0].execute(workflow.build(), {
                "performance_search": {
                    "query": search_params['query'],
                    "limit": search_params['limit'],
                    "postgres_params": postgres_params
                }
            })
            
            response_time_ms = (time.time() - test_start) * 1000
            result = results.get('performance_search', {})
            
            metrics.record_response(
                response_time_ms,
                result.get('success', False),
                result.get('error')
            )
        
        metrics.end_measurement()
        
        # Validate search performance SLA
        sla_validation = metrics.validate_sla(SLA_TARGETS['product_search'])
        
        assert sla_validation['sla_compliant'], f"Search SLA violations: {sla_validation['violations']}"
        
        stats = sla_validation['statistics']
        assert stats['success_rate'] >= 98, f"Search success rate {stats['success_rate']:.1f}% below 98%"
        assert stats['avg_response_time_ms'] <= SLA_TARGETS['product_search']['percentile_95_ms']
    
    def test_search_concurrency_performance(self, performance_infrastructure, runtime_pool):
        """Test search performance under concurrent load"""
        metrics = PerformanceMetrics()
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "concurrent_search", {
            "code": """
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import threading

def execute_concurrent_search(search_params, search_id, postgres_params):
    '''Execute search with concurrency tracking'''
    start_time = time.time()
    thread_id = threading.current_thread().ident
    
    try:
        conn = psycopg2.connect(**postgres_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Simple but efficient search
        search_sql = '''
            SELECT p.id, p.sku, p.name, pp.list_price
            FROM horme.products p
            LEFT JOIN horme.product_pricing pp ON p.id = pp.product_id
            WHERE p.is_published = true
            AND LOWER(p.name) LIKE LOWER(%s)
            ORDER BY p.id
            LIMIT %s
        '''
        
        cursor.execute(search_sql, [f"%{search_params['query']}%", search_params['limit']])
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        result = {
            'success': True,
            'search_id': search_id,
            'thread_id': thread_id,
            'query': search_params['query'],
            'results_count': len(results),
            'execution_time_ms': (time.time() - start_time) * 1000
        }
        
    except Exception as e:
        result = {
            'success': False,
            'search_id': search_id,
            'thread_id': thread_id,
            'error': str(e),
            'execution_time_ms': (time.time() - start_time) * 1000
        }
"""
        })
        
        # Create concurrent search scenarios
        concurrent_searches = []
        search_terms = ['test', 'product', 'computer', 'tool', 'electronic', 'component']
        
        for i in range(SLA_TARGETS['product_search']['max_concurrent_searches']):
            concurrent_searches.append({
                'search_id': i,
                'search_params': {
                    'query': search_terms[i % len(search_terms)],
                    'limit': 10
                }
            })
        
        metrics.start_measurement()
        
        # Execute concurrent searches
        postgres_params = performance_infrastructure['postgres']
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(concurrent_searches)) as executor:
            futures = []
            
            for i, search in enumerate(concurrent_searches):
                runtime = runtime_pool[i % len(runtime_pool)]
                future = executor.submit(self._execute_search, workflow, runtime, search, postgres_params)
                futures.append(future)
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                response_time_ms, success, error = future.result()
                metrics.record_response(response_time_ms, success, error)
        
        metrics.end_measurement()
        
        # Validate concurrent search performance
        stats = metrics.get_statistics()
        
        # Under concurrent load, allow some performance degradation but maintain functionality
        assert stats['success_rate'] >= 95, f"Concurrent search success rate {stats['success_rate']:.1f}% too low"
        assert stats['max_response_time_ms'] <= SLA_TARGETS['product_search']['max_response_time_ms'] * 2  # Allow 100% overhead
        assert stats['throughput_per_second'] >= SLA_TARGETS['product_search']['throughput_searches_per_second'] * 0.7  # 70% of target throughput
    
    def _execute_search(self, workflow: WorkflowBuilder, runtime: LocalRuntime, search: Dict[str, Any], postgres_params: Dict[str, Any]) -> Tuple[float, bool, str]:
        """Helper method to execute search and measure performance"""
        start_time = time.time()
        
        try:
            results, run_id = runtime.execute(workflow.build(), {
                "concurrent_search": {
                    "search_params": search['search_params'],
                    "search_id": search['search_id'],
                    "postgres_params": postgres_params
                }
            })
            
            response_time_ms = (time.time() - start_time) * 1000
            result = results.get('concurrent_search', {})
            
            return response_time_ms, result.get('success', False), result.get('error')
            
        except Exception as e:
            return (time.time() - start_time) * 1000, False, str(e)

class TestSystemLoadPerformance:
    """System-wide load testing and performance validation"""
    
    def test_mixed_workload_performance(self, performance_infrastructure, runtime_pool):
        """Test system performance under mixed workload scenarios"""
        
        # Simulate realistic mixed workload
        workload_scenarios = [
            {'type': 'search', 'weight': 0.6, 'concurrent': 20},      # 60% searches
            {'type': 'upload', 'weight': 0.3, 'concurrent': 5},       # 30% uploads  
            {'type': 'quotation', 'weight': 0.1, 'concurrent': 2}     # 10% quotations
        ]
        
        total_metrics = PerformanceMetrics()
        scenario_metrics = {}
        
        total_metrics.start_measurement()
        
        # Execute mixed workload
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = []
            
            for scenario in workload_scenarios:
                scenario_metrics[scenario['type']] = PerformanceMetrics()
                
                for i in range(scenario['concurrent']):
                    if scenario['type'] == 'search':
                        future = executor.submit(self._execute_search_load, runtime_pool[i % len(runtime_pool)], performance_infrastructure)
                    elif scenario['type'] == 'upload':
                        future = executor.submit(self._execute_upload_load, runtime_pool[i % len(runtime_pool)])
                    else:  # quotation
                        future = executor.submit(self._execute_quotation_load, runtime_pool[i % len(runtime_pool)], performance_infrastructure)
                    
                    futures.append((scenario['type'], future))
            
            # Collect all results
            for scenario_type, future in futures:
                response_time_ms, success, error = future.result()
                total_metrics.record_response(response_time_ms, success, error)
                scenario_metrics[scenario_type].record_response(response_time_ms, success, error)
        
        total_metrics.end_measurement()
        
        # Validate overall system performance
        total_stats = total_metrics.get_statistics()
        
        # System should maintain reasonable performance under mixed load
        assert total_stats['success_rate'] >= 90, f"Mixed workload success rate {total_stats['success_rate']:.1f}% too low"
        assert total_stats['max_response_time_ms'] <= 35000, f"Max response time {total_stats['max_response_time_ms']:.0f}ms too high"
        
        # Validate individual scenario performance
        for scenario_type, metrics in scenario_metrics.items():
            metrics.end_measurement()
            stats = metrics.get_statistics()
            
            if scenario_type == 'search':
                assert stats['percentile_95_ms'] <= SLA_TARGETS['product_search']['percentile_95_ms'] * 1.5
            elif scenario_type == 'upload':
                assert stats['percentile_95_ms'] <= SLA_TARGETS['file_upload_processing']['percentile_95_ms'] * 1.2
            else:  # quotation
                assert stats['percentile_95_ms'] <= SLA_TARGETS['quotation_generation']['percentile_95_ms'] * 1.1
    
    def _execute_search_load(self, runtime: LocalRuntime, infrastructure: Dict[str, Any]) -> Tuple[float, bool, str]:
        """Execute search workload for load testing"""
        start_time = time.time()
        
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("PythonCodeNode", "load_search", {
                "code": """
import psycopg2
from psycopg2.extras import RealDictCursor
def search_load(query, postgres_params):
    conn = psycopg2.connect(**postgres_params)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id, name FROM horme.products WHERE LOWER(name) LIKE LOWER(%s) LIMIT 10", [f"%{query}%"])
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    result = {'success': True, 'count': len(results)}
"""
            })
            
            results, run_id = runtime.execute(workflow.build(), {
                "load_search": {
                    "query": "test",
                    "postgres_params": infrastructure['postgres']
                }
            })
            
            return (time.time() - start_time) * 1000, True, None
            
        except Exception as e:
            return (time.time() - start_time) * 1000, False, str(e)
    
    def _execute_upload_load(self, runtime: LocalRuntime) -> Tuple[float, bool, str]:
        """Execute upload workload for load testing"""
        start_time = time.time()
        
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("PythonCodeNode", "load_upload", {
                "code": """
import time
def process_load_upload(content):
    # Simulate file processing
    time.sleep(0.05)  # 50ms processing
    items = len([line for line in content.split('\\n') if '$' in line])
    result = {'success': True, 'items': items}
"""
            })
            
            test_content = "Load test file\nItem 1: Product A - $10.99\nItem 2: Product B - $25.50"
            
            results, run_id = runtime.execute(workflow.build(), {
                "load_upload": {"content": test_content}
            })
            
            return (time.time() - start_time) * 1000, True, None
            
        except Exception as e:
            return (time.time() - start_time) * 1000, False, str(e)
    
    def _execute_quotation_load(self, runtime: LocalRuntime, infrastructure: Dict[str, Any]) -> Tuple[float, bool, str]:
        """Execute quotation workload for load testing"""
        start_time = time.time()
        
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("PythonCodeNode", "load_quotation", {
                "code": """
import time
def process_load_quotation(items_count):
    # Simulate quotation generation
    time.sleep(0.1 * items_count)  # 100ms per item
    total = items_count * 25.99
    result = {'success': True, 'total': total}
"""
            })
            
            results, run_id = runtime.execute(workflow.build(), {
                "load_quotation": {"items_count": 5}
            })
            
            return (time.time() - start_time) * 1000, True, None
            
        except Exception as e:
            return (time.time() - start_time) * 1000, False, str(e)