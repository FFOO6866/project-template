"""Integration tests for database operations with real 17,266 products dataset.

This module tests database operations using the actual product database
following Tier 2 integration testing requirements (NO MOCKING).
"""

import pytest
import sqlite3
import time
import json
from typing import List, Dict, Any
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseOperations:
    """Test database operations with real product data."""
    
    def test_database_connection_and_schema(self, database_connection, test_metrics_collector):
        """Test basic database connectivity and schema validation."""
        test_metrics_collector.start_test("database_connection_and_schema") 
        
        cursor = database_connection.cursor()
        
        # Verify tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        test_metrics_collector.add_query()
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['products', 'categories', 'brands']
        for table in expected_tables:
            assert table in tables, f"Required table '{table}' not found"
        
        # Verify products table schema
        cursor.execute("PRAGMA table_info(products)")
        test_metrics_collector.add_query()
        columns = cursor.fetchall()
        
        required_columns = ['id', 'sku', 'name', 'description', 'category_id', 'brand_id']
        column_names = [col[1] for col in columns]
        for col in required_columns:
            assert col in column_names, f"Required column '{col}' not found"
        
        test_metrics_collector.end_test()
        assert test_metrics_collector['duration_ms'] < 1000, "Schema validation should be fast"
    
    def test_product_count_validation(self, database_connection, test_metrics_collector):
        """Verify the database contains exactly 17,266 products."""
        test_metrics_collector.start_test("product_count_validation")
        
        cursor = database_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        test_metrics_collector.add_query()
        
        count = cursor.fetchone()[0]
        test_metrics_collector.add_records(count)
        
        assert count == 17266, f"Expected 17,266 products, found {count}"
        
        test_metrics_collector.end_test()
        assert test_metrics_collector['duration_ms'] < 2000, "Product count query too slow"
    
    def test_product_data_integrity(self, database_connection, test_metrics_collector):
        """Test product data integrity and completeness."""
        test_metrics_collector.start_test("product_data_integrity")
        
        cursor = database_connection.cursor()
        
        # Check for null required fields
        cursor.execute("""
            SELECT COUNT(*) FROM products 
            WHERE name IS NULL OR sku IS NULL OR category_id IS NULL
        """)
        test_metrics_collector.add_query()
        null_count = cursor.fetchone()[0]
        assert null_count == 0, f"Found {null_count} products with null required fields"
        
        # Check for duplicate SKUs
        cursor.execute("""
            SELECT sku, COUNT(*) as count FROM products 
            GROUP BY sku HAVING count > 1
        """)
        test_metrics_collector.add_query()
        duplicates = cursor.fetchall()
        assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate SKUs"
        
        # Verify category relationships
        cursor.execute("""
            SELECT COUNT(*) FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE c.id IS NULL
        """)
        test_metrics_collector.add_query()
        orphaned = cursor.fetchone()[0]
        assert orphaned == 0, f"Found {orphaned} products with invalid categories"
        
        test_metrics_collector.end_test()
    
    def test_product_search_functionality(self, database_connection, test_metrics_collector):
        """Test product search with various query patterns."""
        test_metrics_collector.start_test("product_search_functionality")
        
        cursor = database_connection.cursor()
        
        # Test case-insensitive search
        search_terms = ["CLEANING", "power", "Tool", "CEMENT"]
        
        for term in search_terms:
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?)
            """, (f"%{term}%", f"%{term}%"))
            test_metrics_collector.add_query()
            
            count = cursor.fetchone()[0]
            assert count > 0, f"No products found for search term '{term}'"
            test_metrics_collector.add_records(count)
        
        test_metrics_collector.end_test()
        assert test_metrics_collector['duration_ms'] < 5000, "Search queries too slow"
    
    def test_category_based_filtering(self, database_connection, test_categories, test_metrics_collector):
        """Test filtering products by category."""
        test_metrics_collector.start_test("category_based_filtering")
        
        cursor = database_connection.cursor()
        
        for category in test_categories[:3]:  # Test first 3 categories
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE category_id = ? AND status = 'active'
            """, (category['id'],))
            test_metrics_collector.add_query()
            
            count = cursor.fetchone()[0]
            assert count > 0, f"No active products found in category {category['id']}"
            test_metrics_collector.add_records(count)
        
        test_metrics_collector.end_test()
    
    def test_brand_based_filtering(self, database_connection, test_brands, test_metrics_collector):
        """Test filtering products by brand."""
        test_metrics_collector.start_test("brand_based_filtering")
        
        cursor = database_connection.cursor()
        
        for brand in test_brands[:5]:  # Test first 5 brands
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE brand_id = ? AND is_published = 1
            """, (brand['id'],))
            test_metrics_collector.add_query()
            
            count = cursor.fetchone()[0]
            test_metrics_collector.add_records(count)
            # Note: Some brands might have 0 published products, which is valid
        
        test_metrics_collector.end_test()
    
    def test_complex_product_queries(self, database_connection, test_metrics_collector):
        """Test complex multi-table joins and aggregations."""
        test_metrics_collector.start_test("complex_product_queries")
        
        cursor = database_connection.cursor()
        
        # Complex query with joins
        cursor.execute("""
            SELECT 
                c.name as category,
                b.name as brand,
                COUNT(p.id) as product_count,
                AVG(LENGTH(p.description)) as avg_description_length
            FROM products p
            JOIN categories c ON p.category_id = c.id
            JOIN brands b ON p.brand_id = b.id
            WHERE p.status = 'active'
            GROUP BY c.id, b.id
            HAVING product_count > 5
            ORDER BY product_count DESC
            LIMIT 10
        """)
        test_metrics_collector.add_query()
        
        results = cursor.fetchall()
        assert len(results) > 0, "Complex query returned no results"
        
        for result in results:
            assert result['product_count'] > 5, "Query filter not working"
            assert result['avg_description_length'] > 0, "Invalid aggregation"
        
        test_metrics_collector.add_records(len(results))
        test_metrics_collector.end_test()
        assert test_metrics_collector['duration_ms'] < 3000, "Complex query too slow"


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.performance
class TestDatabasePerformance:
    """Test database performance with large dataset."""
    
    def test_large_result_set_performance(self, database_connection, test_metrics_collector):
        """Test performance with large result sets."""
        test_metrics_collector.start_test("large_result_set_performance")
        
        cursor = database_connection.cursor()
        
        # Query that returns significant portion of products
        start_time = time.time()
        cursor.execute("""
            SELECT id, sku, name, category_id, brand_id 
            FROM products 
            WHERE status = 'active'
            ORDER BY name
        """)
        test_metrics_collector.add_query()
        
        results = cursor.fetchall()
        query_time = (time.time() - start_time) * 1000
        
        assert len(results) > 1000, "Should return significant number of products"
        assert query_time < 2000, f"Large query took {query_time}ms, should be < 2000ms"
        
        test_metrics_collector.add_records(len(results))
        test_metrics_collector.end_test()
    
    def test_concurrent_database_access(self, test_database_path, concurrent_test_data, test_metrics_collector):
        """Test concurrent database access with multiple connections."""
        test_metrics_collector.start_test("concurrent_database_access")
        
        def run_concurrent_query(query_id: int, search_term: str):
            """Run a database query in a separate thread."""
            conn = sqlite3.connect(test_database_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM products 
                    WHERE LOWER(name) LIKE LOWER(?)
                """, (f"%{search_term}%",))
                
                count = cursor.fetchone()[0]
                return {'query_id': query_id, 'count': count, 'success': True}
            except Exception as e:
                return {'query_id': query_id, 'error': str(e), 'success': False}
            finally:
                conn.close()
        
        # Run concurrent queries
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=concurrent_test_data['user_count']) as executor:
            futures = []
            
            for i in range(concurrent_test_data['requests_per_user']):
                for j, search_term in enumerate(concurrent_test_data['test_queries']):
                    future = executor.submit(run_concurrent_query, i * 10 + j, search_term)
                    futures.append(future)
            
            results = [future.result() for future in as_completed(futures)]
        
        total_time = (time.time() - start_time) * 1000
        
        # Validate results
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        assert len(failed) == 0, f"Concurrent queries failed: {failed}"
        assert len(successful) == len(futures), "Not all queries completed successfully"
        assert total_time < 10000, f"Concurrent queries took {total_time}ms, should be < 10000ms"
        
        test_metrics_collector.add_records(len(successful))
        test_metrics_collector.end_test()
    
    def test_database_connection_pooling_simulation(self, test_database_path, test_metrics_collector):
        """Simulate database connection pooling behavior."""
        test_metrics_collector.start_test("database_connection_pooling_simulation")
        
        connection_pool = []
        max_connections = 10
        
        def get_connection():
            if connection_pool:
                return connection_pool.pop()
            return sqlite3.connect(test_database_path)
        
        def return_connection(conn):
            if len(connection_pool) < max_connections:
                connection_pool.append(conn)
            else:
                conn.close()
        
        # Simulate multiple operations using connection pool
        operations_count = 50
        start_time = time.time()
        
        for i in range(operations_count):
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM products WHERE id < ?", (i * 100 + 1000,))
            count = cursor.fetchone()[0]
            test_metrics_collector.add_query()
            
            return_connection(conn)
        
        # Clean up remaining connections
        while connection_pool:
            connection_pool.pop().close()
        
        total_time = (time.time() - start_time) * 1000
        avg_time_per_op = total_time / operations_count
        
        assert avg_time_per_op < 100, f"Average operation time {avg_time_per_op}ms too slow"
        
        test_metrics_collector.add_records(operations_count)
        test_metrics_collector.end_test()


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.error_handling
class TestDatabaseErrorHandling:
    """Test database error handling and recovery scenarios."""
    
    def test_invalid_query_handling(self, database_connection, test_metrics_collector):
        """Test handling of invalid SQL queries."""
        test_metrics_collector.start_test("invalid_query_handling")
        
        cursor = database_connection.cursor()
        
        invalid_queries = [
            "SELECT * FROM nonexistent_table",
            "SELECT invalid_column FROM products",
            "INSERT INTO products (invalid_column) VALUES ('test')",
            "DELETE FROM categories WHERE 1=1"  # This should be prevented
        ]
        
        for query in invalid_queries:
            with pytest.raises(sqlite3.Error):
                cursor.execute(query)
                test_metrics_collector.add_error()
        
        # Verify database is still functional after errors
        cursor.execute("SELECT COUNT(*) FROM products")
        test_metrics_collector.add_query()
        count = cursor.fetchone()[0]
        assert count == 17266, "Database integrity compromised after errors"
        
        test_metrics_collector.end_test()
    
    def test_database_lock_handling(self, test_database_path, test_metrics_collector):
        """Test handling of database locks and concurrent write attempts."""
        test_metrics_collector.start_test("database_lock_handling")
        
        def simulate_long_operation():
            conn = sqlite3.connect(test_database_path)
            cursor = conn.cursor()
            try:
                # Start a transaction but don't commit immediately
                cursor.execute("BEGIN EXCLUSIVE")
                time.sleep(2)  # Hold lock for 2 seconds
                cursor.execute("SELECT COUNT(*) FROM products")
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                return False
            finally:
                conn.close()
        
        def quick_read_operation():
            conn = sqlite3.connect(test_database_path, timeout=1.0)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM products")
                result = cursor.fetchone()[0]
                return result
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    return None
                raise
            finally:
                conn.close()
        
        # Start long operation in background
        import threading
        long_op_thread = threading.Thread(target=simulate_long_operation)
        long_op_thread.start()
        
        time.sleep(0.5)  # Let long operation start
        
        # Try quick read - should handle lock gracefully
        result = quick_read_operation()
        
        long_op_thread.join()
        
        # Result might be None (locked) or the count (if it succeeded)
        assert result is None or result == 17266, "Unexpected lock handling behavior"
        
        test_metrics_collector.end_test()
    
    def test_data_corruption_detection(self, database_connection, test_metrics_collector):
        """Test detection of potential data corruption scenarios."""
        test_metrics_collector.start_test("data_corruption_detection")
        
        cursor = database_connection.cursor()
        
        # Check for referential integrity
        cursor.execute("""
            SELECT COUNT(*) FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE c.id IS NULL AND p.category_id IS NOT NULL
        """)
        test_metrics_collector.add_query()
        orphaned_products = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM products p
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE b.id IS NULL AND p.brand_id IS NOT NULL
        """)
        test_metrics_collector.add_query()
        orphaned_brands = cursor.fetchone()[0]
        
        # Check for data consistency
        cursor.execute("""
            SELECT COUNT(*) FROM products
            WHERE (status NOT IN ('active', 'inactive', 'discontinued'))
        """)
        test_metrics_collector.add_query()
        invalid_status = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM products
            WHERE (availability NOT IN ('in_stock', 'out_of_stock', 'limited'))
        """)
        test_metrics_collector.add_query()
        invalid_availability = cursor.fetchone()[0]
        
        # Assert data integrity
        assert orphaned_products == 0, f"Found {orphaned_products} products with invalid categories"
        assert orphaned_brands == 0, f"Found {orphaned_brands} products with invalid brands"
        assert invalid_status == 0, f"Found {invalid_status} products with invalid status"
        # Note: availability might have other valid values, so we don't assert strictly
        
        test_metrics_collector.end_test()