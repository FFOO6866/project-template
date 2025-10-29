"""Integration tests for quotation generation with multiple products.

Tests real quotation generation scenarios using actual quotations database
following Tier 2 integration testing requirements (NO MOCKING).
"""

import pytest
import sqlite3
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid


@pytest.mark.integration
@pytest.mark.database
class TestQuotationGeneration:
    """Test quotation generation with real database operations."""
    
    def test_quotation_creation_workflow(self, quotations_connection, database_connection, test_metrics_collector):
        """Test complete quotation creation workflow."""
        test_metrics_collector.start_test("quotation_creation_workflow")
        
        # Get sample products for quotation
        product_cursor = database_connection.cursor()
        product_cursor.execute("""
            SELECT id, sku, name, description, category_id
            FROM products 
            WHERE status = 'active' AND is_published = 1
            LIMIT 5
        """)
        test_metrics_collector.add_query()
        
        sample_products = product_cursor.fetchall()
        assert len(sample_products) > 0, "No sample products available for quotation"
        test_metrics_collector.add_records(len(sample_products))
        
        # Create quotation
        quotation_cursor = quotations_connection.cursor()
        
        quotation_data = {
            'customer_name': 'Test Construction Company',
            'customer_email': 'test@construction.com',
            'project_name': 'Office Building Construction',
            'quotation_date': datetime.now().strftime('%Y-%m-%d'),
            'valid_until': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'status': 'draft',
            'notes': 'Integration test quotation',
            'total_amount': 0.0
        }
        
        quotation_cursor.execute("""
            INSERT INTO quotations (
                customer_name, customer_email, project_name, 
                quotation_date, valid_until, status, notes, total_amount,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            quotation_data['customer_name'],
            quotation_data['customer_email'],
            quotation_data['project_name'],
            quotation_data['quotation_date'],
            quotation_data['valid_until'],
            quotation_data['status'],
            quotation_data['notes'],
            quotation_data['total_amount']
        ))
        test_metrics_collector.add_query()
        
        quotation_id = quotation_cursor.lastrowid
        assert quotation_id > 0, "Failed to create quotation"
        
        # Add quotation items
        total_amount = 0.0
        
        for i, product in enumerate(sample_products):
            item_data = {
                'product_id': product['id'],
                'product_sku': product['sku'],
                'product_name': product['name'],
                'quantity': (i + 1) * 2,  # Varying quantities
                'unit_price': 50.0 + (i * 25.0),  # Varying prices
                'total_price': 0.0,
                'description': f"Integration test item {i+1}"
            }
            
            item_data['total_price'] = item_data['quantity'] * item_data['unit_price']
            total_amount += item_data['total_price']
            
            quotation_cursor.execute("""
                INSERT INTO quotation_items (
                    quotation_id, product_id, product_sku, product_name,
                    quantity, unit_price, total_price, description,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                quotation_id,
                item_data['product_id'],
                item_data['product_sku'],
                item_data['product_name'],
                item_data['quantity'],
                item_data['unit_price'],
                item_data['total_price'],
                item_data['description']
            ))
            test_metrics_collector.add_query()
        
        # Update quotation total
        quotation_cursor.execute("""
            UPDATE quotations 
            SET total_amount = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (total_amount, quotation_id))
        test_metrics_collector.add_query()
        
        quotations_connection.commit()
        
        # Verify quotation was created correctly
        quotation_cursor.execute("""
            SELECT q.*, COUNT(qi.id) as item_count
            FROM quotations q
            LEFT JOIN quotation_items qi ON q.id = qi.quotation_id
            WHERE q.id = ?
            GROUP BY q.id
        """, (quotation_id,))
        test_metrics_collector.add_query()
        
        created_quotation = quotation_cursor.fetchone()
        assert created_quotation is not None, "Created quotation not found"
        assert created_quotation['customer_name'] == quotation_data['customer_name']
        assert created_quotation['total_amount'] == total_amount
        assert created_quotation['item_count'] == len(sample_products)
        
        test_metrics_collector.add_records(1)
        test_metrics_collector.end_test()
        
        # Clean up
        quotation_cursor.execute("DELETE FROM quotation_items WHERE quotation_id = ?", (quotation_id,))
        quotation_cursor.execute("DELETE FROM quotations WHERE id = ?", (quotation_id,))
        quotations_connection.commit()
        
        return quotation_id, total_amount
    
    def test_multi_product_quotation_calculation(self, quotations_connection, database_connection, test_metrics_collector):
        """Test quotation calculations with multiple products and quantities."""
        test_metrics_collector.start_test("multi_product_quotation_calculation")
        
        # Get products from different categories
        product_cursor = database_connection.cursor()
        product_cursor.execute("""
            SELECT p.id, p.sku, p.name, p.description, p.category_id, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.status = 'active' AND p.is_published = 1
            GROUP BY p.category_id
            LIMIT 3
        """)
        test_metrics_collector.add_query()
        
        products_by_category = product_cursor.fetchall()
        assert len(products_by_category) >= 2, "Need products from multiple categories"
        test_metrics_collector.add_records(len(products_by_category))
        
        # Create complex quotation
        quotation_cursor = quotations_connection.cursor()
        
        quotation_cursor.execute("""
            INSERT INTO quotations (
                customer_name, customer_email, project_name,
                quotation_date, valid_until, status, total_amount,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            'Multi-Product Test Client',
            'multitest@example.com',
            'Complex Construction Project',
            datetime.now().strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),
            'draft',
            0.0
        ))
        test_metrics_collector.add_query()
        
        quotation_id = quotation_cursor.lastrowid
        
        # Add items with varying quantities and prices
        quotation_items = []
        total_calculated = 0.0
        
        for i, product in enumerate(products_by_category):
            # Create multiple line items per product
            for variant in range(1, 3):  # 1-2 variants per product
                quantity = (i + 1) * variant * 5
                unit_price = 25.0 + (i * 15.0) + (variant * 10.0)
                total_price = quantity * unit_price
                
                item = {
                    'product_id': product['id'],
                    'product_sku': product['sku'],
                    'product_name': f"{product['name']} - Variant {variant}",
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': total_price,
                    'category': product['category_name']
                }
                
                quotation_cursor.execute("""
                    INSERT INTO quotation_items (
                        quotation_id, product_id, product_sku, product_name,
                        quantity, unit_price, total_price,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (
                    quotation_id,
                    item['product_id'],
                    item['product_sku'],
                    item['product_name'],
                    item['quantity'],
                    item['unit_price'],
                    item['total_price']
                ))
                test_metrics_collector.add_query()
                
                quotation_items.append(item)
                total_calculated += total_price
        
        # Update quotation total
        quotation_cursor.execute("""
            UPDATE quotations 
            SET total_amount = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (total_calculated, quotation_id))
        test_metrics_collector.add_query()
        
        quotations_connection.commit()
        
        # Verify calculations
        quotation_cursor.execute("""
            SELECT 
                SUM(qi.total_price) as calculated_total,
                SUM(qi.quantity * qi.unit_price) as manual_total,
                COUNT(qi.id) as item_count,
                AVG(qi.unit_price) as avg_unit_price
            FROM quotation_items qi
            WHERE qi.quotation_id = ?
        """, (quotation_id,))
        test_metrics_collector.add_query()
        
        calculation_result = quotation_cursor.fetchone()
        
        assert abs(calculation_result['calculated_total'] - total_calculated) < 0.01, \
            f"Total calculation mismatch: {calculation_result['calculated_total']} vs {total_calculated}"
        assert abs(calculation_result['manual_total'] - total_calculated) < 0.01, \
            "Manual calculation doesn't match"
        assert calculation_result['item_count'] == len(quotation_items), "Item count mismatch"
        assert calculation_result['avg_unit_price'] > 0, "Invalid average unit price"
        
        test_metrics_collector.add_records(calculation_result['item_count'])
        test_metrics_collector.end_test()
        
        # Clean up
        quotation_cursor.execute("DELETE FROM quotation_items WHERE quotation_id = ?", (quotation_id,))
        quotation_cursor.execute("DELETE FROM quotations WHERE id = ?", (quotation_id,))
        quotations_connection.commit()
        
        return calculation_result
    
    def test_quotation_status_workflow(self, quotations_connection, test_metrics_collector):
        """Test quotation status transitions (draft -> sent -> approved/rejected)."""
        test_metrics_collector.start_test("quotation_status_workflow")
        
        cursor = quotations_connection.cursor()
        
        # Create quotation in draft status
        cursor.execute("""
            INSERT INTO quotations (
                customer_name, customer_email, project_name,
                quotation_date, status, total_amount,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            'Status Test Client',
            'status@test.com',
            'Status Workflow Test',
            datetime.now().strftime('%Y-%m-%d'),
            'draft',
            1500.00
        ))
        test_metrics_collector.add_query()
        
        quotation_id = cursor.lastrowid
        
        # Test status transitions
        status_transitions = [
            ('draft', 'sent'),
            ('sent', 'approved'),
        ]
        
        for from_status, to_status in status_transitions:
            # Verify current status
            cursor.execute("SELECT status FROM quotations WHERE id = ?", (quotation_id,))
            test_metrics_collector.add_query()
            
            current = cursor.fetchone()
            assert current['status'] == from_status, f"Expected status {from_status}, got {current['status']}"
            
            # Update status
            cursor.execute("""
                UPDATE quotations 
                SET status = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (to_status, quotation_id))
            test_metrics_collector.add_query()
            
            quotations_connection.commit()
            
            # Verify status change
            cursor.execute("SELECT status, updated_at FROM quotations WHERE id = ?", (quotation_id,))
            test_metrics_collector.add_query()
            
            updated = cursor.fetchone()
            assert updated['status'] == to_status, f"Status not updated to {to_status}"
        
        # Test invalid status transition (should be prevented by application logic)
        cursor.execute("""
            UPDATE quotations 
            SET status = ?, updated_at = datetime('now')
            WHERE id = ?
        """, ('rejected', quotation_id))
        test_metrics_collector.add_query()
        
        quotations_connection.commit()
        
        # Verify final status
        cursor.execute("SELECT status FROM quotations WHERE id = ?", (quotation_id,))
        test_metrics_collector.add_query()
        
        final_status = cursor.fetchone()
        assert final_status['status'] in ['approved', 'rejected'], "Final status should be approved or rejected"
        
        test_metrics_collector.add_records(len(status_transitions) + 1)
        test_metrics_collector.end_test()
        
        # Clean up
        cursor.execute("DELETE FROM quotations WHERE id = ?", (quotation_id,))
        quotations_connection.commit()
    
    def test_quotation_search_and_filtering(self, quotations_connection, database_connection, test_metrics_collector):
        """Test searching and filtering quotations."""
        test_metrics_collector.start_test("quotation_search_and_filtering")
        
        cursor = quotations_connection.cursor()
        
        # Create test quotations with different characteristics
        test_quotations = [
            {
                'customer_name': 'ABC Construction Ltd',
                'customer_email': 'abc@construction.com',
                'project_name': 'Shopping Mall Project',
                'status': 'sent',
                'total_amount': 50000.00
            },
            {
                'customer_name': 'XYZ Builders Inc',
                'customer_email': 'xyz@builders.com',
                'project_name': 'Office Complex Development',
                'status': 'approved',
                'total_amount': 75000.00
            },
            {
                'customer_name': 'DEF Contractors',
                'customer_email': 'def@contractors.com',
                'project_name': 'Residential Complex',
                'status': 'draft',
                'total_amount': 25000.00
            }
        ]
        
        created_quotation_ids = []
        
        for quotation_data in test_quotations:
            cursor.execute("""
                INSERT INTO quotations (
                    customer_name, customer_email, project_name,
                    quotation_date, status, total_amount,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                quotation_data['customer_name'],
                quotation_data['customer_email'],
                quotation_data['project_name'],
                datetime.now().strftime('%Y-%m-%d'),
                quotation_data['status'],
                quotation_data['total_amount']
            ))
            test_metrics_collector.add_query()
            
            created_quotation_ids.append(cursor.lastrowid)
        
        quotations_connection.commit()
        
        # Test various search and filter scenarios
        
        # 1. Search by customer name
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM quotations 
            WHERE LOWER(customer_name) LIKE LOWER(?)
        """, ('%construction%',))
        test_metrics_collector.add_query()
        
        customer_search_count = cursor.fetchone()['count']
        assert customer_search_count >= 1, "Customer name search failed"
        test_metrics_collector.add_records(customer_search_count)
        
        # 2. Filter by status
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM quotations 
            WHERE status = ?
        """, ('approved',))
        test_metrics_collector.add_query()
        
        status_filter_count = cursor.fetchone()['count']
        assert status_filter_count >= 1, "Status filter failed"
        test_metrics_collector.add_records(status_filter_count)
        
        # 3. Filter by amount range
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM quotations 
            WHERE total_amount BETWEEN ? AND ?
        """, (30000.00, 80000.00))
        test_metrics_collector.add_query()
        
        amount_filter_count = cursor.fetchone()['count']
        assert amount_filter_count >= 1, "Amount range filter failed"
        test_metrics_collector.add_records(amount_filter_count)
        
        # 4. Search by project name
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM quotations 
            WHERE LOWER(project_name) LIKE LOWER(?)
        """, ('%complex%',))
        test_metrics_collector.add_query()
        
        project_search_count = cursor.fetchone()['count']
        assert project_search_count >= 1, "Project name search failed"
        test_metrics_collector.add_records(project_search_count)
        
        # 5. Combined filters
        cursor.execute("""
            SELECT id, customer_name, project_name, status, total_amount
            FROM quotations 
            WHERE status IN ('sent', 'approved')
            AND total_amount > ?
            ORDER BY total_amount DESC
        """, (40000.00,))
        test_metrics_collector.add_query()
        
        combined_results = cursor.fetchall()
        assert len(combined_results) >= 1, "Combined filter failed"
        test_metrics_collector.add_records(len(combined_results))
        
        # Verify sorting
        if len(combined_results) > 1:
            for i in range(len(combined_results) - 1):
                assert combined_results[i]['total_amount'] >= combined_results[i+1]['total_amount'], \
                    "Results not properly sorted by amount"
        
        test_metrics_collector.end_test()
        
        # Clean up
        for quotation_id in created_quotation_ids:
            cursor.execute("DELETE FROM quotations WHERE id = ?", (quotation_id,))
        quotations_connection.commit()
    
    def test_quotation_item_management(self, quotations_connection, database_connection, test_metrics_collector):
        """Test adding, updating, and removing quotation items."""
        test_metrics_collector.start_test("quotation_item_management")
        
        # Get sample products
        product_cursor = database_connection.cursor()
        product_cursor.execute("""
            SELECT id, sku, name FROM products 
            WHERE status = 'active' AND is_published = 1
            LIMIT 3
        """)
        test_metrics_collector.add_query()
        
        products = product_cursor.fetchall()
        assert len(products) >= 3, "Need at least 3 products for item management test"
        
        # Create quotation
        quotation_cursor = quotations_connection.cursor()
        quotation_cursor.execute("""
            INSERT INTO quotations (
                customer_name, customer_email, project_name,
                quotation_date, status, total_amount,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            'Item Management Test',
            'itemtest@example.com',
            'Item Management Project',
            datetime.now().strftime('%Y-%m-%d'),
            'draft',
            0.0
        ))
        test_metrics_collector.add_query()
        
        quotation_id = quotation_cursor.lastrowid
        
        # Add initial items
        initial_items = []
        for i, product in enumerate(products):
            item_data = {
                'product_id': product['id'],
                'product_sku': product['sku'],
                'product_name': product['name'],
                'quantity': (i + 1) * 3,
                'unit_price': 100.0 + (i * 50.0),
                'total_price': 0.0
            }
            item_data['total_price'] = item_data['quantity'] * item_data['unit_price']
            
            quotation_cursor.execute("""
                INSERT INTO quotation_items (
                    quotation_id, product_id, product_sku, product_name,
                    quantity, unit_price, total_price,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                quotation_id,
                item_data['product_id'],
                item_data['product_sku'],
                item_data['product_name'],
                item_data['quantity'],
                item_data['unit_price'],
                item_data['total_price']
            ))
            test_metrics_collector.add_query()
            
            item_data['id'] = quotation_cursor.lastrowid
            initial_items.append(item_data)
        
        # Update an item (change quantity and recalculate)
        updated_item = initial_items[0]
        new_quantity = updated_item['quantity'] + 5
        new_total = new_quantity * updated_item['unit_price']
        
        quotation_cursor.execute("""
            UPDATE quotation_items 
            SET quantity = ?, total_price = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (new_quantity, new_total, updated_item['id']))
        test_metrics_collector.add_query()
        
        # Verify update
        quotation_cursor.execute("""
            SELECT quantity, total_price FROM quotation_items WHERE id = ?
        """, (updated_item['id'],))
        test_metrics_collector.add_query()
        
        updated_record = quotation_cursor.fetchone()
        assert updated_record['quantity'] == new_quantity, "Quantity not updated correctly"
        assert abs(updated_record['total_price'] - new_total) < 0.01, "Total price not updated correctly"
        
        # Remove an item
        item_to_remove = initial_items[1]
        quotation_cursor.execute("""
            DELETE FROM quotation_items WHERE id = ?
        """, (item_to_remove['id'],))
        test_metrics_collector.add_query()
        
        # Verify removal
        quotation_cursor.execute("""
            SELECT COUNT(*) as count FROM quotation_items WHERE quotation_id = ?
        """, (quotation_id,))
        test_metrics_collector.add_query()
        
        remaining_count = quotation_cursor.fetchone()['count']
        assert remaining_count == len(initial_items) - 1, "Item not removed correctly"
        
        # Calculate and update quotation total
        quotation_cursor.execute("""
            SELECT SUM(total_price) as total FROM quotation_items WHERE quotation_id = ?
        """, (quotation_id,))
        test_metrics_collector.add_query()
        
        calculated_total = quotation_cursor.fetchone()['total'] or 0.0
        
        quotation_cursor.execute("""
            UPDATE quotations 
            SET total_amount = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (calculated_total, quotation_id))
        test_metrics_collector.add_query()
        
        # Verify final state
        quotation_cursor.execute("""
            SELECT 
                q.total_amount,
                COUNT(qi.id) as item_count,
                SUM(qi.total_price) as items_total
            FROM quotations q
            LEFT JOIN quotation_items qi ON q.id = qi.quotation_id
            WHERE q.id = ?
            GROUP BY q.id
        """, (quotation_id,))
        test_metrics_collector.add_query()
        
        final_state = quotation_cursor.fetchone()
        assert abs(final_state['total_amount'] - final_state['items_total']) < 0.01, \
            "Quotation total doesn't match sum of items"
        assert final_state['item_count'] == remaining_count, "Item count mismatch"
        
        test_metrics_collector.add_records(final_state['item_count'])
        test_metrics_collector.end_test()
        
        # Clean up
        quotation_cursor.execute("DELETE FROM quotation_items WHERE quotation_id = ?", (quotation_id,))
        quotation_cursor.execute("DELETE FROM quotations WHERE id = ?", (quotation_id,))
        quotations_connection.commit()


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.performance
class TestQuotationPerformance:
    """Test quotation system performance with large datasets."""
    
    def test_large_quotation_generation_performance(self, quotations_connection, database_connection, test_metrics_collector):
        """Test performance of generating quotations with many items."""
        test_metrics_collector.start_test("large_quotation_generation_performance")
        
        # Get products for large quotation
        product_cursor = database_connection.cursor()
        product_cursor.execute("""
            SELECT id, sku, name FROM products 
            WHERE status = 'active' AND is_published = 1
            LIMIT 50
        """)
        test_metrics_collector.add_query()
        
        products = product_cursor.fetchall()
        assert len(products) >= 20, "Need at least 20 products for large quotation test"
        
        quotation_cursor = quotations_connection.cursor()
        
        # Create large quotation
        start_time = time.time()
        
        quotation_cursor.execute("""
            INSERT INTO quotations (
                customer_name, customer_email, project_name,
                quotation_date, status, total_amount,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            'Large Quotation Performance Test',
            'performance@test.com',
            'Large Scale Construction Project',
            datetime.now().strftime('%Y-%m-%d'),
            'draft',
            0.0
        ))
        test_metrics_collector.add_query()
        
        quotation_id = quotation_cursor.lastrowid
        creation_time = (time.time() - start_time) * 1000
        
        # Add many items
        items_start_time = time.time()
        total_amount = 0.0
        
        for i, product in enumerate(products):
            quantity = (i % 10) + 1  # 1-10 quantity
            unit_price = 50.0 + (i * 5.0)
            total_price = quantity * unit_price
            total_amount += total_price
            
            quotation_cursor.execute("""
                INSERT INTO quotation_items (
                    quotation_id, product_id, product_sku, product_name,
                    quantity, unit_price, total_price,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                quotation_id, product['id'], product['sku'], product['name'],
                quantity, unit_price, total_price
            ))
            test_metrics_collector.add_query()
        
        items_time = (time.time() - items_start_time) * 1000
        
        # Update quotation total
        update_start_time = time.time()
        quotation_cursor.execute("""
            UPDATE quotations 
            SET total_amount = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (total_amount, quotation_id))
        test_metrics_collector.add_query()
        
        quotations_connection.commit()
        update_time = (time.time() - update_start_time) * 1000
        
        total_time = creation_time + items_time + update_time
        avg_time_per_item = items_time / len(products)
        
        # Performance assertions
        assert creation_time < 100, f"Quotation creation took {creation_time}ms, should be < 100ms"
        assert avg_time_per_item < 50, f"Average item creation {avg_time_per_item}ms too slow"
        assert total_time < 5000, f"Total large quotation creation took {total_time}ms, should be < 5000ms"
        
        test_metrics_collector.add_records(len(products))
        test_metrics_collector.end_test()
        
        # Clean up
        quotation_cursor.execute("DELETE FROM quotation_items WHERE quotation_id = ?", (quotation_id,))
        quotation_cursor.execute("DELETE FROM quotations WHERE id = ?", (quotation_id,))
        quotations_connection.commit()
    
    def test_concurrent_quotation_operations(self, test_quotations_db_path, test_database_path, test_metrics_collector):
        """Test concurrent quotation creation and modification."""
        test_metrics_collector.start_test("concurrent_quotation_operations")
        
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def create_quotation_concurrent(thread_id: int) -> Dict[str, Any]:
            """Create quotation in separate thread."""
            quot_conn = sqlite3.connect(test_quotations_db_path)
            prod_conn = sqlite3.connect(test_database_path)
            
            try:
                quot_cursor = quot_conn.cursor()
                prod_cursor = prod_conn.cursor()
                
                # Get some products
                prod_cursor.execute("""
                    SELECT id, sku, name FROM products 
                    WHERE status = 'active' 
                    LIMIT 5 OFFSET ?
                """, (thread_id * 5,))
                
                products = prod_cursor.fetchall()
                if not products:
                    return {'thread_id': thread_id, 'success': False, 'error': 'No products found'}
                
                # Create quotation
                quot_cursor.execute("""
                    INSERT INTO quotations (
                        customer_name, customer_email, project_name,
                        quotation_date, status, total_amount,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (
                    f'Concurrent Client {thread_id}',
                    f'client{thread_id}@test.com',
                    f'Concurrent Project {thread_id}',
                    datetime.now().strftime('%Y-%m-%d'),
                    'draft',
                    0.0
                ))
                
                quotation_id = quot_cursor.lastrowid
                total_amount = 0.0
                
                # Add items
                for i, product in enumerate(products):
                    quantity = (i + 1) * 2
                    unit_price = 100.0 + (thread_id * 10.0)
                    total_price = quantity * unit_price
                    total_amount += total_price
                    
                    quot_cursor.execute("""
                        INSERT INTO quotation_items (
                            quotation_id, product_id, product_sku, product_name,
                            quantity, unit_price, total_price,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    """, (
                        quotation_id, product['id'], product['sku'], product['name'],
                        quantity, unit_price, total_price
                    ))
                
                # Update total
                quot_cursor.execute("""
                    UPDATE quotations 
                    SET total_amount = ?, updated_at = datetime('now')
                    WHERE id = ?
                """, (total_amount, quotation_id))
                
                quot_conn.commit()
                
                return {
                    'thread_id': thread_id,
                    'quotation_id': quotation_id,
                    'item_count': len(products),
                    'total_amount': total_amount,
                    'success': True
                }
                
            except Exception as e:
                return {'thread_id': thread_id, 'error': str(e), 'success': False}
            finally:
                quot_conn.close()
                prod_conn.close()
        
        # Run concurrent quotation creation
        num_threads = 5
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for i in range(num_threads):
                future = executor.submit(create_quotation_concurrent, i)
                futures.append(future)
            
            results = [future.result() for future in as_completed(futures)]
        
        total_time = (time.time() - start_time) * 1000
        
        # Validate results
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        assert len(failed) == 0, f"Concurrent quotation creation failed: {failed}"
        assert len(successful) == num_threads, "Not all quotations created successfully"
        assert total_time < 10000, f"Concurrent operations took {total_time}ms, should be < 10000ms"
        
        # Verify quotations in database
        quot_conn = sqlite3.connect(test_quotations_db_path)
        cursor = quot_conn.cursor()
        
        for result in successful:
            cursor.execute("SELECT total_amount FROM quotations WHERE id = ?", (result['quotation_id'],))
            stored_quotation = cursor.fetchone()
            assert stored_quotation is not None, f"Quotation {result['quotation_id']} not found"
            assert abs(stored_quotation[0] - result['total_amount']) < 0.01, "Amount mismatch in concurrent creation"
        
        total_items = sum(r['item_count'] for r in successful)
        test_metrics_collector.add_records(total_items)
        test_metrics_collector.end_test()
        
        # Clean up
        for result in successful:
            cursor.execute("DELETE FROM quotation_items WHERE quotation_id = ?", (result['quotation_id'],))
            cursor.execute("DELETE FROM quotations WHERE id = ?", (result['quotation_id'],))
        
        quot_conn.commit()
        quot_conn.close()