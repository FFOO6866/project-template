#!/usr/bin/env python3
"""
TIER 2 - INTEGRATION TESTING (<5 seconds)
Tests quotation system integration with real Docker services.
NO MOCKING - tests actual database connections, API calls, file operations.
"""

import pytest
import psycopg2
import redis
import sqlite3
import json
import time
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from src.workflows.quotation_generation import QuotationGenerationWorkflow

class TestQuotationIntegration:
    """Test quotation system integration with real infrastructure."""
    
    @pytest.fixture(scope="class")
    def docker_config(self):
        """Get Docker configuration from environment."""
        return {
            'postgres_host': os.getenv('DB_HOST', 'localhost'),
            'postgres_port': int(os.getenv('DB_PORT', '6660')),
            'postgres_db': os.getenv('DB_NAME', 'horme-pov_test'),
            'postgres_user': os.getenv('DB_USER', 'test_user'),
            'postgres_password': os.getenv('DB_PASSWORD', 'test_password'),
            'redis_host': os.getenv('REDIS_HOST', 'localhost'),
            'redis_port': int(os.getenv('REDIS_PORT', '6661')),
        }
    
    @pytest.fixture
    def postgres_connection(self, docker_config):
        """Create real PostgreSQL connection."""
        conn = psycopg2.connect(
            host=docker_config['postgres_host'],
            port=docker_config['postgres_port'],
            database=docker_config['postgres_db'],
            user=docker_config['postgres_user'],
            password=docker_config['postgres_password']
        )
        yield conn
        conn.close()
    
    @pytest.fixture
    def redis_connection(self, docker_config):
        """Create real Redis connection."""
        client = redis.Redis(
            host=docker_config['redis_host'],
            port=docker_config['redis_port'],
            decode_responses=True
        )
        yield client
        client.flushdb()  # Clean up after test
    
    @pytest.fixture
    def quotation_workflow(self):
        """Create quotation workflow instance."""
        return QuotationGenerationWorkflow()
    
    @pytest.fixture
    def sample_enterprise_data(self):
        """Enterprise-grade sample data for integration testing."""
        return {
            'requirements': [
                {
                    'category': 'Industrial Equipment',
                    'description': 'Caterpillar 320 Excavator with GPS tracking',
                    'quantity': 5,
                    'keywords': ['caterpillar', '320', 'excavator', 'gps', 'tracking'],
                    'brand': 'Caterpillar',
                    'model': '320',
                    'specifications': {
                        'engine_power': '122 HP',
                        'operating_weight': '20,300 kg',
                        'bucket_capacity': '0.8-1.3 m³'
                    }
                },
                {
                    'category': 'Safety Systems',
                    'description': 'Honeywell Multi-Gas Detector with Wireless',
                    'quantity': 25,
                    'keywords': ['honeywell', 'multi-gas', 'detector', 'wireless'],
                    'brand': 'Honeywell',
                    'model': 'GasAlert Quattro',
                    'specifications': {
                        'detection_gases': 'H2S, CO, O2, LEL',
                        'battery_life': '14 hours',
                        'wireless_range': '100m'
                    }
                }
            ],
            'pricing_results': {
                'pricing_results': {
                    'Industrial Equipment_CAT320': {
                        'product_id': 'CAT-320-GPS',
                        'product_name': 'Caterpillar 320 Excavator with GPS Package',
                        'category': 'Industrial Equipment',
                        'brand': 'Caterpillar',
                        'model': '320',
                        'quantity': 5,
                        'final_unit_price': 285000.00,
                        'total_price': 1425000.00,
                        'savings_breakdown': {
                            'volume_discount': 142500.00,
                            'enterprise_discount': 71250.00,
                            'total_savings': 213750.00
                        },
                        'supplier_info': {
                            'name': 'Heavy Equipment Solutions',
                            'delivery_time': '6-8 weeks',
                            'warranty': '2 years full coverage'
                        }
                    },
                    'Safety Systems_HW-GQ': {
                        'product_id': 'HW-GASALERT-QUATTRO',
                        'product_name': 'Honeywell GasAlert Quattro Multi-Gas Detector',
                        'category': 'Safety Systems',
                        'brand': 'Honeywell',
                        'model': 'GasAlert Quattro',
                        'quantity': 25,
                        'final_unit_price': 1250.00,
                        'total_price': 31250.00,
                        'savings_breakdown': {
                            'bulk_discount': 2500.00,
                            'safety_program_discount': 1875.00,
                            'total_savings': 4375.00
                        },
                        'supplier_info': {
                            'name': 'Industrial Safety Supply',
                            'delivery_time': '2-3 weeks',
                            'warranty': '3 years manufacturer'
                        }
                    }
                }
            },
            'customer_info': {
                'name': 'Global Construction Corp',
                'tier': 'enterprise',
                'contact_email': 'procurement@globalconstruction.com',
                'billing_address': '500 Industrial Blvd, Houston, TX 77001',
                'tax_exempt': False,
                'payment_terms': 'Net 45 days'
            }
        }
    
    @pytest.mark.timeout(5)
    def test_postgresql_quotation_storage(self, postgres_connection, quotation_workflow, sample_enterprise_data):
        """Test real PostgreSQL database integration for quotation storage."""
        start_time = time.time()
        
        # Create quotation tables in PostgreSQL
        cursor = postgres_connection.cursor()
        
        # Drop tables if they exist (for clean testing)
        cursor.execute("DROP TABLE IF EXISTS quotation_items CASCADE")
        cursor.execute("DROP TABLE IF EXISTS quotations CASCADE")
        
        # Create quotations table
        cursor.execute("""
            CREATE TABLE quotations (
                id SERIAL PRIMARY KEY,
                quote_number VARCHAR(50) UNIQUE NOT NULL,
                customer_name VARCHAR(255) NOT NULL,
                customer_tier VARCHAR(50) DEFAULT 'standard',
                quote_date DATE NOT NULL,
                valid_until DATE,
                status VARCHAR(50) DEFAULT 'draft',
                subtotal DECIMAL(15,2) NOT NULL,
                tax_amount DECIMAL(15,2) NOT NULL,
                total_amount DECIMAL(15,2) NOT NULL,
                total_items INTEGER DEFAULT 0,
                total_savings DECIMAL(15,2) DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                quotation_data JSONB,
                version VARCHAR(10) DEFAULT '1.0'
            )
        """)
        
        # Create quotation_items table
        cursor.execute("""
            CREATE TABLE quotation_items (
                id SERIAL PRIMARY KEY,
                quotation_id INTEGER NOT NULL REFERENCES quotations(id),
                line_number INTEGER NOT NULL,
                product_id VARCHAR(100),
                product_name VARCHAR(500) NOT NULL,
                brand VARCHAR(100),
                model VARCHAR(100),
                category VARCHAR(100),
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(15,2) NOT NULL,
                line_total DECIMAL(15,2) NOT NULL,
                savings DECIMAL(15,2) DEFAULT 0.0
            )
        """)
        
        postgres_connection.commit()
        
        # Execute quotation workflow
        workflow = quotation_workflow.create_complete_quotation_workflow()
        runtime = LocalRuntime()
        
        params = {
            'requirements': sample_enterprise_data['requirements'],
            'pricing_results': sample_enterprise_data['pricing_results'],
            'customer_name': sample_enterprise_data['customer_info']['name'],
            'customer_tier': sample_enterprise_data['customer_info']['tier']
        }
        
        results, run_id = runtime.execute(workflow, parameters=params)
        
        # Store quotation in PostgreSQL (real database operation)
        quotation = results.get('quotation', {})
        financial = quotation['financial_summary']
        
        cursor.execute("""
            INSERT INTO quotations 
            (quote_number, customer_name, customer_tier, quote_date, valid_until, 
             status, subtotal, tax_amount, total_amount, total_items, total_savings,
             quotation_data, version)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            quotation['quote_number'],
            quotation['customer_info']['name'],
            quotation['customer_info']['tier'],
            quotation['quote_date'],
            quotation['valid_until'],
            quotation['status'],
            financial['subtotal'],
            financial['tax_amount'],
            financial['total_amount'],
            financial['total_items'],
            financial['total_savings'],
            json.dumps(quotation),
            quotation['version']
        ))
        
        quotation_id = cursor.fetchone()[0]
        
        # Insert line items
        for item in quotation['line_items']:
            cursor.execute("""
                INSERT INTO quotation_items 
                (quotation_id, line_number, product_id, product_name, brand, model,
                 category, quantity, unit_price, line_total, savings)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                quotation_id, item['line_number'], item['product_id'],
                item['product_name'], item.get('brand', ''), item.get('model', ''),
                item.get('category', ''), item['quantity'], item['unit_price'],
                item['line_total'], item.get('savings', 0.0)
            ))
        
        postgres_connection.commit()
        
        # Verify data integrity with real database queries
        cursor.execute("SELECT COUNT(*) FROM quotations WHERE quote_number = %s", (quotation['quote_number'],))
        quotation_count = cursor.fetchone()[0]
        assert quotation_count == 1, "Should have exactly one quotation record"
        
        cursor.execute("SELECT COUNT(*) FROM quotation_items WHERE quotation_id = %s", (quotation_id,))
        item_count = cursor.fetchone()[0]
        assert item_count == 2, "Should have exactly two line items"
        
        # Test complex query performance
        cursor.execute("""
            SELECT q.quote_number, q.total_amount, COUNT(qi.id) as item_count,
                   SUM(qi.line_total) as calculated_subtotal
            FROM quotations q
            LEFT JOIN quotation_items qi ON q.id = qi.quotation_id
            WHERE q.quote_number = %s
            GROUP BY q.id, q.quote_number, q.total_amount
        """, (quotation['quote_number'],))
        
        query_result = cursor.fetchone()
        assert query_result is not None, "Complex query should return result"
        assert query_result[2] == 2, "Query should count correct number of items"
        
        execution_time = time.time() - start_time
        assert execution_time < 5.0, f"Integration test took too long: {execution_time:.3f}s"
        
        # Test financial accuracy in database
        expected_total = 1425000.00 + 31250.00  # Enterprise equipment total
        stored_subtotal = float(query_result[3])
        assert abs(stored_subtotal - expected_total) < 0.01, f"Database subtotal mismatch: expected {expected_total}, got {stored_subtotal}"
        
        print(f"✓ PostgreSQL integration: Stored {quotation['quote_number']} with {item_count} items in {execution_time:.3f}s")
        
        return {
            'test_type': 'postgresql_integration',
            'quotation_id': quotation_id,
            'execution_time': execution_time,
            'records_created': quotation_count + item_count
        }
    
    @pytest.mark.timeout(5)
    def test_redis_caching_integration(self, redis_connection, quotation_workflow, sample_enterprise_data):
        """Test real Redis caching integration for quotation workflow."""
        start_time = time.time()
        
        # Generate quotation
        workflow = quotation_workflow.create_complete_quotation_workflow()
        runtime = LocalRuntime()
        
        params = {
            'requirements': sample_enterprise_data['requirements'],
            'pricing_results': sample_enterprise_data['pricing_results'],
            'customer_name': sample_enterprise_data['customer_info']['name'],
            'customer_tier': sample_enterprise_data['customer_info']['tier']
        }
        
        results, run_id = runtime.execute(workflow, parameters=params)
        quotation = results.get('quotation', {})
        
        # Cache quotation data in Redis (real cache operation)
        cache_key = f"quotation:{quotation['quote_number']}"
        redis_connection.setex(cache_key, 3600, json.dumps(quotation))  # Cache for 1 hour
        
        # Cache quotation metadata
        metadata_key = f"quotation:metadata:{quotation['quote_number']}"
        metadata = {
            'customer': quotation['customer_info']['name'],
            'total_amount': quotation['financial_summary']['total_amount'],
            'item_count': quotation['financial_summary']['total_items'],
            'created_at': quotation['created_at'],
            'status': quotation['status']
        }
        redis_connection.setex(metadata_key, 3600, json.dumps(metadata))
        
        # Cache pricing breakdown for analytics
        pricing_key = f"pricing:breakdown:{quotation['quote_number']}"
        pricing_breakdown = {}
        for item in quotation['line_items']:
            pricing_breakdown[item['product_id']] = {
                'unit_price': item['unit_price'],
                'quantity': item['quantity'],
                'total': item['line_total'],
                'savings': item.get('savings', 0.0)
            }
        redis_connection.setex(pricing_key, 1800, json.dumps(pricing_breakdown))  # 30 minute cache
        
        # Test cache retrieval and data integrity
        cached_quotation = json.loads(redis_connection.get(cache_key))
        assert cached_quotation['quote_number'] == quotation['quote_number'], "Cached quotation should match original"
        assert cached_quotation['financial_summary']['total_amount'] == quotation['financial_summary']['total_amount'], "Cached financial data should match"
        
        cached_metadata = json.loads(redis_connection.get(metadata_key))
        assert cached_metadata['customer'] == quotation['customer_info']['name'], "Cached metadata should match"
        assert cached_metadata['item_count'] == 2, "Should cache correct item count"
        
        cached_pricing = json.loads(redis_connection.get(pricing_key))
        assert len(cached_pricing) == 2, "Should cache pricing for all items"
        
        # Test cache performance with multiple operations
        performance_start = time.time()
        for i in range(100):
            test_key = f"performance:test:{i}"
            redis_connection.set(test_key, f"value_{i}")
            retrieved_value = redis_connection.get(test_key)
            assert retrieved_value == f"value_{i}", f"Cache operation {i} failed"
        
        cache_performance_time = time.time() - performance_start
        assert cache_performance_time < 2.0, f"Cache performance test took too long: {cache_performance_time:.3f}s"
        
        # Test cache expiration and TTL
        ttl = redis_connection.ttl(cache_key)
        assert ttl > 0, "Cache should have valid TTL"
        assert ttl <= 3600, "TTL should not exceed set value"
        
        # Test cache analytics queries
        cache_keys = redis_connection.keys("quotation:*")
        assert len(cache_keys) >= 2, "Should have cached quotation and metadata"
        
        pricing_keys = redis_connection.keys("pricing:*")
        assert len(pricing_keys) >= 1, "Should have cached pricing breakdown"
        
        execution_time = time.time() - start_time
        assert execution_time < 5.0, f"Integration test took too long: {execution_time:.3f}s"
        
        print(f"✓ Redis caching: Cached {quotation['quote_number']} with {len(cache_keys) + len(pricing_keys)} keys in {execution_time:.3f}s")
        
        return {
            'test_type': 'redis_caching',
            'cache_keys_created': len(cache_keys) + len(pricing_keys),
            'execution_time': execution_time,
            'cache_performance_time': cache_performance_time
        }
    
    @pytest.mark.timeout(5)
    def test_file_storage_integration(self, quotation_workflow, sample_enterprise_data):
        """Test real file storage operations for quotation documents."""
        start_time = time.time()
        
        # Create temporary directory for file operations (real file system)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Generate quotation
            workflow = quotation_workflow.create_complete_quotation_workflow()
            runtime = LocalRuntime()
            
            params = {
                'requirements': sample_enterprise_data['requirements'],
                'pricing_results': sample_enterprise_data['pricing_results'],
                'customer_name': sample_enterprise_data['customer_info']['name'],
                'customer_tier': sample_enterprise_data['customer_info']['tier']
            }
            
            results, run_id = runtime.execute(workflow, parameters=params)
            quotation = results.get('quotation', {})
            html_content = results.get('html_content', '')
            
            # Save quotation data as JSON (real file operation)
            quotation_file = temp_path / f"{quotation['quote_number']}_data.json"
            with open(quotation_file, 'w', encoding='utf-8') as f:
                json.dump(quotation, f, indent=2, default=str)
            
            # Save HTML quotation (real file operation)
            html_file = temp_path / f"{quotation['quote_number']}_quotation.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Create quotation summary CSV (real file operation)
            csv_file = temp_path / f"{quotation['quote_number']}_summary.csv"
            with open(csv_file, 'w', encoding='utf-8') as f:
                f.write("Line,Product ID,Product Name,Quantity,Unit Price,Total,Savings\n")
                for item in quotation['line_items']:
                    f.write(f"{item['line_number']},{item['product_id']},\"{item['product_name']}\","
                           f"{item['quantity']},{item['unit_price']},{item['line_total']},{item.get('savings', 0.0)}\n")
            
            # Create audit log (real file operation)
            audit_file = temp_path / f"{quotation['quote_number']}_audit.log"
            with open(audit_file, 'w', encoding='utf-8') as f:
                f.write(f"Quotation Generated: {datetime.now().isoformat()}\n")
                f.write(f"Quote Number: {quotation['quote_number']}\n")
                f.write(f"Customer: {quotation['customer_info']['name']}\n")
                f.write(f"Total Amount: ${quotation['financial_summary']['total_amount']:,.2f}\n")
                f.write(f"Items: {quotation['financial_summary']['total_items']}\n")
                f.write(f"Run ID: {run_id}\n")
            
            # Verify file integrity and content
            assert quotation_file.exists(), "Quotation JSON file should be created"
            assert html_file.exists(), "HTML quotation file should be created"
            assert csv_file.exists(), "CSV summary file should be created"
            assert audit_file.exists(), "Audit log file should be created"
            
            # Test file sizes and content
            json_size = quotation_file.stat().st_size
            html_size = html_file.stat().st_size
            csv_size = csv_file.stat().st_size
            audit_size = audit_file.stat().st_size
            
            assert json_size > 1000, f"JSON file too small: {json_size} bytes"
            assert html_size > 5000, f"HTML file too small: {html_size} bytes"
            assert csv_size > 100, f"CSV file too small: {csv_size} bytes"
            assert audit_size > 50, f"Audit file too small: {audit_size} bytes"
            
            # Verify JSON data integrity by reloading
            with open(quotation_file, 'r', encoding='utf-8') as f:
                reloaded_quotation = json.load(f)
            
            assert reloaded_quotation['quote_number'] == quotation['quote_number'], "Reloaded quotation should match"
            assert reloaded_quotation['financial_summary']['total_amount'] == quotation['financial_summary']['total_amount'], "Financial data should persist"
            
            # Test CSV parsing
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_lines = f.readlines()
            
            assert len(csv_lines) == 3, "CSV should have header + 2 data lines"  # Header + 2 items
            assert "Product ID" in csv_lines[0], "CSV should have proper header"
            
            # Test concurrent file operations
            concurrent_files = []
            for i in range(10):
                concurrent_file = temp_path / f"concurrent_{i}.txt"
                with open(concurrent_file, 'w') as f:
                    f.write(f"Concurrent operation {i}\n")
                concurrent_files.append(concurrent_file)
            
            # Verify all concurrent files exist
            for concurrent_file in concurrent_files:
                assert concurrent_file.exists(), f"Concurrent file should exist: {concurrent_file}"
            
            execution_time = time.time() - start_time
            assert execution_time < 5.0, f"Integration test took too long: {execution_time:.3f}s"
            
            total_files = 4 + len(concurrent_files)  # Main files + concurrent files
            total_size = json_size + html_size + csv_size + audit_size
            
            print(f"✓ File storage: Created {total_files} files ({total_size:,} bytes) in {execution_time:.3f}s")
            
            return {
                'test_type': 'file_storage',
                'files_created': total_files,
                'total_size_bytes': total_size,
                'execution_time': execution_time
            }
    
    @pytest.mark.timeout(5)
    def test_api_endpoint_integration(self, quotation_workflow, sample_enterprise_data):
        """Test API endpoint integration for quotation services."""
        start_time = time.time()
        
        # Simulate API endpoint workflow
        workflow = quotation_workflow.create_complete_quotation_workflow()
        runtime = LocalRuntime()
        
        # Test multiple customer scenarios (API-style)
        api_scenarios = [
            {
                'customer': 'Manufacturing Corp',
                'tier': 'enterprise',
                'expected_discount': True
            },
            {
                'customer': 'Small Business Inc',
                'tier': 'standard',
                'expected_discount': False
            },
            {
                'customer': 'Government Agency',
                'tier': 'government',
                'expected_discount': True
            }
        ]
        
        api_results = []
        
        for scenario in api_scenarios:
            scenario_start = time.time()
            
            params = {
                'requirements': sample_enterprise_data['requirements'],
                'pricing_results': sample_enterprise_data['pricing_results'],
                'customer_name': scenario['customer'],
                'customer_tier': scenario['tier']
            }
            
            results, run_id = runtime.execute(workflow, parameters=params)
            scenario_time = time.time() - scenario_start
            
            # Validate API response structure
            assert 'quotation' in results, "API should return quotation"
            assert 'html_content' in results, "API should return HTML content"
            assert 'success' in results, "API should return success status"
            
            quotation = results['quotation']
            
            # Validate API response data
            assert quotation['customer_info']['name'] == scenario['customer'], "Customer name should match request"
            assert quotation['customer_info']['tier'] == scenario['tier'], "Customer tier should match request"
            assert quotation['quote_number'].startswith('Q'), "Quote number should have correct format"
            
            # Test tier-specific business logic
            financial = quotation['financial_summary']
            if scenario['tier'] == 'enterprise':
                assert financial['total_savings'] > 0, "Enterprise tier should have savings"
            
            api_results.append({
                'customer': scenario['customer'],
                'tier': scenario['tier'],
                'quote_number': quotation['quote_number'],
                'total_amount': financial['total_amount'],
                'processing_time': scenario_time,
                'success': results.get('success', False)
            })
            
            # API performance requirement
            assert scenario_time < 2.0, f"API response too slow for {scenario['customer']}: {scenario_time:.3f}s"
        
        # Test API batch processing
        batch_start = time.time()
        batch_params = {
            'requirements': sample_enterprise_data['requirements'] * 3,  # Simulate larger batch
            'pricing_results': sample_enterprise_data['pricing_results'],
            'customer_name': 'Batch Processing Test',
            'customer_tier': 'enterprise'
        }
        
        batch_results, batch_run_id = runtime.execute(workflow, parameters=batch_params)
        batch_time = time.time() - batch_start
        
        assert batch_results.get('success', False), "Batch processing should succeed"
        batch_quotation = batch_results['quotation']
        assert batch_quotation['financial_summary']['total_items'] == 6, "Batch should process all items"
        assert batch_time < 3.0, f"Batch processing too slow: {batch_time:.3f}s"
        
        # Test API error handling
        error_params = {
            'requirements': [],  # Empty requirements should be handled gracefully
            'pricing_results': {},
            'customer_name': 'Error Test Customer',
            'customer_tier': 'standard'
        }
        
        error_results, error_run_id = runtime.execute(workflow, parameters=error_params)
        # Should handle gracefully without crashing
        
        execution_time = time.time() - start_time
        assert execution_time < 5.0, f"Integration test took too long: {execution_time:.3f}s"
        
        # Calculate API performance metrics
        avg_api_time = sum(r['processing_time'] for r in api_results) / len(api_results)
        max_api_time = max(r['processing_time'] for r in api_results)
        success_rate = sum(1 for r in api_results if r['success']) / len(api_results) * 100
        
        assert avg_api_time < 1.5, f"Average API response time too slow: {avg_api_time:.3f}s"
        assert success_rate == 100.0, f"API success rate below 100%: {success_rate:.1f}%"
        
        print(f"✓ API integration: Processed {len(api_results)} scenarios + batch in {execution_time:.3f}s")
        
        return {
            'test_type': 'api_integration',
            'scenarios_processed': len(api_results),
            'avg_response_time': avg_api_time,
            'max_response_time': max_api_time,
            'success_rate': success_rate,
            'batch_processing_time': batch_time,
            'execution_time': execution_time
        }
    
    @pytest.mark.timeout(5)
    def test_service_communication_validation(self, postgres_connection, redis_connection, quotation_workflow, sample_enterprise_data):
        """Test communication between services with real infrastructure."""
        start_time = time.time()
        
        # Test workflow: Generate -> Cache -> Store -> Retrieve
        workflow = quotation_workflow.create_complete_quotation_workflow()
        runtime = LocalRuntime()
        
        params = {
            'requirements': sample_enterprise_data['requirements'],
            'pricing_results': sample_enterprise_data['pricing_results'],
            'customer_name': 'Service Communication Test Corp',
            'customer_tier': 'enterprise'
        }
        
        # Step 1: Generate quotation
        results, run_id = runtime.execute(workflow, parameters=params)
        quotation = results.get('quotation', {})
        assert quotation, "Quotation generation should succeed"
        
        # Step 2: Cache in Redis (real cache operation)
        cache_key = f"service_test:{quotation['quote_number']}"
        redis_connection.setex(cache_key, 600, json.dumps(quotation))
        
        # Step 3: Store in PostgreSQL (real database operation)
        cursor = postgres_connection.cursor()
        
        # Ensure tables exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_test_quotations (
                id SERIAL PRIMARY KEY,
                quote_number VARCHAR(50) UNIQUE NOT NULL,
                customer_name VARCHAR(255) NOT NULL,
                total_amount DECIMAL(15,2) NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                quotation_data JSONB
            )
        """)
        
        cursor.execute("""
            INSERT INTO service_test_quotations 
            (quote_number, customer_name, total_amount, quotation_data)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            quotation['quote_number'],
            quotation['customer_info']['name'],
            quotation['financial_summary']['total_amount'],
            json.dumps(quotation)
        ))
        
        service_id = cursor.fetchone()[0]
        postgres_connection.commit()
        
        # Step 4: Cross-service validation
        # Retrieve from cache
        cached_data = json.loads(redis_connection.get(cache_key))
        
        # Retrieve from database
        cursor.execute("""
            SELECT quote_number, customer_name, total_amount, quotation_data
            FROM service_test_quotations 
            WHERE id = %s
        """, (service_id,))
        
        db_result = cursor.fetchone()
        db_quotation = json.loads(db_result[3])
        
        # Cross-validate data consistency
        assert cached_data['quote_number'] == db_quotation['quote_number'], "Cache and DB quote numbers should match"
        assert cached_data['financial_summary']['total_amount'] == db_quotation['financial_summary']['total_amount'], "Financial totals should match across services"
        assert cached_data['customer_info']['name'] == db_quotation['customer_info']['name'], "Customer names should match across services"
        
        # Test service resilience with cache miss
        redis_connection.delete(cache_key)
        assert redis_connection.get(cache_key) is None, "Cache should be cleared"
        
        # Should be able to reconstruct from database
        cursor.execute("SELECT quotation_data FROM service_test_quotations WHERE id = %s", (service_id,))
        fallback_data = json.loads(cursor.fetchone()[0])
        assert fallback_data['quote_number'] == quotation['quote_number'], "Should fallback to database data"
        
        # Test concurrent service operations
        concurrent_operations = []
        for i in range(5):
            concurrent_key = f"concurrent:{quotation['quote_number']}:{i}"
            redis_connection.set(concurrent_key, f"operation_{i}")
            concurrent_operations.append(concurrent_key)
        
        # Verify all concurrent operations
        for key in concurrent_operations:
            assert redis_connection.get(key) is not None, f"Concurrent operation should be cached: {key}"
        
        execution_time = time.time() - start_time
        assert execution_time < 5.0, f"Integration test took too long: {execution_time:.3f}s"
        
        print(f"✓ Service communication: Validated cache-database consistency in {execution_time:.3f}s")
        
        return {
            'test_type': 'service_communication',
            'quotation_id': quotation['quote_number'],
            'services_tested': ['quotation_generation', 'redis_cache', 'postgresql_storage'],
            'concurrent_operations': len(concurrent_operations),
            'execution_time': execution_time
        }

if __name__ == "__main__":
    # Run specific test for development
    import os
    os.environ.setdefault('DB_HOST', 'localhost')
    os.environ.setdefault('DB_PORT', '6660')
    os.environ.setdefault('REDIS_HOST', 'localhost')
    os.environ.setdefault('REDIS_PORT', '6661')
    
    test_class = TestQuotationIntegration()
    docker_config = test_class.docker_config()
    print(f"Testing with Docker config: {docker_config}")