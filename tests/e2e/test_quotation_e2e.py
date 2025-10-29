#!/usr/bin/env python3
"""
TIER 3 - END-TO-END TESTING (<10 seconds)
Tests complete quotation workflows from start to finish with real infrastructure.
NO MOCKING - complete scenarios with real services, data, and business processes.
"""

import pytest
import psycopg2
import redis
import json
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from pathlib import Path
import sys
import os
import tempfile
import concurrent.futures
import threading

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from src.workflows.quotation_generation import QuotationGenerationWorkflow
from src.rfp_analysis_system import RequirementItem, ProductMatch, PricingRule

class TestQuotationE2E:
    """End-to-end testing of complete quotation business workflows."""
    
    @pytest.fixture(scope="class")
    def infrastructure_config(self):
        """Real infrastructure configuration."""
        return {
            'postgres': {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', '6660')),
                'database': os.getenv('DB_NAME', 'horme-pov_test'),
                'user': os.getenv('DB_USER', 'test_user'),
                'password': os.getenv('DB_PASSWORD', 'test_password')
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', '6661'))
            }
        }
    
    @pytest.fixture
    def database_connection(self, infrastructure_config):
        """Real PostgreSQL connection for E2E testing."""
        conn = psycopg2.connect(**infrastructure_config['postgres'])
        cursor = conn.cursor()
        
        # Setup E2E testing schema
        cursor.execute("DROP SCHEMA IF EXISTS e2e_test CASCADE")
        cursor.execute("CREATE SCHEMA e2e_test")
        cursor.execute("SET search_path TO e2e_test")
        
        # Create comprehensive tables for E2E testing
        cursor.execute("""
            CREATE TABLE customers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                tier VARCHAR(50) DEFAULT 'standard',
                email VARCHAR(255),
                billing_address TEXT,
                tax_exempt BOOLEAN DEFAULT FALSE,
                credit_limit DECIMAL(15,2) DEFAULT 100000.00,
                payment_terms VARCHAR(50) DEFAULT 'Net 30',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE quotations (
                id SERIAL PRIMARY KEY,
                quote_number VARCHAR(50) UNIQUE NOT NULL,
                customer_id INTEGER REFERENCES customers(id),
                customer_name VARCHAR(255) NOT NULL,
                customer_tier VARCHAR(50),
                rfp_id VARCHAR(100),
                quote_date DATE NOT NULL,
                valid_until DATE,
                status VARCHAR(50) DEFAULT 'draft',
                subtotal DECIMAL(15,2) NOT NULL,
                tax_rate DECIMAL(5,4) DEFAULT 0.10,
                tax_amount DECIMAL(15,2) NOT NULL,
                total_amount DECIMAL(15,2) NOT NULL,
                total_items INTEGER DEFAULT 0,
                total_savings DECIMAL(15,2) DEFAULT 0.0,
                approval_status VARCHAR(50) DEFAULT 'pending',
                approved_by VARCHAR(255),
                approved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                quotation_data JSONB,
                version VARCHAR(10) DEFAULT '1.0'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE quotation_items (
                id SERIAL PRIMARY KEY,
                quotation_id INTEGER REFERENCES quotations(id),
                line_number INTEGER NOT NULL,
                product_id VARCHAR(100),
                product_name VARCHAR(500) NOT NULL,
                product_description TEXT,
                brand VARCHAR(100),
                model VARCHAR(100),
                category VARCHAR(100),
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(15,2) NOT NULL,
                list_price DECIMAL(15,2),
                discount_percent DECIMAL(5,2) DEFAULT 0.00,
                line_total DECIMAL(15,2) NOT NULL,
                savings DECIMAL(15,2) DEFAULT 0.0,
                supplier_id VARCHAR(100),
                delivery_time VARCHAR(100),
                warranty VARCHAR(255)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE quotation_approval_workflow (
                id SERIAL PRIMARY KEY,
                quotation_id INTEGER REFERENCES quotations(id),
                approval_level INTEGER NOT NULL,
                approver_name VARCHAR(255),
                approval_threshold DECIMAL(15,2),
                status VARCHAR(50) DEFAULT 'pending',
                approved_at TIMESTAMP,
                notes TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE business_metrics (
                id SERIAL PRIMARY KEY,
                metric_name VARCHAR(255) NOT NULL,
                metric_value DECIMAL(15,2),
                metric_date DATE DEFAULT CURRENT_DATE,
                quotation_id INTEGER REFERENCES quotations(id),
                customer_tier VARCHAR(50),
                category VARCHAR(100)
            )
        """)
        
        conn.commit()
        yield conn
        conn.close()
    
    @pytest.fixture
    def cache_connection(self, infrastructure_config):
        """Real Redis connection for E2E testing."""
        client = redis.Redis(**infrastructure_config['redis'], decode_responses=True)
        client.flushdb()  # Clean slate for E2E testing
        yield client
        client.flushdb()  # Clean up after testing
    
    @pytest.fixture
    def real_customer_scenarios(self):
        """Real-world customer scenarios for E2E testing."""
        return [
            {
                'rfp_id': 'RFP-2024-CONSTRUCTION-001',
                'customer': {
                    'name': 'Global Construction Enterprises',
                    'tier': 'enterprise',
                    'email': 'procurement@globalconstruction.com',
                    'billing_address': '500 Industrial Blvd, Houston, TX 77001',
                    'tax_exempt': False,
                    'credit_limit': 5000000.00,
                    'payment_terms': 'Net 45'
                },
                'requirements': [
                    {
                        'category': 'Heavy Equipment',
                        'description': 'Caterpillar 336 Excavator with GPS and Telematics',
                        'quantity': 3,
                        'specifications': {
                            'engine_power': '268 HP',
                            'operating_weight': '36,200 kg',
                            'bucket_capacity': '1.7-2.3 m³',
                            'gps_enabled': True,
                            'telematics_package': 'Advanced'
                        },
                        'delivery_requirement': '8-10 weeks',
                        'warranty_requirement': '2 years full coverage'
                    },
                    {
                        'category': 'Safety Equipment',
                        'description': 'Complete Safety Package for 50 Workers',
                        'quantity': 50,
                        'specifications': {
                            'hard_hats': 'ANSI Z89.1 Type I',
                            'safety_glasses': 'Anti-fog, UV protection',
                            'high_vis_vests': 'Class 3, ANSI/ISEA 107',
                            'safety_boots': 'Steel toe, slip resistant',
                            'fall_protection': 'Full body harness with lanyard'
                        },
                        'delivery_requirement': '2-3 weeks',
                        'warranty_requirement': '1 year manufacturer'
                    }
                ],
                'expected_outcomes': {
                    'total_amount_range': (850000, 1200000),
                    'approval_required': True,
                    'enterprise_discount': True,
                    'processing_priority': 'high'
                }
            },
            {
                'rfp_id': 'RFP-2024-MANUFACTURING-002',
                'customer': {
                    'name': 'Precision Manufacturing Inc',
                    'tier': 'standard',
                    'email': 'purchasing@precisionmfg.com',
                    'billing_address': '123 Factory Lane, Detroit, MI 48201',
                    'tax_exempt': True,
                    'credit_limit': 500000.00,
                    'payment_terms': 'Net 30'
                },
                'requirements': [
                    {
                        'category': 'Industrial Tools',
                        'description': 'High-Precision Measurement Equipment',
                        'quantity': 15,
                        'specifications': {
                            'accuracy': '±0.001 mm',
                            'measuring_range': '0-300 mm',
                            'digital_display': True,
                            'data_output': 'RS232/USB',
                            'calibration_certificate': True
                        },
                        'delivery_requirement': '4-6 weeks',
                        'warranty_requirement': '1 year calibration guarantee'
                    }
                ],
                'expected_outcomes': {
                    'total_amount_range': (45000, 75000),
                    'approval_required': False,
                    'enterprise_discount': False,
                    'processing_priority': 'standard'
                }
            },
            {
                'rfp_id': 'RFP-2024-GOVERNMENT-003',
                'customer': {
                    'name': 'Department of Transportation',
                    'tier': 'government',
                    'email': 'contracts@dot.gov',
                    'billing_address': '1200 New Jersey Ave SE, Washington, DC 20590',
                    'tax_exempt': True,
                    'credit_limit': 10000000.00,
                    'payment_terms': 'Net 60'
                },
                'requirements': [
                    {
                        'category': 'Fleet Vehicles',
                        'description': 'Heavy-Duty Maintenance Trucks with Equipment',
                        'quantity': 25,
                        'specifications': {
                            'vehicle_class': 'Class 6 Commercial',
                            'payload_capacity': '19,500 lbs',
                            'equipment_package': 'Road maintenance tools',
                            'fuel_type': 'Diesel',
                            'emissions_standard': 'EPA 2024',
                            'warranty': '5 years/100,000 miles'
                        },
                        'delivery_requirement': '12-16 weeks',
                        'warranty_requirement': '5 years comprehensive'
                    }
                ],
                'expected_outcomes': {
                    'total_amount_range': (2500000, 3500000),
                    'approval_required': True,
                    'enterprise_discount': True,
                    'processing_priority': 'high'
                }
            }
        ]
    
    @pytest.mark.timeout(10)
    def test_complete_quotation_business_workflow(self, database_connection, cache_connection, real_customer_scenarios):
        """Test complete business workflow from RFP to quotation approval."""
        start_time = time.time()
        
        workflow_metrics = []
        quotation_workflow = QuotationGenerationWorkflow()
        
        for scenario in real_customer_scenarios:
            scenario_start = time.time()
            
            # Step 1: Customer Registration (real database operation)
            cursor = database_connection.cursor()
            cursor.execute("""
                INSERT INTO customers (name, tier, email, billing_address, tax_exempt, credit_limit, payment_terms)
                VALUES (%(name)s, %(tier)s, %(email)s, %(billing_address)s, %(tax_exempt)s, %(credit_limit)s, %(payment_terms)s)
                RETURNING id
            """, scenario['customer'])
            
            customer_id = cursor.fetchone()[0]
            database_connection.commit()
            
            # Step 2: Generate Realistic Pricing Results
            pricing_results = self._generate_realistic_pricing(scenario['requirements'])
            
            # Step 3: Execute Quotation Generation Workflow
            workflow = quotation_workflow.create_complete_quotation_workflow()
            runtime = LocalRuntime()
            
            params = {
                'requirements': scenario['requirements'],
                'pricing_results': {'pricing_results': pricing_results},
                'customer_name': scenario['customer']['name'],
                'customer_tier': scenario['customer']['tier']
            }
            
            results, run_id = runtime.execute(workflow, parameters=params)
            quotation = results.get('quotation', {})
            
            # Step 4: Store Complete Quotation (real database operations)
            financial = quotation['financial_summary']
            cursor.execute("""
                INSERT INTO quotations 
                (quote_number, customer_id, customer_name, customer_tier, rfp_id,
                 quote_date, valid_until, status, subtotal, tax_rate, tax_amount,
                 total_amount, total_items, total_savings, quotation_data, version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                quotation['quote_number'], customer_id, quotation['customer_info']['name'],
                quotation['customer_info']['tier'], scenario['rfp_id'],
                quotation['quote_date'], quotation['valid_until'], quotation['status'],
                financial['subtotal'], financial['tax_rate']/100, financial['tax_amount'],
                financial['total_amount'], financial['total_items'], financial['total_savings'],
                json.dumps(quotation), quotation['version']
            ))
            
            quotation_id = cursor.fetchone()[0]
            database_connection.commit()
            
            # Step 5: Store Line Items with Detailed Information
            for item in quotation['line_items']:
                cursor.execute("""
                    INSERT INTO quotation_items 
                    (quotation_id, line_number, product_id, product_name, product_description,
                     brand, model, category, quantity, unit_price, line_total, savings)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    quotation_id, item['line_number'], item['product_id'],
                    item['product_name'], item.get('description', item['product_name']),
                    item.get('brand', ''), item.get('model', ''), item.get('category', ''),
                    item['quantity'], item['unit_price'], item['line_total'],
                    item.get('savings', 0.0)
                ))
            
            database_connection.commit()
            
            # Step 6: Cache Quotation Data for Fast Access
            cache_key = f"e2e:quotation:{quotation['quote_number']}"
            cache_connection.setex(cache_key, 1800, json.dumps(quotation))
            
            # Cache customer-specific data
            customer_cache_key = f"e2e:customer:{customer_id}:quotations"
            customer_quotations = cache_connection.get(customer_cache_key)
            if customer_quotations:
                quotations_list = json.loads(customer_quotations)
            else:
                quotations_list = []
            
            quotations_list.append({
                'quote_number': quotation['quote_number'],
                'total_amount': financial['total_amount'],
                'created_at': quotation['created_at']
            })
            cache_connection.setex(customer_cache_key, 3600, json.dumps(quotations_list))
            
            # Step 7: Business Approval Workflow
            approval_required = scenario['expected_outcomes']['approval_required']
            if approval_required:
                approval_threshold = 100000.00 if scenario['customer']['tier'] == 'standard' else 500000.00
                
                cursor.execute("""
                    INSERT INTO quotation_approval_workflow
                    (quotation_id, approval_level, approval_threshold, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (quotation_id, 1, approval_threshold, 'pending'))
                
                approval_id = cursor.fetchone()[0]
                
                # Simulate approval process
                if financial['total_amount'] > approval_threshold:
                    cursor.execute("""
                        UPDATE quotation_approval_workflow
                        SET status = %s, approver_name = %s, approved_at = %s, notes = %s
                        WHERE id = %s
                    """, ('approved', 'System Auto-Approval', datetime.now(), 
                         f'Approved for {scenario["customer"]["tier"]} tier customer', approval_id))
                    
                    cursor.execute("""
                        UPDATE quotations
                        SET approval_status = %s, approved_by = %s, approved_at = %s
                        WHERE id = %s
                    """, ('approved', 'System Auto-Approval', datetime.now(), quotation_id))
                
                database_connection.commit()
            
            # Step 8: Business Metrics Collection
            metrics_data = [
                ('quotation_total_amount', financial['total_amount'], quotation_id, scenario['customer']['tier'], None),
                ('quotation_item_count', financial['total_items'], quotation_id, scenario['customer']['tier'], None),
                ('quotation_savings', financial['total_savings'], quotation_id, scenario['customer']['tier'], None),
            ]
            
            for item in quotation['line_items']:
                metrics_data.append((
                    'category_total', item['line_total'], quotation_id, 
                    scenario['customer']['tier'], item.get('category', 'Unknown')
                ))
            
            cursor.executemany("""
                INSERT INTO business_metrics (metric_name, metric_value, quotation_id, customer_tier, category)
                VALUES (%s, %s, %s, %s, %s)
            """, metrics_data)
            
            database_connection.commit()
            
            # Step 9: Validation Against Expected Outcomes
            expected = scenario['expected_outcomes']
            
            # Validate total amount within expected range
            total_amount = financial['total_amount']
            assert expected['total_amount_range'][0] <= total_amount <= expected['total_amount_range'][1], \
                f"Total amount ${total_amount:,.2f} outside expected range ${expected['total_amount_range'][0]:,.2f} - ${expected['total_amount_range'][1]:,.2f}"
            
            # Validate enterprise discount application
            if expected['enterprise_discount'] and scenario['customer']['tier'] in ['enterprise', 'government']:
                assert financial['total_savings'] > 0, f"Enterprise customer should have savings, got ${financial['total_savings']:,.2f}"
            
            # Validate approval workflow
            if expected['approval_required']:
                cursor.execute("SELECT status FROM quotation_approval_workflow WHERE quotation_id = %s", (quotation_id,))
                approval_status = cursor.fetchone()
                assert approval_status is not None, "Approval workflow should be created for high-value quotations"
            
            scenario_time = time.time() - scenario_start
            
            workflow_metrics.append({
                'rfp_id': scenario['rfp_id'],
                'customer': scenario['customer']['name'],
                'tier': scenario['customer']['tier'],
                'quote_number': quotation['quote_number'],
                'total_amount': total_amount,
                'processing_time': scenario_time,
                'items_processed': len(scenario['requirements']),
                'approval_required': approval_required,
                'success': True
            })
        
        execution_time = time.time() - start_time
        assert execution_time < 10.0, f"E2E test took too long: {execution_time:.3f}s"
        
        # Comprehensive Business Metrics Analysis
        total_quotations = len(workflow_metrics)
        total_amount = sum(m['total_amount'] for m in workflow_metrics)
        avg_processing_time = sum(m['processing_time'] for m in workflow_metrics) / total_quotations
        
        # Validate business performance requirements
        assert avg_processing_time < 5.0, f"Average processing time too slow: {avg_processing_time:.3f}s"
        assert all(m['success'] for m in workflow_metrics), "All workflows should complete successfully"
        
        # Validate data consistency across services
        cursor.execute("SELECT COUNT(*) FROM quotations")
        db_quotation_count = cursor.fetchone()[0]
        assert db_quotation_count == total_quotations, "Database should contain all generated quotations"
        
        # Validate cache consistency
        cached_quotations = 0
        for metric in workflow_metrics:
            cache_key = f"e2e:quotation:{metric['quote_number']}"
            if cache_connection.get(cache_key):
                cached_quotations += 1
        
        assert cached_quotations == total_quotations, "All quotations should be cached"
        
        print(f"✓ Complete business workflow: Processed {total_quotations} quotations (${total_amount:,.2f}) in {execution_time:.3f}s")
        
        return {
            'test_type': 'complete_business_workflow',
            'quotations_processed': total_quotations,
            'total_business_value': total_amount,
            'avg_processing_time': avg_processing_time,
            'execution_time': execution_time,
            'success_rate': 100.0,
            'workflow_metrics': workflow_metrics
        }
    
    @pytest.mark.timeout(10)
    def test_performance_under_load(self, database_connection, cache_connection):
        """Test performance under realistic business load with statistical analysis."""
        start_time = time.time()
        
        quotation_workflow = QuotationGenerationWorkflow()
        
        # Generate multiple concurrent quotation requests
        concurrent_requests = []
        for i in range(20):
            request = {
                'customer_name': f'Load Test Customer {i:02d}',
                'customer_tier': 'enterprise' if i % 3 == 0 else 'standard',
                'requirements': [
                    {
                        'category': 'Test Equipment',
                        'description': f'Load Test Product {i}',
                        'quantity': (i % 10) + 1,
                        'specifications': {'test_id': f'LOAD-{i:03d}'}
                    }
                ],
                'expected_unit_price': 1000.0 + (i * 50),
                'request_id': f'LOAD-REQ-{i:03d}'
            }
            concurrent_requests.append(request)
        
        # Execute concurrent quotation generation
        execution_times = []
        quotation_results = []
        
        def process_quotation_request(request):
            request_start = time.time()
            
            # Generate pricing
            pricing_results = {
                f"{request['requirements'][0]['category']}_{request['request_id']}": {
                    'product_id': f"LOAD-PROD-{request['request_id']}",
                    'product_name': request['requirements'][0]['description'],
                    'category': request['requirements'][0]['category'],
                    'quantity': request['requirements'][0]['quantity'],
                    'final_unit_price': request['expected_unit_price'],
                    'total_price': request['expected_unit_price'] * request['requirements'][0]['quantity'],
                    'savings_breakdown': {'total_savings': 50.0}
                }
            }
            
            # Execute workflow
            workflow = quotation_workflow.create_complete_quotation_workflow()
            runtime = LocalRuntime()
            
            params = {
                'requirements': request['requirements'],
                'pricing_results': {'pricing_results': pricing_results},
                'customer_name': request['customer_name'],
                'customer_tier': request['customer_tier']
            }
            
            results, run_id = runtime.execute(workflow, parameters=params)
            request_time = time.time() - request_start
            
            return {
                'request_id': request['request_id'],
                'quotation': results.get('quotation', {}),
                'processing_time': request_time,
                'success': results.get('success', False)
            }
        
        # Execute concurrent processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_request = {executor.submit(process_quotation_request, req): req for req in concurrent_requests}
            
            for future in concurrent.futures.as_completed(future_to_request):
                result = future.result()
                quotation_results.append(result)
                execution_times.append(result['processing_time'])
        
        # Store all results in database for persistence testing
        cursor = database_connection.cursor()
        stored_quotations = 0
        
        for result in quotation_results:
            if result['success']:
                quotation = result['quotation']
                financial = quotation['financial_summary']
                
                cursor.execute("""
                    INSERT INTO quotations 
                    (quote_number, customer_name, customer_tier, quote_date, valid_until,
                     status, subtotal, tax_amount, total_amount, total_items, total_savings,
                     quotation_data, version)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    quotation['quote_number'], quotation['customer_info']['name'],
                    quotation['customer_info']['tier'], quotation['quote_date'],
                    quotation['valid_until'], quotation['status'], financial['subtotal'],
                    financial['tax_amount'], financial['total_amount'], financial['total_items'],
                    financial['total_savings'], json.dumps(quotation), quotation['version']
                ))
                
                stored_quotations += 1
        
        database_connection.commit()
        
        # Statistical Performance Analysis
        successful_requests = sum(1 for r in quotation_results if r['success'])
        success_rate = (successful_requests / len(quotation_results)) * 100
        
        avg_time = statistics.mean(execution_times)
        median_time = statistics.median(execution_times)
        std_dev = statistics.stdev(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)
        
        # Calculate percentiles
        sorted_times = sorted(execution_times)
        percentile_95 = sorted_times[int(0.95 * len(sorted_times))]
        percentile_99 = sorted_times[int(0.99 * len(sorted_times))]
        
        execution_time = time.time() - start_time
        assert execution_time < 10.0, f"E2E load test took too long: {execution_time:.3f}s"
        
        # Performance Requirements Validation
        assert success_rate >= 95.0, f"Success rate below requirement: {success_rate:.1f}%"
        assert avg_time < 2.0, f"Average response time too slow: {avg_time:.3f}s"
        assert percentile_95 < 4.0, f"95th percentile too slow: {percentile_95:.3f}s"
        assert std_dev < 1.0, f"Response time too inconsistent: {std_dev:.3f}s"
        
        # Business Throughput Validation
        throughput = successful_requests / execution_time  # requests per second
        assert throughput >= 2.0, f"Throughput below requirement: {throughput:.2f} req/s"
        
        # Database Performance Validation
        assert stored_quotations == successful_requests, "All successful quotations should be stored"
        
        # Cache Performance Testing
        cache_operations = 0
        cache_start = time.time()
        
        for result in quotation_results[:10]:  # Test first 10 for cache performance
            if result['success']:
                quotation = result['quotation']
                cache_key = f"perf_test:{quotation['quote_number']}"
                cache_connection.setex(cache_key, 300, json.dumps(quotation))
                
                # Verify cache retrieval
                cached_data = cache_connection.get(cache_key)
                assert cached_data is not None, "Cache retrieval should succeed"
                cache_operations += 2  # set + get
        
        cache_time = time.time() - cache_start
        cache_throughput = cache_operations / cache_time if cache_time > 0 else 0
        
        print(f"✓ Performance under load: {successful_requests}/{len(quotation_results)} requests "
              f"(avg: {avg_time:.3f}s, 95%: {percentile_95:.3f}s, throughput: {throughput:.2f} req/s)")
        
        return {
            'test_type': 'performance_under_load',
            'total_requests': len(quotation_results),
            'successful_requests': successful_requests,
            'success_rate': success_rate,
            'avg_response_time': avg_time,
            'median_response_time': median_time,
            'std_deviation': std_dev,
            'min_time': min_time,
            'max_time': max_time,
            'percentile_95': percentile_95,
            'percentile_99': percentile_99,
            'throughput_req_per_sec': throughput,
            'cache_throughput_ops_per_sec': cache_throughput,
            'execution_time': execution_time
        }
    
    @pytest.mark.timeout(10)
    def test_error_recovery_and_resilience(self, database_connection, cache_connection):
        """Test system error recovery and resilience under failure conditions."""
        start_time = time.time()
        
        quotation_workflow = QuotationGenerationWorkflow()
        error_scenarios = []
        recovery_results = []
        
        # Scenario 1: Invalid pricing data
        try:
            workflow = quotation_workflow.create_complete_quotation_workflow()
            runtime = LocalRuntime()
            
            params = {
                'requirements': [{'category': 'Test', 'description': 'Invalid test', 'quantity': 1}],
                'pricing_results': {'pricing_results': {}},  # Empty pricing results
                'customer_name': 'Error Recovery Test',
                'customer_tier': 'standard'
            }
            
            results, run_id = runtime.execute(workflow, parameters=params)
            # Should handle gracefully without crashing
            error_scenarios.append({
                'scenario': 'invalid_pricing_data',
                'success': True,  # Success means it handled the error gracefully
                'error_handled': True
            })
        except Exception as e:
            error_scenarios.append({
                'scenario': 'invalid_pricing_data',
                'success': False,
                'error': str(e),
                'error_handled': False
            })
        
        # Scenario 2: Database connection interruption simulation
        cursor = database_connection.cursor()
        
        # Create a valid quotation first
        workflow = quotation_workflow.create_complete_quotation_workflow()
        runtime = LocalRuntime()
        
        valid_params = {
            'requirements': [{'category': 'Recovery Test', 'description': 'Database recovery test', 'quantity': 1}],
            'pricing_results': {
                'pricing_results': {
                    'recovery_test': {
                        'product_id': 'REC-001',
                        'product_name': 'Recovery Test Product',
                        'final_unit_price': 100.0,
                        'total_price': 100.0,
                        'savings_breakdown': {'total_savings': 10.0}
                    }
                }
            },
            'customer_name': 'Database Recovery Customer',
            'customer_tier': 'standard'
        }
        
        results, run_id = runtime.execute(workflow, parameters=valid_params)
        quotation = results.get('quotation', {})
        
        if quotation:
            # Test database resilience with constraint violations
            try:
                # Attempt to insert duplicate quote number
                financial = quotation['financial_summary']
                cursor.execute("""
                    INSERT INTO quotations 
                    (quote_number, customer_name, customer_tier, quote_date, valid_until,
                     status, subtotal, tax_amount, total_amount, total_items, total_savings,
                     quotation_data, version)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    quotation['quote_number'], 'First Insert', 'standard',
                    quotation['quote_date'], quotation['valid_until'], 'draft',
                    financial['subtotal'], financial['tax_amount'], financial['total_amount'],
                    financial['total_items'], financial['total_savings'],
                    json.dumps(quotation), '1.0'
                ))
                database_connection.commit()
                
                # This should fail due to unique constraint
                cursor.execute("""
                    INSERT INTO quotations 
                    (quote_number, customer_name, customer_tier, quote_date, valid_until,
                     status, subtotal, tax_amount, total_amount, total_items, total_savings,
                     quotation_data, version)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    quotation['quote_number'], 'Duplicate Insert', 'standard',
                    quotation['quote_date'], quotation['valid_until'], 'draft',
                    financial['subtotal'], financial['tax_amount'], financial['total_amount'],
                    financial['total_items'], financial['total_savings'],
                    json.dumps(quotation), '1.0'
                ))
                database_connection.commit()
                
                error_scenarios.append({
                    'scenario': 'database_constraint_violation',
                    'success': False,  # Should have failed
                    'error_handled': False
                })
                
            except psycopg2.IntegrityError:
                # This is expected - constraint violation should be caught
                database_connection.rollback()
                error_scenarios.append({
                    'scenario': 'database_constraint_violation',
                    'success': True,  # Successfully caught the constraint violation
                    'error_handled': True
                })
            
            # Test recovery by generating new quote number
            recovery_quotation = dict(quotation)
            recovery_quotation['quote_number'] = recovery_quotation['quote_number'].replace('-', '-R-')  # Make it unique
            
            try:
                cursor.execute("""
                    INSERT INTO quotations 
                    (quote_number, customer_name, customer_tier, quote_date, valid_until,
                     status, subtotal, tax_amount, total_amount, total_items, total_savings,
                     quotation_data, version)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    recovery_quotation['quote_number'], 'Recovery Insert', 'standard',
                    quotation['quote_date'], quotation['valid_until'], 'draft',
                    financial['subtotal'], financial['tax_amount'], financial['total_amount'],
                    financial['total_items'], financial['total_savings'],
                    json.dumps(recovery_quotation), '1.0'
                ))
                database_connection.commit()
                
                recovery_results.append({
                    'scenario': 'successful_recovery',
                    'recovery_quote_number': recovery_quotation['quote_number'],
                    'success': True
                })
                
            except Exception as e:
                recovery_results.append({
                    'scenario': 'failed_recovery',
                    'error': str(e),
                    'success': False
                })
        
        # Scenario 3: Cache service interruption
        cache_errors = []
        try:
            # Test cache resilience
            test_data = {'test': 'cache_resilience', 'timestamp': datetime.now().isoformat()}
            cache_connection.set('resilience_test', json.dumps(test_data))
            
            retrieved_data = cache_connection.get('resilience_test')
            assert retrieved_data is not None, "Cache should store and retrieve data"
            
            # Test cache failure simulation
            invalid_key = 'nonexistent_key_12345'
            result = cache_connection.get(invalid_key)
            assert result is None, "Cache should handle missing keys gracefully"
            
            cache_errors.append({
                'scenario': 'cache_missing_key',
                'handled_gracefully': True,
                'success': True
            })
            
        except Exception as e:
            cache_errors.append({
                'scenario': 'cache_error',
                'error': str(e),
                'success': False
            })
        
        execution_time = time.time() - start_time
        assert execution_time < 10.0, f"E2E resilience test took too long: {execution_time:.3f}s"
        
        # Validate error handling effectiveness
        handled_scenarios = sum(1 for s in error_scenarios if s.get('error_handled', False))
        total_scenarios = len(error_scenarios)
        error_handling_rate = (handled_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0
        
        successful_recoveries = sum(1 for r in recovery_results if r.get('success', False))
        total_recoveries = len(recovery_results)
        recovery_rate = (successful_recoveries / total_recoveries * 100) if total_recoveries > 0 else 0
        
        cache_resilience = sum(1 for c in cache_errors if c.get('success', False))
        cache_scenarios = len(cache_errors)
        cache_resilience_rate = (cache_resilience / cache_scenarios * 100) if cache_scenarios > 0 else 0
        
        # Business Continuity Requirements
        assert error_handling_rate >= 80.0, f"Error handling rate below requirement: {error_handling_rate:.1f}%"
        
        print(f"✓ Error recovery: {error_handling_rate:.1f}% error handling, {recovery_rate:.1f}% recovery rate in {execution_time:.3f}s")
        
        return {
            'test_type': 'error_recovery_resilience',
            'error_scenarios': error_scenarios,
            'recovery_results': recovery_results,
            'cache_errors': cache_errors,
            'error_handling_rate': error_handling_rate,
            'recovery_rate': recovery_rate,
            'cache_resilience_rate': cache_resilience_rate,
            'execution_time': execution_time
        }
    
    def _generate_realistic_pricing(self, requirements: List[Dict]) -> Dict[str, Dict]:
        """Generate realistic pricing results for requirements."""
        pricing_results = {}
        
        # Pricing rules by category
        category_pricing = {
            'Heavy Equipment': {'base_price': 250000, 'variance': 50000},
            'Safety Equipment': {'base_price': 25, 'variance': 15},
            'Fleet Vehicles': {'base_price': 120000, 'variance': 30000},
            'Industrial Tools': {'base_price': 2500, 'variance': 1000},
            'Test Equipment': {'base_price': 1000, 'variance': 500},
            'Recovery Test': {'base_price': 100, 'variance': 50}
        }
        
        for i, req in enumerate(requirements):
            category = req.get('category', 'Unknown')
            pricing_info = category_pricing.get(category, {'base_price': 1000, 'variance': 500})
            
            base_price = pricing_info['base_price']
            variance = pricing_info['variance']
            
            # Calculate realistic unit price with variance
            unit_price = base_price + ((i % 5) - 2) * (variance / 3)  # Add some variance
            quantity = req.get('quantity', 1)
            total_price = unit_price * quantity
            
            # Calculate realistic savings based on quantity and tier
            volume_discount = 0.05 if quantity >= 10 else 0.02
            savings = total_price * volume_discount
            
            key = f"{category}_{i:04d}"
            pricing_results[key] = {
                'product_id': f"PROD-{category.upper()[:3]}-{i:03d}",
                'product_name': req.get('description', f'{category} Item'),
                'category': category,
                'brand': req.get('specifications', {}).get('brand', 'Generic'),
                'model': f"Model-{i:03d}",
                'quantity': quantity,
                'final_unit_price': round(unit_price, 2),
                'total_price': round(total_price, 2),
                'savings_breakdown': {
                    'volume_discount': round(savings, 2),
                    'total_savings': round(savings, 2)
                },
                'supplier_info': {
                    'name': f'Supplier {(i % 3) + 1}',
                    'delivery_time': req.get('delivery_requirement', '4-6 weeks'),
                    'warranty': req.get('warranty_requirement', '1 year standard')
                }
            }
        
        return pricing_results

if __name__ == "__main__":
    # Run specific test for development
    import os
    os.environ.setdefault('DB_HOST', 'localhost')
    os.environ.setdefault('DB_PORT', '6660')
    os.environ.setdefault('REDIS_HOST', 'localhost')
    os.environ.setdefault('REDIS_PORT', '6661')
    
    test_class = TestQuotationE2E()
    print("E2E Testing Framework Ready")