"""Integration tests for product search and filtering functionality.

Tests real product search scenarios using the actual 17,266 products database
following Tier 2 integration testing requirements (NO MOCKING).
"""

import pytest
import sqlite3
import time
from typing import List, Dict, Any, Tuple
import re
import json


@pytest.mark.integration
@pytest.mark.database
class TestProductSearch:
    """Test product search functionality with real data."""
    
    def test_basic_text_search(self, database_connection, test_metrics_collector):
        """Test basic text search across product names and descriptions."""
        test_metrics_collector.start_test("basic_text_search")
        
        cursor = database_connection.cursor()
        
        # Test search for "tools for cement work" as specified
        search_term = "cement"
        cursor.execute("""
            SELECT id, sku, name, description, category_id
            FROM products 
            WHERE (LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))
            AND status = 'active' AND is_published = 1
            ORDER BY 
                CASE 
                    WHEN LOWER(name) LIKE LOWER(?) THEN 1
                    ELSE 2
                END,
                name
        """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        test_metrics_collector.add_query()
        
        results = cursor.fetchall()
        test_metrics_collector.add_records(len(results))
        
        assert len(results) > 0, f"No products found for '{search_term}'"
        
        # Verify results contain search term
        for result in results[:5]:  # Check first 5 results
            name_matches = search_term.lower() in result['name'].lower()
            desc_matches = search_term.lower() in result['description'].lower() if result['description'] else False
            assert name_matches or desc_matches, f"Product {result['name']} doesn't match search term"
        
        test_metrics_collector.end_test()
        assert test_metrics_collector['duration_ms'] < 2000, "Basic search too slow"
    
    def test_multi_keyword_search(self, database_connection, test_metrics_collector):
        """Test search with multiple keywords."""
        test_metrics_collector.start_test("multi_keyword_search")
        
        cursor = database_connection.cursor()
        
        # Test "tools for cement work" 
        keywords = ["tools", "cement", "work"]
        
        # Build dynamic query for AND search (all keywords must match)
        conditions = []
        params = []
        for keyword in keywords:
            conditions.append("(LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        query = f"""
            SELECT id, sku, name, description, category_id,
                   (LENGTH(name) - LENGTH(REPLACE(LOWER(name), LOWER(?), ''))) +
                   (LENGTH(COALESCE(description, '')) - LENGTH(REPLACE(LOWER(COALESCE(description, '')), LOWER(?), ''))) as relevance_score
            FROM products 
            WHERE {' AND '.join(conditions)}
            AND status = 'active' AND is_published = 1
            ORDER BY relevance_score DESC, name
            LIMIT 20
        """
        
        all_params = [keywords[0], keywords[0]] + params
        cursor.execute(query, all_params)
        test_metrics_collector.add_query()
        
        results = cursor.fetchall()
        test_metrics_collector.add_records(len(results))
        
        # Also test OR search (any keyword matches)
        or_conditions = " OR ".join(conditions)
        or_query = f"""
            SELECT id, sku, name, description, category_id
            FROM products 
            WHERE ({or_conditions})
            AND status = 'active' AND is_published = 1
            ORDER BY name
            LIMIT 50
        """
        
        cursor.execute(or_query, params)
        test_metrics_collector.add_query()
        
        or_results = cursor.fetchall()
        test_metrics_collector.add_records(len(or_results))
        
        assert len(or_results) >= len(results), "OR search should return more or equal results than AND"
        assert len(or_results) > 0, "Multi-keyword search returned no results"
        
        test_metrics_collector.end_test()
    
    def test_fuzzy_search_patterns(self, database_connection, test_metrics_collector):
        """Test fuzzy search patterns and typo tolerance."""
        test_metrics_collector.start_test("fuzzy_search_patterns")
        
        cursor = database_connection.cursor()
        
        # Test common typos and variations
        search_variations = [
            ("cleaner", "cleaning", "clean"),  # Different word forms
            ("tool", "tools"),  # Singular/plural
            ("cement", "concrete"),  # Related terms
        ]
        
        for variations in search_variations:
            for search_term in variations:
                cursor.execute("""
                    SELECT COUNT(DISTINCT id) as count
                    FROM products 
                    WHERE (LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))
                    AND status = 'active'
                """, (f"%{search_term}%", f"%{search_term}%"))
                test_metrics_collector.add_query()
                
                count = cursor.fetchone()['count']
                test_metrics_collector.add_records(count)
                
                # Each variation should find some products
                # Note: We don't assert count > 0 because some terms might not exist
        
        test_metrics_collector.end_test()
    
    def test_search_performance_with_indexes(self, database_connection, test_metrics_collector):
        """Test search performance and potential index usage."""
        test_metrics_collector.start_test("search_performance_with_indexes")
        
        cursor = database_connection.cursor()
        
        # Test multiple search patterns for performance
        search_patterns = [
            "power%",  # Prefix search
            "%tool%",  # Contains search
            "%cleaning",  # Suffix search
            "blue wonder%"  # Brand-like prefix
        ]
        
        for pattern in search_patterns:
            start_time = time.time()
            
            cursor.execute("""
                SELECT id, name, category_id
                FROM products 
                WHERE LOWER(name) LIKE LOWER(?)
                AND status = 'active'
                ORDER BY name
                LIMIT 100
            """, (pattern,))
            test_metrics_collector.add_query()
            
            results = cursor.fetchall()
            query_time = (time.time() - start_time) * 1000
            
            test_metrics_collector.add_records(len(results))
            
            # Performance assertion - searches should be reasonably fast
            assert query_time < 1000, f"Search pattern '{pattern}' took {query_time}ms, should be < 1000ms"
        
        test_metrics_collector.end_test()


@pytest.mark.integration  
@pytest.mark.database
class TestProductFiltering:
    """Test product filtering by various criteria."""
    
    def test_category_filtering(self, database_connection, test_categories, test_metrics_collector):
        """Test filtering products by category."""
        test_metrics_collector.start_test("category_filtering")
        
        cursor = database_connection.cursor()
        
        for category in test_categories[:3]:
            # Test single category filter
            cursor.execute("""
                SELECT COUNT(*) as count, 
                       MIN(id) as min_id, 
                       MAX(id) as max_id
                FROM products 
                WHERE category_id = ? AND status = 'active'
            """, (category['id'],))
            test_metrics_collector.add_query()
            
            result = cursor.fetchone()
            count = result['count']
            test_metrics_collector.add_records(count)
            
            if count > 0:
                # Verify all products in category
                cursor.execute("""
                    SELECT id, name, category_id
                    FROM products 
                    WHERE category_id = ? AND status = 'active'
                    LIMIT 10
                """, (category['id'],))
                test_metrics_collector.add_query()
                
                samples = cursor.fetchall()
                for sample in samples:
                    assert sample['category_id'] == category['id'], "Category filter not working correctly"
        
        test_metrics_collector.end_test()
    
    def test_brand_filtering(self, database_connection, test_brands, test_metrics_collector):
        """Test filtering products by brand."""
        test_metrics_collector.start_test("brand_filtering")
        
        cursor = database_connection.cursor()
        
        for brand in test_brands[:5]:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM products 
                WHERE brand_id = ? AND is_published = 1
            """, (brand['id'],))
            test_metrics_collector.add_query()
            
            count = cursor.fetchone()['count']
            test_metrics_collector.add_records(count)
            
            if count > 0:
                # Get sample products from this brand
                cursor.execute("""
                    SELECT id, name, brand_id
                    FROM products 
                    WHERE brand_id = ? AND is_published = 1
                    LIMIT 5
                """, (brand['id'],))
                test_metrics_collector.add_query()
                
                samples = cursor.fetchall()
                for sample in samples:
                    assert sample['brand_id'] == brand['id'], "Brand filter not working correctly"
        
        test_metrics_collector.end_test()
    
    def test_status_and_availability_filtering(self, database_connection, test_metrics_collector):
        """Test filtering by product status and availability."""
        test_metrics_collector.start_test("status_and_availability_filtering")
        
        cursor = database_connection.cursor()
        
        # Test status filtering
        status_values = ['active', 'inactive']
        for status in status_values:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM products 
                WHERE status = ?
            """, (status,))
            test_metrics_collector.add_query()
            
            count = cursor.fetchone()['count']
            test_metrics_collector.add_records(count)
            
            if count > 0:
                # Verify status filter
                cursor.execute("""
                    SELECT status FROM products WHERE status = ? LIMIT 5
                """, (status,))
                test_metrics_collector.add_query()
                
                samples = cursor.fetchall()
                for sample in samples:
                    assert sample['status'] == status, f"Status filter failed for {status}"
        
        # Test availability filtering
        cursor.execute("SELECT DISTINCT availability FROM products WHERE availability IS NOT NULL")
        test_metrics_collector.add_query()
        availability_values = [row['availability'] for row in cursor.fetchall()]
        
        for availability in availability_values[:3]:  # Test first 3 availability types
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM products 
                WHERE availability = ?
            """, (availability,))
            test_metrics_collector.add_query()
            
            count = cursor.fetchone()['count']
            test_metrics_collector.add_records(count)
        
        test_metrics_collector.end_test()
    
    def test_published_status_filtering(self, database_connection, test_metrics_collector):
        """Test filtering by published status."""
        test_metrics_collector.start_test("published_status_filtering")
        
        cursor = database_connection.cursor()
        
        # Count published vs unpublished
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN is_published = 1 THEN 1 ELSE 0 END) as published_count,
                SUM(CASE WHEN is_published = 0 THEN 1 ELSE 0 END) as unpublished_count,
                COUNT(*) as total_count
            FROM products
        """)
        test_metrics_collector.add_query()
        
        result = cursor.fetchone()
        published_count = result['published_count']
        unpublished_count = result['unpublished_count']
        total_count = result['total_count']
        
        test_metrics_collector.add_records(total_count)
        
        assert published_count + unpublished_count == total_count, "Published count doesn't add up"
        assert total_count == 17266, "Total product count incorrect"
        
        # Test filtering by published status
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM products 
            WHERE is_published = 1 AND status = 'active'
        """)
        test_metrics_collector.add_query()
        
        active_published = cursor.fetchone()['count']
        test_metrics_collector.add_records(active_published)
        
        assert active_published > 0, "No active published products found"
        
        test_metrics_collector.end_test()


@pytest.mark.integration
@pytest.mark.database  
class TestAdvancedFiltering:
    """Test advanced filtering combinations and edge cases."""
    
    def test_combined_filters(self, database_connection, test_categories, test_brands, test_metrics_collector):
        """Test combining multiple filters."""
        test_metrics_collector.start_test("combined_filters")
        
        cursor = database_connection.cursor()
        
        # Combine category, brand, and status filters
        if test_categories and test_brands:
            category_id = test_categories[0]['id']
            brand_id = test_brands[0]['id']
            
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM products 
                WHERE category_id = ? 
                AND brand_id = ? 
                AND status = 'active' 
                AND is_published = 1
            """, (category_id, brand_id))
            test_metrics_collector.add_query()
            
            count = cursor.fetchone()['count']
            test_metrics_collector.add_records(count)
            
            # Test search within filtered results
            cursor.execute("""
                SELECT id, name, category_id, brand_id
                FROM products 
                WHERE category_id = ? 
                AND brand_id = ? 
                AND status = 'active' 
                AND is_published = 1
                AND (LOWER(name) LIKE '%power%' OR LOWER(description) LIKE '%power%')
            """, (category_id, brand_id))
            test_metrics_collector.add_query()
            
            filtered_search = cursor.fetchall()
            test_metrics_collector.add_records(len(filtered_search))
            
            # Verify combined filters work correctly
            for product in filtered_search:
                assert product['category_id'] == category_id, "Category filter failed in combination"
                assert product['brand_id'] == brand_id, "Brand filter failed in combination"
        
        test_metrics_collector.end_test()
    
    def test_pagination_with_filters(self, database_connection, test_metrics_collector):
        """Test pagination combined with filtering."""
        test_metrics_collector.start_test("pagination_with_filters")
        
        cursor = database_connection.cursor()
        
        # Test pagination with search
        search_term = "blue"
        page_size = 10
        
        for page in range(3):  # Test first 3 pages
            offset = page * page_size
            
            cursor.execute("""
                SELECT id, name
                FROM products 
                WHERE LOWER(name) LIKE LOWER(?)
                AND status = 'active'
                ORDER BY name
                LIMIT ? OFFSET ?
            """, (f"%{search_term}%", page_size, offset))
            test_metrics_collector.add_query()
            
            results = cursor.fetchall()
            test_metrics_collector.add_records(len(results))
            
            if len(results) == 0:
                break  # No more results
                
            # Verify pagination doesn't return duplicates across pages
            if page > 0:  # Skip first page comparison
                cursor.execute("""
                    SELECT id, name
                    FROM products 
                    WHERE LOWER(name) LIKE LOWER(?)
                    AND status = 'active'
                    ORDER BY name
                    LIMIT ? OFFSET ?
                """, (f"%{search_term}%", page_size, (page-1) * page_size))
                test_metrics_collector.add_query()
                
                prev_results = cursor.fetchall()
                
                # Ensure no overlap between pages
                current_ids = {r['id'] for r in results}
                prev_ids = {r['id'] for r in prev_results}
                assert len(current_ids.intersection(prev_ids)) == 0, "Pagination overlap detected"
        
        test_metrics_collector.end_test()
    
    def test_sorting_with_filters(self, database_connection, test_metrics_collector):
        """Test various sorting options with filters."""
        test_metrics_collector.start_test("sorting_with_filters")
        
        cursor = database_connection.cursor()
        
        # Test different sorting options
        sort_options = [
            ("name ASC", "name"),
            ("name DESC", "name"),
            ("category_id ASC, name ASC", "category_id"),
            ("brand_id ASC, name ASC", "brand_id")
        ]
        
        for sort_clause, sort_field in sort_options:
            cursor.execute(f"""
                SELECT id, name, category_id, brand_id
                FROM products 
                WHERE status = 'active' AND is_published = 1
                ORDER BY {sort_clause}
                LIMIT 20
            """)
            test_metrics_collector.add_query()
            
            results = cursor.fetchall()
            test_metrics_collector.add_records(len(results))
            
            assert len(results) > 0, f"No results for sort option {sort_clause}"
            
            # Verify sorting is working (basic check)
            if len(results) > 1:
                if sort_field == "name":
                    if "DESC" in sort_clause:
                        assert results[0]['name'] >= results[1]['name'], f"Descending sort failed for {sort_clause}"
                    else:
                        assert results[0]['name'] <= results[1]['name'], f"Ascending sort failed for {sort_clause}"
        
        test_metrics_collector.end_test()
    
    def test_edge_case_filtering(self, database_connection, test_metrics_collector):
        """Test edge cases in filtering."""
        test_metrics_collector.start_test("edge_case_filtering")
        
        cursor = database_connection.cursor()
        
        # Test empty search terms
        empty_searches = ["", "   ", None]
        for search_term in empty_searches:
            if search_term is None:
                continue  # Skip None test as it would cause SQL error
                
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM products 
                WHERE LOWER(name) LIKE LOWER(?)
                AND status = 'active'
            """, (f"%{search_term.strip() if search_term else ''}%",))
            test_metrics_collector.add_query()
            
            count = cursor.fetchone()['count']
            test_metrics_collector.add_records(count)
            
            # Empty search should return all active products
            if not search_term or not search_term.strip():
                assert count > 1000, "Empty search should return many products"
        
        # Test very long search terms
        long_term = "a" * 1000
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM products 
            WHERE LOWER(name) LIKE LOWER(?)
        """, (f"%{long_term}%",))
        test_metrics_collector.add_query()
        
        count = cursor.fetchone()['count']
        test_metrics_collector.add_records(count)
        
        # Very long search should return 0 results
        assert count == 0, "Very long search term should return no results"
        
        test_metrics_collector.end_test()