#!/usr/bin/env python3
"""
TIER 1 - COMPONENT TESTING (<1 second)
Tests individual quotation workflow components with real data validation.
"""

import pytest
import json
import time
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

class TestQuotationComponents:
    """Test individual quotation workflow components."""
    
    @pytest.fixture
    def quotation_workflow(self):
        """Create quotation workflow instance."""
        return QuotationGenerationWorkflow()
    
    @pytest.fixture
    def sample_requirements(self):
        """Sample requirements for testing."""
        return [
            {
                'category': 'Power Tools',
                'description': 'DEWALT DCD791D2 20V cordless drill',
                'quantity': 50,
                'keywords': ['dewalt', 'dcd791d2', '20v', 'cordless', 'drill'],
                'brand': 'DEWALT',
                'model': 'DCD791D2'
            },
            {
                'category': 'Safety Equipment',
                'description': '3M Safety Glasses with Anti-Fog',
                'quantity': 100,
                'keywords': ['3m', 'safety', 'glasses', 'anti-fog'],
                'brand': '3M',
                'model': 'SecureFit SF401AF'
            }
        ]
    
    @pytest.fixture
    def sample_pricing_results(self):
        """Sample pricing results for testing."""
        return {
            'pricing_results': {
                'Power Tools_1234': {
                    'product_id': 'DWT-001',
                    'product_name': 'DEWALT DCD791D2 20V MAX XR Cordless Drill',
                    'category': 'Power Tools',
                    'brand': 'DEWALT',
                    'model': 'DCD791D2',
                    'quantity': 50,
                    'final_unit_price': 179.99,
                    'total_price': 8999.50,
                    'savings_breakdown': {'total_savings': 900.50}
                },
                'Safety Equipment_5678': {
                    'product_id': '3M-SF401AF',
                    'product_name': '3M SecureFit Safety Glasses Anti-Fog',
                    'category': 'Safety Equipment',
                    'brand': '3M',
                    'model': 'SF401AF',
                    'quantity': 100,
                    'final_unit_price': 12.99,
                    'total_price': 1299.00,
                    'savings_breakdown': {'total_savings': 200.00}
                }
            }
        }
    
    @pytest.mark.timeout(1)
    def test_quote_number_generation(self, quotation_workflow):
        """Test quote number generation algorithm."""
        start_time = time.time()
        
        workflow = quotation_workflow.create_quotation_data_workflow()
        runtime = LocalRuntime()
        
        # Test with minimal data
        params = {
            'requirements': [{'category': 'Test', 'description': 'Test item', 'quantity': 1}],
            'pricing_results': {
                'pricing_results': {
                    'test_key': {
                        'product_id': 'TEST-001',
                        'product_name': 'Test Product',
                        'final_unit_price': 100.0,
                        'total_price': 100.0,
                        'savings_breakdown': {'total_savings': 10.0}
                    }
                }
            }
        }
        
        results, run_id = runtime.execute(workflow, parameters=params)
        
        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Component test took too long: {execution_time:.3f}s"
        
        # Validate quote number format
        quote_number = results.get('quote_number', '')
        assert quote_number.startswith('Q'), "Quote number should start with 'Q'"
        assert len(quote_number) >= 12, "Quote number should be at least 12 characters"
        assert '-' in quote_number, "Quote number should contain hyphen separator"
        
        # Validate date component in quote number
        date_part = quote_number[1:9]  # YYYYMMDD
        assert date_part.isdigit(), "Date part should be numeric"
        assert len(date_part) == 8, "Date part should be 8 digits"
        
        print(f"✓ Quote number generation: {quote_number} in {execution_time:.3f}s")
    
    @pytest.mark.timeout(1)
    def test_financial_calculations(self, quotation_workflow, sample_requirements, sample_pricing_results):
        """Test financial calculations accuracy."""
        start_time = time.time()
        
        workflow = quotation_workflow.create_quotation_data_workflow()
        runtime = LocalRuntime()
        
        params = {
            'requirements': sample_requirements,
            'pricing_results': sample_pricing_results,
            'customer_name': 'Test Customer',
            'customer_tier': 'enterprise'
        }
        
        results, run_id = runtime.execute(workflow, parameters=params)
        
        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Component test took too long: {execution_time:.3f}s"
        
        quotation = results.get('quotation', {})
        financial = quotation.get('financial_summary', {})
        
        # Test financial calculations with zero tolerance for errors
        expected_subtotal = 8999.50 + 1299.00  # 10298.50
        expected_tax = expected_subtotal * 0.10  # 1029.85
        expected_total = expected_subtotal + expected_tax  # 11328.35
        expected_savings = 900.50 + 200.00  # 1100.50
        
        assert financial['subtotal'] == expected_subtotal, f"Subtotal calculation error: expected {expected_subtotal}, got {financial['subtotal']}"
        assert financial['tax_amount'] == round(expected_tax, 2), f"Tax calculation error: expected {round(expected_tax, 2)}, got {financial['tax_amount']}"
        assert financial['total_amount'] == round(expected_total, 2), f"Total calculation error: expected {round(expected_total, 2)}, got {financial['total_amount']}"
        assert financial['total_savings'] == expected_savings, f"Savings calculation error: expected {expected_savings}, got {financial['total_savings']}"
        
        # Test precision requirements
        assert isinstance(financial['subtotal'], (int, float)), "Subtotal should be numeric"
        assert isinstance(financial['tax_amount'], (int, float)), "Tax amount should be numeric"
        assert isinstance(financial['total_amount'], (int, float)), "Total amount should be numeric"
        
        # Test business logic constraints
        assert financial['total_amount'] > financial['subtotal'], "Total should be greater than subtotal"
        assert financial['tax_rate'] >= 0, "Tax rate should be non-negative"
        assert financial['total_items'] == 2, "Should count correct number of items"
        
        print(f"✓ Financial calculations: ${financial['total_amount']:,.2f} in {execution_time:.3f}s")
    
    @pytest.mark.timeout(1)
    def test_line_item_generation(self, quotation_workflow, sample_requirements, sample_pricing_results):
        """Test line item generation accuracy."""
        start_time = time.time()
        
        workflow = quotation_workflow.create_quotation_data_workflow()
        runtime = LocalRuntime()
        
        params = {
            'requirements': sample_requirements,
            'pricing_results': sample_pricing_results
        }
        
        results, run_id = runtime.execute(workflow, parameters=params)
        
        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Component test took too long: {execution_time:.3f}s"
        
        quotation = results.get('quotation', {})
        line_items = quotation.get('line_items', [])
        
        # Validate line item count and structure
        assert len(line_items) == 2, "Should generate correct number of line items"
        
        for i, item in enumerate(line_items, 1):
            # Required fields validation
            required_fields = ['line_number', 'product_id', 'product_name', 'quantity', 'unit_price', 'line_total']
            for field in required_fields:
                assert field in item, f"Line item {i} missing required field: {field}"
                assert item[field] is not None, f"Line item {i} field {field} should not be None"
            
            # Data type validation
            assert isinstance(item['line_number'], int), f"Line number should be integer"
            assert isinstance(item['quantity'], int), f"Quantity should be integer"
            assert isinstance(item['unit_price'], (int, float)), f"Unit price should be numeric"
            assert isinstance(item['line_total'], (int, float)), f"Line total should be numeric"
            
            # Business logic validation
            assert item['line_number'] == i, f"Line number should be sequential: expected {i}, got {item['line_number']}"
            assert item['quantity'] > 0, f"Quantity should be positive"
            assert item['unit_price'] > 0, f"Unit price should be positive"
            assert abs(item['line_total'] - (item['quantity'] * item['unit_price'])) < 0.01, f"Line total calculation error"
        
        # Validate specific line items match expected data
        dewalt_item = next((item for item in line_items if 'DEWALT' in item['product_name']), None)
        assert dewalt_item is not None, "Should find DEWALT product"
        assert dewalt_item['quantity'] == 50, "DEWALT quantity should match"
        assert dewalt_item['unit_price'] == 179.99, "DEWALT unit price should match"
        
        safety_item = next((item for item in line_items if '3M' in item['product_name']), None)
        assert safety_item is not None, "Should find 3M product"
        assert safety_item['quantity'] == 100, "3M quantity should match"
        assert safety_item['unit_price'] == 12.99, "3M unit price should match"
        
        print(f"✓ Line item generation: {len(line_items)} items in {execution_time:.3f}s")
    
    @pytest.mark.timeout(1)
    def test_quotation_metadata(self, quotation_workflow, sample_requirements, sample_pricing_results):
        """Test quotation metadata generation."""
        start_time = time.time()
        
        workflow = quotation_workflow.create_quotation_data_workflow()
        runtime = LocalRuntime()
        
        params = {
            'requirements': sample_requirements,
            'pricing_results': sample_pricing_results,
            'customer_name': 'Enterprise Customer',
            'customer_tier': 'enterprise'
        }
        
        results, run_id = runtime.execute(workflow, parameters=params)
        
        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Component test took too long: {execution_time:.3f}s"
        
        quotation = results.get('quotation', {})
        
        # Validate metadata structure
        required_sections = ['quote_number', 'quote_date', 'valid_until', 'customer_info', 'rfp_info', 'terms_and_conditions']
        for section in required_sections:
            assert section in quotation, f"Missing required section: {section}"
        
        # Validate customer information
        customer_info = quotation['customer_info']
        assert customer_info['name'] == 'Enterprise Customer', "Customer name should match"
        assert customer_info['tier'] == 'enterprise', "Customer tier should match"
        
        # Validate RFP information
        rfp_info = quotation['rfp_info']
        assert rfp_info['requirements_count'] == 2, "Should count requirements correctly"
        assert 'Power Tools' in rfp_info['categories'], "Should include Power Tools category"
        assert 'Safety Equipment' in rfp_info['categories'], "Should include Safety Equipment category"
        assert rfp_info['total_quantity'] == 150, "Should sum quantities correctly"
        
        # Validate date logic
        quote_date = datetime.strptime(quotation['quote_date'], '%Y-%m-%d')
        valid_until = datetime.strptime(quotation['valid_until'], '%Y-%m-%d')
        assert valid_until > quote_date, "Valid until should be after quote date"
        
        # Validate terms and conditions
        terms = quotation['terms_and_conditions']
        required_terms = ['payment_terms', 'delivery_terms', 'validity', 'warranty', 'notes']
        for term in required_terms:
            assert term in terms, f"Missing required term: {term}"
            assert isinstance(terms[term], str), f"Term {term} should be string"
            assert len(terms[term]) > 0, f"Term {term} should not be empty"
        
        print(f"✓ Quotation metadata: {quotation['quote_number']} in {execution_time:.3f}s")
    
    @pytest.mark.timeout(1)
    def test_edge_case_calculations(self, quotation_workflow):
        """Test edge cases in financial calculations."""
        start_time = time.time()
        
        workflow = quotation_workflow.create_quotation_data_workflow()
        runtime = LocalRuntime()
        
        # Test with zero quantity
        params = {
            'requirements': [{'category': 'Test', 'description': 'Zero quantity test', 'quantity': 0}],
            'pricing_results': {
                'pricing_results': {
                    'zero_test': {
                        'product_id': 'ZERO-001',
                        'product_name': 'Zero Quantity Product',
                        'final_unit_price': 100.0,
                        'total_price': 0.0,
                        'savings_breakdown': {'total_savings': 0.0}
                    }
                }
            }
        }
        
        results, run_id = runtime.execute(workflow, parameters=params)
        
        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Component test took too long: {execution_time:.3f}s"
        
        quotation = results.get('quotation', {})
        financial = quotation.get('financial_summary', {})
        
        # Test zero calculations
        assert financial['subtotal'] == 0.0, "Subtotal should be zero for zero quantity"
        assert financial['tax_amount'] == 0.0, "Tax should be zero for zero subtotal"
        assert financial['total_amount'] == 0.0, "Total should be zero"
        
        # Test with high precision decimal
        params_decimal = {
            'requirements': [{'category': 'Test', 'description': 'Decimal test', 'quantity': 3}],
            'pricing_results': {
                'pricing_results': {
                    'decimal_test': {
                        'product_id': 'DEC-001',
                        'product_name': 'Decimal Product',
                        'final_unit_price': 33.333333,
                        'total_price': 99.999999,
                        'savings_breakdown': {'total_savings': 1.111111}
                    }
                }
            }
        }
        
        results_decimal, _ = runtime.execute(workflow, parameters=params_decimal)
        quotation_decimal = results_decimal.get('quotation', {})
        financial_decimal = quotation_decimal.get('financial_summary', {})
        
        # Test decimal precision handling
        assert isinstance(financial_decimal['subtotal'], (int, float)), "Should handle decimal precision"
        assert isinstance(financial_decimal['total_amount'], (int, float)), "Should handle decimal precision"
        
        print(f"✓ Edge case calculations: Zero and decimal handling in {execution_time:.3f}s")
    
    @pytest.mark.timeout(1)
    def test_enterprise_grade_precision(self, quotation_workflow):
        """Test Enterprise Grade precision requirements (≥95% precision, ≥90% recall)."""
        start_time = time.time()
        
        workflow = quotation_workflow.create_quotation_data_workflow()
        runtime = LocalRuntime()
        
        # Test multiple precision scenarios
        test_cases = [
            # High volume, low unit price
            {'unit_price': 0.99, 'quantity': 10000, 'expected_total': 9900.00},
            # High unit price, low volume
            {'unit_price': 9999.99, 'quantity': 1, 'expected_total': 9999.99},
            # Complex decimal calculation
            {'unit_price': 123.456789, 'quantity': 7, 'expected_total': 864.20}  # Rounded to 2 decimal places
        ]
        
        precision_errors = 0
        for i, case in enumerate(test_cases):
            params = {
                'requirements': [{'category': 'Precision', 'description': f'Precision test {i}', 'quantity': case['quantity']}],
                'pricing_results': {
                    'pricing_results': {
                        f'precision_test_{i}': {
                            'product_id': f'PREC-{i:03d}',
                            'product_name': f'Precision Product {i}',
                            'final_unit_price': case['unit_price'],
                            'total_price': case['unit_price'] * case['quantity'],
                            'savings_breakdown': {'total_savings': 0.0}
                        }
                    }
                }
            }
            
            results, _ = runtime.execute(workflow, parameters=params)
            quotation = results.get('quotation', {})
            financial = quotation.get('financial_summary', {})
            
            actual_subtotal = financial.get('subtotal', 0)
            expected_subtotal = case['expected_total']
            
            # Allow for floating point precision tolerance
            precision_error = abs(actual_subtotal - expected_subtotal)
            if precision_error > 0.01:  # More than 1 cent difference
                precision_errors += 1
                print(f"Precision error in case {i}: expected {expected_subtotal}, got {actual_subtotal}")
        
        # Calculate precision metrics
        total_cases = len(test_cases)
        precision_rate = (total_cases - precision_errors) / total_cases * 100
        
        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Component test took too long: {execution_time:.3f}s"
        assert precision_rate >= 95.0, f"Precision rate {precision_rate:.1f}% below Enterprise Grade requirement of ≥95%"
        
        print(f"✓ Enterprise Grade precision: {precision_rate:.1f}% accuracy in {execution_time:.3f}s")
    
    @pytest.mark.timeout(1)
    def test_performance_benchmarking(self, quotation_workflow, sample_requirements, sample_pricing_results):
        """Test performance benchmarking with statistical analysis."""
        execution_times = []
        
        # Run multiple iterations for statistical analysis
        for i in range(10):
            start_time = time.time()
            
            workflow = quotation_workflow.create_quotation_data_workflow()
            runtime = LocalRuntime()
            
            params = {
                'requirements': sample_requirements,
                'pricing_results': sample_pricing_results,
                'customer_name': f'Benchmark Customer {i}',
                'customer_tier': 'standard'
            }
            
            results, run_id = runtime.execute(workflow, parameters=params)
            
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            # Validate each execution
            assert results.get('success', False), f"Execution {i} should succeed"
            assert execution_time < 1.0, f"Execution {i} took too long: {execution_time:.3f}s"
        
        # Statistical analysis
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        std_dev = (sum((t - avg_time) ** 2 for t in execution_times) / len(execution_times)) ** 0.5
        
        # Performance requirements
        assert avg_time < 0.5, f"Average execution time {avg_time:.3f}s exceeds 0.5s threshold"
        assert max_time < 1.0, f"Maximum execution time {max_time:.3f}s exceeds 1.0s threshold"
        assert std_dev < 0.1, f"Standard deviation {std_dev:.3f}s indicates inconsistent performance"
        
        # 95th percentile calculation
        sorted_times = sorted(execution_times)
        percentile_95 = sorted_times[int(0.95 * len(sorted_times))]
        assert percentile_95 < 0.8, f"95th percentile {percentile_95:.3f}s exceeds 0.8s threshold"
        
        print(f"✓ Performance benchmarking: avg={avg_time:.3f}s, max={max_time:.3f}s, std={std_dev:.3f}s")
        
        # Return performance metrics for reporting
        return {
            'component_type': 'quotation_generation',
            'iterations': len(execution_times),
            'avg_time': avg_time,
            'max_time': max_time,
            'min_time': min_time,
            'std_dev': std_dev,
            'percentile_95': percentile_95,
            'all_times': execution_times
        }

if __name__ == "__main__":
    # Run specific test for development
    import sys
    test_class = TestQuotationComponents()
    test_class.test_quote_number_generation(test_class.quotation_workflow())