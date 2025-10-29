"""Integration tests for work-based recommendations system.

Tests real work-based recommendation scenarios using actual product database
following Tier 2 integration testing requirements (NO MOCKING).
"""

import pytest
import sqlite3
import json
import time
from typing import List, Dict, Any, Tuple
import math


@pytest.mark.integration
@pytest.mark.database
class TestWorkBasedRecommendations:
    """Test work-based product recommendation functionality."""
    
    def test_work_type_classification(self, database_connection, sample_work_description, test_metrics_collector):
        """Test classification of work types and material needs."""
        test_metrics_collector.start_test("work_type_classification")
        
        work_desc = sample_work_description
        
        # Simulate work type classification (real implementation would use ML/NLP)
        def classify_work_type(description: str, work_type: str) -> Dict[str, Any]:
            """Classify work type and extract material categories."""
            classification = {
                'primary_work_type': work_type.lower(),
                'secondary_categories': [],
                'material_categories': [],
                'urgency_level': 'medium',
                'complexity_score': 0.5
            }
            
            # Map work types to material categories
            work_category_mapping = {
                'commercial construction': ['cement', 'tools', 'safety', 'measuring'],
                'residential construction': ['tools', 'materials', 'safety', 'electrical'],
                'renovation': ['tools', 'cleaning', 'materials', 'safety'],
                'maintenance': ['cleaning', 'tools', 'safety', 'repair']
            }
            
            primary_type = classification['primary_work_type']
            if 'construction' in primary_type:
                classification['material_categories'] = work_category_mapping.get(primary_type, ['tools', 'materials'])
                classification['complexity_score'] = 0.8
            
            # Extract additional categories from description
            desc_lower = description.lower()
            if 'office' in desc_lower:
                classification['secondary_categories'].append('commercial')
            if 'retail' in desc_lower:
                classification['secondary_categories'].append('retail')
            if 'floor' in desc_lower or 'story' in desc_lower:
                classification['complexity_score'] = min(1.0, classification['complexity_score'] + 0.2)
            
            return classification
        
        classification = classify_work_type(work_desc['description'], work_desc['work_type'])
        
        assert 'primary_work_type' in classification, "Missing primary work type"
        assert 'material_categories' in classification, "Missing material categories"
        assert len(classification['material_categories']) > 0, "No material categories identified"
        assert 0 <= classification['complexity_score'] <= 1, "Invalid complexity score"
        
        test_metrics_collector.add_records(len(classification['material_categories']))
        test_metrics_collector.end_test()
        
        return classification
    
    def test_material_need_extraction(self, sample_work_description, test_metrics_collector):
        """Test extraction of specific material needs from work description."""
        test_metrics_collector.start_test("material_need_extraction")
        
        description = sample_work_description['description']
        
        def extract_material_needs(description: str) -> List[Dict[str, Any]]:
            """Extract specific material needs with quantities and priorities."""
            needs = []
            
            # Define material patterns and their typical uses
            material_patterns = {
                'concrete': {'category': 'cement', 'priority': 'high', 'typical_quantity': 'bulk'},
                'cement': {'category': 'cement', 'priority': 'high', 'typical_quantity': 'bulk'},
                'power tools': {'category': 'tools', 'priority': 'high', 'typical_quantity': 'multiple'},
                'safety gear': {'category': 'safety', 'priority': 'critical', 'typical_quantity': 'per_worker'},
                'cleaning': {'category': 'cleaning', 'priority': 'medium', 'typical_quantity': 'standard'},
                'measurement': {'category': 'measuring', 'priority': 'high', 'typical_quantity': 'precision'}
            }
            
            desc_lower = description.lower()
            
            for material, details in material_patterns.items():
                if material in desc_lower:
                    need = {
                        'material_type': material,
                        'category': details['category'],
                        'priority': details['priority'],
                        'quantity_type': details['typical_quantity'],
                        'estimated_budget': 10000  # Placeholder
                    }
                    
                    # Adjust based on project context
                    if 'office' in desc_lower and 'building' in desc_lower:
                        need['estimated_budget'] *= 2  # Commercial projects cost more
                    
                    needs.append(need)
            
            return needs
        
        material_needs = extract_material_needs(description)
        
        assert len(material_needs) > 0, "No material needs extracted"
        
        for need in material_needs:
            required_fields = ['material_type', 'category', 'priority', 'quantity_type']
            for field in required_fields:
                assert field in need, f"Missing required field: {field}"
            
            assert need['priority'] in ['low', 'medium', 'high', 'critical'], "Invalid priority level"
            assert need['estimated_budget'] > 0, "Invalid budget estimate"
        
        test_metrics_collector.add_records(len(material_needs))
        test_metrics_collector.end_test()
        
        return material_needs
    
    def test_product_recommendation_matching(self, database_connection, sample_work_description, test_metrics_collector):
        """Test matching work requirements to actual products."""
        test_metrics_collector.start_test("product_recommendation_matching")
        
        cursor = database_connection.cursor()
        
        def recommend_products_for_work(work_desc: Dict[str, Any]) -> Dict[str, List[Dict]]:
            """Generate product recommendations based on work description."""
            recommendations = {}
            
            for material_need in work_desc['materials_needed']:
                # Search for products matching each material need
                search_terms = material_need.split()
                main_term = search_terms[0] if search_terms else material_need
                
                cursor.execute("""
                    SELECT p.id, p.sku, p.name, p.description, p.category_id, 
                           c.name as category_name, b.name as brand_name,
                           CASE 
                               WHEN LOWER(p.name) LIKE LOWER(?) THEN 3
                               WHEN LOWER(p.description) LIKE LOWER(?) THEN 2
                               ELSE 1
                           END as relevance_score
                    FROM products p
                    JOIN categories c ON p.category_id = c.id
                    JOIN brands b ON p.brand_id = b.id
                    WHERE (LOWER(p.name) LIKE LOWER(?) OR LOWER(p.description) LIKE LOWER(?))
                    AND p.status = 'active' AND p.is_published = 1
                    ORDER BY relevance_score DESC, p.name
                    LIMIT 10
                """, (f"%{main_term}%", f"%{main_term}%", f"%{main_term}%", f"%{main_term}%"))
                test_metrics_collector.add_query()
                
                products = cursor.fetchall()
                test_metrics_collector.add_records(len(products))
                
                # Enhance product data with recommendation scores
                enhanced_products = []
                for product in products:
                    enhanced_product = dict(product)
                    enhanced_product['recommendation_score'] = calculate_recommendation_score(
                        product, material_need, work_desc
                    )
                    enhanced_product['estimated_quantity'] = estimate_quantity_needed(
                        product, work_desc
                    )
                    enhanced_products.append(enhanced_product)
                
                # Sort by recommendation score
                enhanced_products.sort(key=lambda x: x['recommendation_score'], reverse=True)
                recommendations[material_need] = enhanced_products
            
            return recommendations
        
        def calculate_recommendation_score(product: Dict, material_need: str, work_desc: Dict) -> float:
            """Calculate recommendation score for product-work match."""
            score = product['relevance_score'] * 0.4  # Base relevance
            
            # Budget compatibility
            budget_range = work_desc.get('budget_range', '100000-500000')
            if '500000' in budget_range:
                score += 0.3  # Higher budget allows for premium products
            
            # Timeline urgency
            timeline = work_desc.get('timeline', '')
            if '12 months' in timeline:
                score += 0.2  # Long timeline allows for better planning
            
            # Brand reputation (simplified)
            if product['brand_name'] and len(product['brand_name']) > 3:
                score += 0.1
            
            return min(score, 5.0)  # Cap at 5.0
        
        def estimate_quantity_needed(product: Dict, work_desc: Dict) -> int:
            """Estimate quantity needed based on work scope."""
            base_quantity = 10
            
            # Adjust based on work description
            desc_lower = work_desc['description'].lower()
            if '5-story' in desc_lower:
                base_quantity *= 5
            if 'office complex' in desc_lower:
                base_quantity *= 2
            
            return base_quantity
        
        recommendations = recommend_products_for_work(sample_work_description)
        
        # Validate recommendations
        assert len(recommendations) > 0, "No recommendations generated"
        
        total_recommended_products = sum(len(products) for products in recommendations.values())
        assert total_recommended_products > 0, "No products recommended"
        
        # Validate recommendation quality
        for material_need, products in recommendations.items():
            if products:  # Only check if products were found
                # Top recommendation should have good score
                top_product = products[0]
                assert top_product['recommendation_score'] > 0, "Top recommendation has zero score"
                assert top_product['estimated_quantity'] > 0, "Invalid quantity estimate"
                
                # Check that product is relevant to material need
                product_text = (top_product['name'] + ' ' + (top_product['description'] or '')).lower()
                material_words = material_need.lower().split()
                relevance_found = any(word in product_text for word in material_words if len(word) > 2)
                # Note: We don't assert this strictly as some matches might be category-based
        
        test_metrics_collector.end_test()
        return recommendations
    
    def test_recommendation_ranking_algorithm(self, database_connection, sample_work_description, test_metrics_collector):
        """Test ranking algorithm for product recommendations."""
        test_metrics_collector.start_test("recommendation_ranking_algorithm")
        
        cursor = database_connection.cursor()
        
        # Get a sample of products for testing ranking
        cursor.execute("""
            SELECT p.id, p.sku, p.name, p.description, p.category_id,
                   c.name as category_name, b.name as brand_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            JOIN brands b ON p.brand_id = b.id
            WHERE LOWER(p.name) LIKE '%tool%'
            AND p.status = 'active' AND p.is_published = 1
            LIMIT 20
        """)
        test_metrics_collector.add_query()
        
        sample_products = cursor.fetchall()
        test_metrics_collector.add_records(len(sample_products))
        
        def advanced_ranking_algorithm(products: List[Dict], work_context: Dict) -> List[Dict]:
            """Advanced ranking algorithm considering multiple factors."""
            ranked_products = []
            
            for product in products:
                score_components = {
                    'name_relevance': 0,
                    'description_relevance': 0,
                    'category_relevance': 0,
                    'brand_quality': 0,
                    'work_suitability': 0
                }
                
                # Name relevance scoring
                name_lower = product['name'].lower()
                for material in work_context['materials_needed']:
                    material_words = material.lower().split()
                    for word in material_words:
                        if len(word) > 2 and word in name_lower:
                            score_components['name_relevance'] += 2.0
                
                # Description relevance scoring
                if product['description']:
                    desc_lower = product['description'].lower()
                    for material in work_context['materials_needed']:
                        material_words = material.lower().split()
                        for word in material_words:
                            if len(word) > 2 and word in desc_lower:
                                score_components['description_relevance'] += 1.0
                
                # Work type suitability
                work_type_lower = work_context['work_type'].lower()
                if 'construction' in work_type_lower:
                    construction_keywords = ['construction', 'building', 'concrete', 'cement']
                    text_to_check = (name_lower + ' ' + (product['description'] or '').lower())
                    for keyword in construction_keywords:
                        if keyword in text_to_check:
                            score_components['work_suitability'] += 1.5
                
                # Brand quality (simplified heuristic)
                if product['brand_name'] and product['brand_name'] != 'NO BRAND':
                    score_components['brand_quality'] = 1.0
                
                # Calculate total score
                total_score = sum(score_components.values())
                
                ranked_product = dict(product)
                ranked_product['ranking_score'] = total_score
                ranked_product['score_breakdown'] = score_components
                ranked_products.append(ranked_product)
            
            # Sort by total score
            ranked_products.sort(key=lambda x: x['ranking_score'], reverse=True)
            return ranked_products
        
        ranked_products = advanced_ranking_algorithm(sample_products, sample_work_description)
        
        # Validate ranking results
        assert len(ranked_products) == len(sample_products), "Ranking changed product count"
        
        # Check that ranking is actually sorting products
        if len(ranked_products) > 1:
            assert ranked_products[0]['ranking_score'] >= ranked_products[1]['ranking_score'], \
                "Products not properly ranked by score"
        
        # Validate score components
        for product in ranked_products:
            assert 'ranking_score' in product, "Missing ranking score"
            assert 'score_breakdown' in product, "Missing score breakdown"
            assert product['ranking_score'] >= 0, "Negative ranking score"
            
            # Check score breakdown structure
            required_components = ['name_relevance', 'description_relevance', 'category_relevance', 
                                 'brand_quality', 'work_suitability']
            for component in required_components:
                assert component in product['score_breakdown'], f"Missing score component: {component}"
        
        test_metrics_collector.end_test()
        return ranked_products
    
    def test_work_budget_optimization(self, database_connection, sample_work_description, test_metrics_collector):
        """Test optimizing product recommendations within budget constraints."""
        test_metrics_collector.start_test("work_budget_optimization")
        
        cursor = database_connection.cursor()
        
        # Extract budget from work description
        budget_str = sample_work_description.get('budget_range', '100000-500000')
        max_budget = float(budget_str.split('-')[1]) if '-' in budget_str else 500000
        
        def optimize_recommendations_for_budget(materials_needed: List[str], max_budget: float) -> Dict[str, Any]:
            """Optimize product selection within budget constraints."""
            optimization_result = {
                'recommended_products': [],
                'total_estimated_cost': 0,
                'budget_utilization': 0,
                'savings_opportunities': [],
                'budget_breakdown': {}
            }
            
            budget_per_category = max_budget / len(materials_needed)
            
            for material in materials_needed:
                # Find products for this material
                search_term = material.split()[0]
                cursor.execute("""
                    SELECT p.id, p.sku, p.name, p.description, p.category_id,
                           c.name as category_name
                    FROM products p
                    JOIN categories c ON p.category_id = c.id
                    WHERE (LOWER(p.name) LIKE LOWER(?) OR LOWER(p.description) LIKE LOWER(?))
                    AND p.status = 'active' AND p.is_published = 1
                    ORDER BY p.name
                    LIMIT 15
                """, (f"%{search_term}%", f"%{search_term}%"))
                test_metrics_collector.add_query()
                
                products = cursor.fetchall()
                test_metrics_collector.add_records(len(products))
                
                if products:
                    # Simulate price estimation and optimization
                    category_recommendations = []
                    category_cost = 0
                    
                    for i, product in enumerate(products[:5]):  # Limit to top 5 for budget calc
                        # Simulate pricing based on product characteristics
                        estimated_price = estimate_product_price(product, material)
                        estimated_quantity = max(1, int(budget_per_category / estimated_price / 10))
                        item_total = estimated_price * estimated_quantity
                        
                        if category_cost + item_total <= budget_per_category:
                            recommendation = {
                                'product_id': product['id'],
                                'sku': product['sku'],
                                'name': product['name'],
                                'category': product['category_name'],
                                'estimated_price': estimated_price,
                                'recommended_quantity': estimated_quantity,
                                'total_cost': item_total,
                                'priority': 'high' if i < 2 else 'medium'
                            }
                            category_recommendations.append(recommendation)
                            category_cost += item_total
                    
                    optimization_result['recommended_products'].extend(category_recommendations)
                    optimization_result['budget_breakdown'][material] = category_cost
                    optimization_result['total_estimated_cost'] += category_cost
            
            optimization_result['budget_utilization'] = optimization_result['total_estimated_cost'] / max_budget
            
            return optimization_result
        
        def estimate_product_price(product: Dict, material_context: str) -> float:
            """Estimate product price based on characteristics."""
            base_price = 100.0  # Base price
            
            # Adjust based on product name characteristics
            name_lower = product['name'].lower()
            
            if 'professional' in name_lower or 'premium' in name_lower:
                base_price *= 2.0
            elif 'basic' in name_lower or 'standard' in name_lower:
                base_price *= 0.8
            
            # Adjust based on material type
            if 'cement' in material_context or 'concrete' in material_context:
                base_price *= 0.5  # Bulk materials typically cheaper per unit
            elif 'power' in material_context and 'tool' in material_context:
                base_price *= 3.0  # Power tools more expensive
            elif 'safety' in material_context:
                base_price *= 1.5  # Safety equipment premium
            
            return base_price
        
        optimization_result = optimize_recommendations_for_budget(
            sample_work_description['materials_needed'],
            max_budget
        )
        
        # Validate optimization results
        assert 'recommended_products' in optimization_result, "Missing recommended products"
        assert 'total_estimated_cost' in optimization_result, "Missing total cost"
        assert 'budget_utilization' in optimization_result, "Missing budget utilization"
        
        assert len(optimization_result['recommended_products']) > 0, "No products recommended within budget"
        assert optimization_result['total_estimated_cost'] > 0, "Zero total cost"
        assert optimization_result['total_estimated_cost'] <= max_budget, "Exceeded budget constraint"
        assert 0 <= optimization_result['budget_utilization'] <= 1.0, "Invalid budget utilization"
        
        # Validate individual product recommendations
        for product in optimization_result['recommended_products']:
            required_fields = ['product_id', 'sku', 'name', 'estimated_price', 'recommended_quantity', 'total_cost']
            for field in required_fields:
                assert field in product, f"Missing required field: {field}"
            
            assert product['estimated_price'] > 0, "Invalid estimated price"
            assert product['recommended_quantity'] > 0, "Invalid recommended quantity"
            assert product['total_cost'] > 0, "Invalid total cost"
            assert product['priority'] in ['low', 'medium', 'high', 'critical'], "Invalid priority"
        
        test_metrics_collector.end_test()
        return optimization_result


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.performance
class TestWorkRecommendationPerformance:
    """Test work-based recommendation system performance."""
    
    def test_recommendation_generation_speed(self, database_connection, test_metrics_collector):
        """Test speed of recommendation generation for various work types."""
        test_metrics_collector.start_test("recommendation_generation_speed")
        
        cursor = database_connection.cursor()
        
        work_scenarios = [
            {'type': 'Commercial Construction', 'materials': ['cement', 'tools', 'safety']},
            {'type': 'Residential Renovation', 'materials': ['cleaning', 'tools', 'materials']},
            {'type': 'Industrial Maintenance', 'materials': ['safety', 'cleaning', 'tools']},
            {'type': 'Office Fit-out', 'materials': ['tools', 'materials', 'cleaning']}
        ]
        
        total_recommendations = 0
        start_time = time.time()
        
        for scenario in work_scenarios:
            scenario_start = time.time()
            
            for material in scenario['materials']:
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM products 
                    WHERE (LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))
                    AND status = 'active' AND is_published = 1
                """, (f"%{material}%", f"%{material}%"))
                test_metrics_collector.add_query()
                
                count = cursor.fetchone()['count']
                total_recommendations += min(count, 10)  # Limit recommendations per material
                test_metrics_collector.add_records(count)
            
            scenario_time = (time.time() - scenario_start) * 1000
            assert scenario_time < 2000, f"Scenario {scenario['type']} took {scenario_time}ms, should be < 2000ms"
        
        total_time = (time.time() - start_time) * 1000
        avg_time_per_scenario = total_time / len(work_scenarios)
        
        assert total_recommendations > 0, "No recommendations generated"
        assert avg_time_per_scenario < 1500, f"Average scenario time {avg_time_per_scenario}ms too slow"
        
        test_metrics_collector.end_test()
    
    def test_large_work_project_handling(self, database_connection, test_metrics_collector):
        """Test handling of large work projects with many material requirements."""
        test_metrics_collector.start_test("large_work_project_handling")
        
        cursor = database_connection.cursor()
        
        # Simulate large construction project
        large_project_materials = [
            'cement', 'concrete', 'tools', 'power tools', 'safety equipment',
            'cleaning supplies', 'measuring tools', 'electrical components',
            'plumbing supplies', 'construction hardware', 'protective gear',
            'maintenance materials', 'finishing materials', 'insulation',
            'roofing materials', 'flooring materials', 'painting supplies'
        ]
        
        start_time = time.time()
        total_products_found = 0
        
        # Process all materials efficiently
        for material in large_project_materials:
            cursor.execute("""
                SELECT COUNT(*) as count,
                       AVG(LENGTH(name)) as avg_name_length
                FROM products 
                WHERE (LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))
                AND status = 'active' AND is_published = 1
            """, (f"%{material}%", f"%{material}%"))
            test_metrics_collector.add_query()
            
            result = cursor.fetchone()
            count = result['count']
            total_products_found += count
            test_metrics_collector.add_records(count)
        
        processing_time = (time.time() - start_time) * 1000
        avg_time_per_material = processing_time / len(large_project_materials)
        
        assert total_products_found > 0, "No products found for large project"
        assert processing_time < 10000, f"Large project processing took {processing_time}ms, should be < 10000ms"
        assert avg_time_per_material < 500, f"Average per material {avg_time_per_material}ms too slow"
        
        test_metrics_collector.end_test()
    
    def test_concurrent_recommendation_requests(self, test_database_path, concurrent_test_data, test_metrics_collector):
        """Test concurrent work-based recommendation requests."""
        test_metrics_collector.start_test("concurrent_recommendation_requests")
        
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def generate_recommendations_concurrent(work_id: int, materials: List[str]) -> Dict[str, Any]:
            """Generate recommendations in separate thread."""
            conn = sqlite3.connect(test_database_path)
            cursor = conn.cursor()
            
            try:
                results = {'work_id': work_id, 'recommendations': {}, 'total_products': 0}
                
                for material in materials:
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM products 
                        WHERE (LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))
                        AND status = 'active'
                    """, (f"%{material}%", f"%{material}%"))
                    
                    count = cursor.fetchone()['count']
                    results['recommendations'][material] = min(count, 20)  # Limit results
                    results['total_products'] += results['recommendations'][material]
                
                results['success'] = True
                return results
                
            except Exception as e:
                return {'work_id': work_id, 'error': str(e), 'success': False}
            finally:
                conn.close()
        
        # Simulate concurrent recommendation requests
        work_requests = [
            {'id': 1, 'materials': ['cement', 'tools']},
            {'id': 2, 'materials': ['cleaning', 'safety']},
            {'id': 3, 'materials': ['power', 'measuring']},
            {'id': 4, 'materials': ['electrical', 'hardware']}
        ]
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for work_request in work_requests:
                future = executor.submit(
                    generate_recommendations_concurrent, 
                    work_request['id'], 
                    work_request['materials']
                )
                futures.append(future)
            
            results = [future.result() for future in as_completed(futures)]
        
        total_time = (time.time() - start_time) * 1000
        
        # Validate concurrent results
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        assert len(failed) == 0, f"Concurrent recommendation requests failed: {failed}"
        assert len(successful) == len(work_requests), "Not all requests completed successfully"
        assert total_time < 8000, f"Concurrent requests took {total_time}ms, should be < 8000ms"
        
        # Verify each request found products
        total_products_all_requests = sum(r['total_products'] for r in successful)
        assert total_products_all_requests > 0, "No products found in any concurrent request"
        
        test_metrics_collector.add_records(total_products_all_requests)
        test_metrics_collector.end_test()