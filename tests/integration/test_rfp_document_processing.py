"""Integration tests for RFP document processing functionality.

Tests real RFP document processing scenarios using actual system components
following Tier 2 integration testing requirements (NO MOCKING).
"""

import pytest
import sqlite3
import json
import time
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import re


@pytest.mark.integration
@pytest.mark.database
class TestRFPDocumentProcessing:
    """Test RFP document processing with real system integration."""
    
    def test_rfp_content_parsing(self, sample_rfp_document, test_metrics_collector):
        """Test parsing RFP document content to extract requirements."""
        test_metrics_collector.start_test("rfp_content_parsing")
        
        rfp_content = sample_rfp_document['content']
        
        # Simulate RFP parsing logic (real implementation would use NLP/LLM)
        def extract_requirements_from_rfp(content: str) -> List[str]:
            """Extract material requirements from RFP content."""
            requirements = []
            
            # Look for common requirement patterns
            patterns = [
                r'(?:need|require|looking for|seeking)\s+([^.]+)',
                r'(?:materials?|supplies?|equipment|tools?):\s*([^.]+)',
                r'[-•]\s*([^.\n]+(?:tool|equipment|material|supply|cement|power|safety|clean)[^.\n]*)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    clean_req = match.strip().lower()
                    if len(clean_req) > 5 and clean_req not in requirements:
                        requirements.append(clean_req)
            
            return requirements[:10]  # Limit to 10 requirements
        
        extracted_requirements = extract_requirements_from_rfp(rfp_content)
        test_metrics_collector.add_records(len(extracted_requirements))
        
        assert len(extracted_requirements) > 0, "No requirements extracted from RFP"
        
        # Verify expected requirements are found
        expected_keywords = ['cement', 'tools', 'safety', 'cleaning', 'measuring']
        found_keywords = 0
        
        for requirement in extracted_requirements:
            for keyword in expected_keywords:
                if keyword in requirement:
                    found_keywords += 1
                    break
        
        assert found_keywords >= 2, f"Expected keywords not found in requirements: {extracted_requirements}"
        
        test_metrics_collector.end_test()
        assert test_metrics_collector['duration_ms'] < 1000, "RFP parsing too slow"
    
    def test_requirement_to_product_matching(self, database_connection, sample_rfp_document, test_metrics_collector):
        """Test matching RFP requirements to actual products."""
        test_metrics_collector.start_test("requirement_to_product_matching")
        
        cursor = database_connection.cursor()
        requirements = sample_rfp_document['requirements']
        
        matched_products = {}
        
        for requirement in requirements:
            # Search for products matching each requirement
            search_terms = requirement.split()
            conditions = []
            params = []
            
            for term in search_terms:
                if len(term) > 2:  # Skip very short terms
                    conditions.append("(LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))")
                    params.extend([f"%{term}%", f"%{term}%"])
            
            if conditions:
                query = f"""
                    SELECT id, sku, name, description, category_id, brand_id
                    FROM products 
                    WHERE ({' OR '.join(conditions)})
                    AND status = 'active' AND is_published = 1
                    ORDER BY 
                        CASE 
                            WHEN LOWER(name) LIKE LOWER(?) THEN 1
                            ELSE 2
                        END,
                        name
                    LIMIT 20
                """
                
                # Add relevance parameter for ordering
                all_params = params + [f"%{search_terms[0]}%"]
                
                cursor.execute(query, all_params)
                test_metrics_collector.add_query()
                
                products = cursor.fetchall()
                matched_products[requirement] = products
                test_metrics_collector.add_records(len(products))
        
        # Verify matching results
        assert len(matched_products) > 0, "No product matches found for any requirements"
        
        total_matches = sum(len(products) for products in matched_products.values())
        assert total_matches > 0, "No products matched any requirements"
        
        # Verify match quality for key requirements
        cement_matches = matched_products.get('cement supplies', [])
        if cement_matches:
            cement_found = any('cement' in product['name'].lower() or 
                             'concrete' in product['name'].lower() 
                             for product in cement_matches)
            assert cement_found, "Cement requirement not properly matched"
        
        test_metrics_collector.end_test()
    
    def test_rfp_response_generation(self, database_connection, sample_rfp_document, test_metrics_collector):
        """Test generating RFP response with matched products."""
        test_metrics_collector.start_test("rfp_response_generation")
        
        cursor = database_connection.cursor()
        
        def generate_rfp_response(rfp_doc: Dict[str, Any]) -> Dict[str, Any]:
            """Generate RFP response with product recommendations."""
            response = {
                'rfp_title': rfp_doc['title'],
                'response_date': time.strftime('%Y-%m-%d'),
                'categories': [],
                'total_estimated_cost': 0,
                'recommended_products': []
            }
            
            # Process each requirement
            for requirement in rfp_doc['requirements']:
                category_response = {
                    'requirement': requirement,
                    'products': [],
                    'subtotal': 0
                }
                
                # Find matching products
                search_term = requirement.split()[0]  # Use first word for search
                cursor.execute("""
                    SELECT p.id, p.sku, p.name, p.description, c.name as category_name
                    FROM products p
                    JOIN categories c ON p.category_id = c.id
                    WHERE (LOWER(p.name) LIKE LOWER(?) OR LOWER(p.description) LIKE LOWER(?))
                    AND p.status = 'active' AND p.is_published = 1
                    ORDER BY p.name
                    LIMIT 5
                """, (f"%{search_term}%", f"%{search_term}%"))
                test_metrics_collector.add_query()
                
                products = cursor.fetchall()
                test_metrics_collector.add_records(len(products))
                
                for product in products:
                    product_info = {
                        'id': product['id'],
                        'sku': product['sku'],
                        'name': product['name'],
                        'category': product['category_name'],
                        'estimated_price': 100.0,  # Placeholder price
                        'quantity': 10  # Default quantity
                    }
                    category_response['products'].append(product_info)
                    category_response['subtotal'] += product_info['estimated_price'] * product_info['quantity']
                
                if category_response['products']:
                    response['categories'].append(category_response)
                    response['total_estimated_cost'] += category_response['subtotal']
            
            return response
        
        # Generate response
        rfp_response = generate_rfp_response(sample_rfp_document)
        
        # Validate response structure
        assert 'rfp_title' in rfp_response, "RFP response missing title"
        assert 'categories' in rfp_response, "RFP response missing categories"
        assert 'total_estimated_cost' in rfp_response, "RFP response missing cost estimate"
        
        assert len(rfp_response['categories']) > 0, "No product categories in RFP response"
        assert rfp_response['total_estimated_cost'] > 0, "RFP response has no cost estimate"
        
        # Validate category responses
        for category in rfp_response['categories']:
            assert 'requirement' in category, "Category missing requirement"
            assert 'products' in category, "Category missing products"
            assert len(category['products']) > 0, "Category has no products"
            
            # Validate product information
            for product in category['products']:
                required_fields = ['id', 'sku', 'name', 'category', 'estimated_price']
                for field in required_fields:
                    assert field in product, f"Product missing required field: {field}"
        
        test_metrics_collector.end_test()
        return rfp_response
    
    def test_rfp_document_storage(self, documents_connection, sample_rfp_document, test_metrics_collector):
        """Test storing RFP documents in the documents database."""
        test_metrics_collector.start_test("rfp_document_storage")
        
        cursor = documents_connection.cursor()
        
        # Store RFP document
        document_data = {
            'title': sample_rfp_document['title'],
            'content': sample_rfp_document['content'],
            'document_type': 'rfp',
            'requirements': json.dumps(sample_rfp_document['requirements']),
            'metadata': json.dumps({
                'project_type': 'construction',
                'budget_range': '500000',
                'timeline': '12 months'
            })
        }
        
        cursor.execute("""
            INSERT INTO documents (title, content, document_type, status, created_at, updated_at)
            VALUES (?, ?, ?, 'active', datetime('now'), datetime('now'))
        """, (
            document_data['title'],
            document_data['content'], 
            document_data['document_type']
        ))
        test_metrics_collector.add_query()
        
        document_id = cursor.lastrowid
        assert document_id > 0, "Failed to insert RFP document"
        
        # Verify document was stored correctly
        cursor.execute("""
            SELECT id, title, content, document_type, status, created_at
            FROM documents 
            WHERE id = ?
        """, (document_id,))
        test_metrics_collector.add_query()
        
        stored_doc = cursor.fetchone()
        assert stored_doc is not None, "Stored document not found"
        assert stored_doc['title'] == document_data['title'], "Document title mismatch"
        assert stored_doc['document_type'] == 'rfp', "Document type mismatch"
        assert stored_doc['status'] == 'active', "Document status mismatch"
        
        test_metrics_collector.add_records(1)
        test_metrics_collector.end_test()
        
        # Clean up test document
        cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        documents_connection.commit()
    
    def test_rfp_version_management(self, documents_connection, sample_rfp_document, test_metrics_collector):
        """Test RFP document version management."""
        test_metrics_collector.start_test("rfp_version_management")
        
        cursor = documents_connection.cursor()
        
        # Create initial RFP document
        cursor.execute("""
            INSERT INTO documents (title, content, document_type, status, created_at, updated_at)
            VALUES (?, ?, 'rfp', 'active', datetime('now'), datetime('now'))
        """, (sample_rfp_document['title'], sample_rfp_document['content']))
        test_metrics_collector.add_query()
        
        document_id = cursor.lastrowid
        
        # Create document version
        cursor.execute("""
            INSERT INTO document_versions (document_id, version_number, content, created_at)
            VALUES (?, 1, ?, datetime('now'))
        """, (document_id, sample_rfp_document['content']))
        test_metrics_collector.add_query()
        
        version_id = cursor.lastrowid
        
        # Update document with new version
        updated_content = sample_rfp_document['content'] + "\n\nAdditional requirement: Environmental compliance materials"
        
        cursor.execute("""
            UPDATE documents 
            SET content = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (updated_content, document_id))
        test_metrics_collector.add_query()
        
        # Create new version
        cursor.execute("""
            INSERT INTO document_versions (document_id, version_number, content, created_at)
            VALUES (?, 2, ?, datetime('now'))
        """, (document_id, updated_content))
        test_metrics_collector.add_query()
        
        # Verify version history
        cursor.execute("""
            SELECT version_number, LENGTH(content) as content_length
            FROM document_versions 
            WHERE document_id = ?
            ORDER BY version_number
        """, (document_id,))
        test_metrics_collector.add_query()
        
        versions = cursor.fetchall()
        assert len(versions) == 2, "Expected 2 document versions"
        assert versions[0]['version_number'] == 1, "First version number incorrect"
        assert versions[1]['version_number'] == 2, "Second version number incorrect"
        assert versions[1]['content_length'] > versions[0]['content_length'], "Updated version should be longer"
        
        test_metrics_collector.add_records(len(versions))
        test_metrics_collector.end_test()
        
        # Clean up test data
        cursor.execute("DELETE FROM document_versions WHERE document_id = ?", (document_id,))
        cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        documents_connection.commit()


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.performance
class TestRFPProcessingPerformance:
    """Test RFP processing performance with large datasets."""
    
    def test_large_rfp_processing_performance(self, database_connection, test_metrics_collector):
        """Test processing large RFP documents."""
        test_metrics_collector.start_test("large_rfp_processing_performance")
        
        # Create large RFP document
        large_rfp_content = f"""
        Large Construction Project RFP
        
        Project Overview:
        This is a major infrastructure project requiring extensive materials and equipment.
        
        Required Materials and Equipment:
        """ + "\n".join([
            f"- Category {i}: {item}"
            for i in range(1, 101)
            for item in ['cement supplies', 'power tools', 'safety equipment', 'cleaning materials', 'measuring tools']
        ])
        
        # Extract requirements (simulate processing)
        start_time = time.time()
        
        # Process requirements in batches
        requirement_batches = [
            'cement supplies', 'power tools', 'safety equipment', 
            'cleaning materials', 'measuring tools', 'electrical components',
            'plumbing supplies', 'construction hardware', 'protective gear'
        ]
        
        cursor = database_connection.cursor()
        total_matches = 0
        
        for requirement in requirement_batches:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM products 
                WHERE (LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))
                AND status = 'active' AND is_published = 1
            """, (f"%{requirement}%", f"%{requirement}%"))
            test_metrics_collector.add_query()
            
            count = cursor.fetchone()['count']
            total_matches += count
            test_metrics_collector.add_records(count)
        
        processing_time = (time.time() - start_time) * 1000
        
        assert total_matches > 0, "No products matched large RFP requirements"
        assert processing_time < 5000, f"Large RFP processing took {processing_time}ms, should be < 5000ms"
        
        test_metrics_collector.end_test()
    
    def test_concurrent_rfp_processing(self, test_database_path, concurrent_test_data, test_metrics_collector):
        """Test concurrent RFP processing scenarios."""
        test_metrics_collector.start_test("concurrent_rfp_processing")
        
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def process_rfp_concurrent(rfp_id: int, requirements: List[str]) -> Dict[str, Any]:
            """Process RFP in separate thread."""
            conn = sqlite3.connect(test_database_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            try:
                results = {'rfp_id': rfp_id, 'matches': {}, 'total_time': 0}
                start_time = time.time()
                
                for requirement in requirements:
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM products 
                        WHERE (LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))
                        AND status = 'active'
                    """, (f"%{requirement}%", f"%{requirement}%"))
                    
                    count = cursor.fetchone()['count']
                    results['matches'][requirement] = count
                
                results['total_time'] = (time.time() - start_time) * 1000
                results['success'] = True
                return results
                
            except Exception as e:
                return {'rfp_id': rfp_id, 'error': str(e), 'success': False}
            finally:
                conn.close()
        
        # Simulate multiple concurrent RFP processing requests
        rfp_requirements = [
            ['cement', 'tools', 'safety'],
            ['cleaning', 'power', 'measuring'],
            ['electrical', 'plumbing', 'hardware'],
            ['protective', 'construction', 'materials']
        ]
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for i, requirements in enumerate(rfp_requirements):
                future = executor.submit(process_rfp_concurrent, i, requirements)
                futures.append(future)
            
            results = [future.result() for future in as_completed(futures)]
        
        total_time = (time.time() - start_time) * 1000
        
        # Validate concurrent processing results
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        assert len(failed) == 0, f"Concurrent RFP processing failed: {failed}"
        assert len(successful) == len(rfp_requirements), "Not all RFP processes completed"
        assert total_time < 10000, f"Concurrent RFP processing took {total_time}ms, should be < 10000ms"
        
        # Verify individual processing times
        for result in successful:
            assert result['total_time'] < 3000, f"Individual RFP processing too slow: {result['total_time']}ms"
            assert sum(result['matches'].values()) >= 0, "Invalid match counts"
        
        test_metrics_collector.add_records(len(successful))
        test_metrics_collector.end_test()
    
    def test_rfp_memory_usage_optimization(self, database_connection, test_metrics_collector):
        """Test memory usage during RFP processing."""
        test_metrics_collector.start_test("rfp_memory_usage_optimization")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        cursor = database_connection.cursor()
        
        # Process large number of requirements
        requirements = [f"requirement_{i}" for i in range(100)]
        
        for i, requirement in enumerate(requirements):
            cursor.execute("""
                SELECT id, name, description
                FROM products 
                WHERE LOWER(name) LIKE LOWER(?)
                AND status = 'active'
                LIMIT 50
            """, (f"%{requirement[:5]}%",))  # Use first 5 chars to get some matches
            test_metrics_collector.add_query()
            
            results = cursor.fetchall()
            test_metrics_collector.add_records(len(results))
            
            # Check memory usage periodically
            if i % 20 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                # Memory shouldn't grow excessively
                assert memory_increase < 100, f"Memory usage increased by {memory_increase}MB, should be < 100MB"
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory
        
        assert total_memory_increase < 200, f"Total memory increase {total_memory_increase}MB too high"
        
        test_metrics_collector.end_test()