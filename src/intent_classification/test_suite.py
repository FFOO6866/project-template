"""
Comprehensive test suite for DIY intent classification system.
Tests classification accuracy, response time, and realistic customer queries.
"""

import asyncio
import json
import time
import pytest
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path
import requests
from unittest.mock import MagicMock, patch

# Import system components
from intent_classifier import DIYIntentClassificationSystem, ClassificationResult
from entity_extraction import DIYEntityExtractor, EntityType
from query_expansion import DIYQueryExpander
from training_data import DIYTrainingDataGenerator


class IntentClassificationTestSuite:
    """Comprehensive test suite for intent classification system"""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        
        # Realistic customer queries for testing
        self.realistic_test_queries = [
            # Project Planning
            ("I want to renovate my bathroom", "project_planning"),
            ("Planning to install new kitchen cabinets", "project_planning"),
            ("Thinking of building a deck in my HDB balcony", "project_planning"),
            ("Need help designing a storage system", "project_planning"),
            ("Want to upgrade my bedroom flooring", "project_planning"),
            
            # Problem Solving
            ("fix squeaky floors", "problem_solving"),
            ("My faucet is leaking badly", "problem_solving"),
            ("Urgent: toilet is clogged", "problem_solving"),
            ("Aircon not cooling properly", "problem_solving"),
            ("Sliding door stuck, need immediate help", "problem_solving"),
            
            # Tool Selection
            ("best drill for concrete drilling", "tool_selection"),
            ("What saw do I need for cutting wood", "tool_selection"),
            ("Recommend hammer for home use", "tool_selection"),  
            ("Need measuring tape for renovation", "tool_selection"),
            ("Which screwdriver set is good for beginners", "tool_selection"),
            
            # Product Comparison
            ("DeWalt vs Makita drill", "product_comparison"),
            ("Compare Bosch and Black & Decker tools", "product_comparison"),
            ("Which is better: Ryobi or Milwaukee", "product_comparison"),
            ("Festool vs Stanley measuring tools", "product_comparison"),
            ("Best value: cheap drill or premium brand", "product_comparison"),
            
            # Learning
            ("how to install tiles", "learning"),
            ("Learn to use a circular saw safely", "learning"),
            ("Tutorial for bathroom renovation", "learning"),
            ("Step by step guide to painting walls", "learning"),
            ("Teach me basic plumbing repairs", "learning"),
            
            # Singapore-specific contexts
            ("Renovate HDB flat bathroom with Town Council approval", "project_planning"),
            ("Fix aircon in tropical humid weather", "problem_solving"),
            ("Tools for void deck renovation project", "tool_selection"),
            ("Condo vs landed property maintenance tools", "product_comparison"),
            ("How to get renovation permit in Singapore", "learning"),
            
            # Complex queries
            ("I'm a beginner looking for budget tools to fix my leaking kitchen faucet urgently", "problem_solving"),
            ("Professional contractor needs heavy-duty drill comparison for concrete work in HDB renovation", "product_comparison"),
            ("Planning major bathroom renovation in condo - need step by step guide and tool recommendations", "project_planning"),
        ]
        
        # Edge cases for robustness testing
        self.edge_case_queries = [
            # Very short queries
            ("fix", "problem_solving"),
            ("drill", "tool_selection"),
            ("how", "learning"),
            
            # Very long queries  
            ("I am planning a comprehensive home renovation project for my three-bedroom HDB flat including bathroom upgrade with new tiles and fixtures, kitchen cabinet installation with modern appliances, bedroom flooring replacement with laminate, living room feature wall creation, and balcony waterproofing and I need detailed guidance on tools, materials, budget planning, contractor selection, Town Council approval process, timeline management, and step-by-step execution plan", "project_planning"),
            
            # Ambiguous queries
            ("problem with installation", "problem_solving"),
            ("need help", "learning"),
            ("best option", "product_comparison"),
            
            # Misspelled queries
            ("fix leaky facet", "problem_solving"),
            ("DeWelt vs Maketa drill", "product_comparison"),
            ("how to instal tiles", "learning"),
            
            # Mixed language (Singapore context)
            ("fix aircon in HDB lah", "problem_solving"),
            ("good drill for DIY projects ah", "tool_selection"),
        ]
    
    def setup_test_environment(self):
        """Set up test environment with mock data if needed"""
        # Create temporary model for testing if needed
        # This would normally load a pre-trained model
        pass
    
    def test_training_data_quality(self):
        """Test quality and distribution of training data"""
        print("Testing training data quality...")
        
        generator = DIYTrainingDataGenerator()
        training_data = generator.generate_all_training_data()
        
        # Test data quantity
        assert len(training_data) >= 1000, f"Insufficient training data: {len(training_data)}"
        
        # Test intent distribution
        intent_counts = {}
        for example in training_data:
            intent_counts[example.intent] = intent_counts.get(example.intent, 0) + 1
        
        # Check all intents are represented
        expected_intents = ["project_planning", "problem_solving", "tool_selection", 
                          "product_comparison", "learning"]
        for intent in expected_intents:
            assert intent in intent_counts, f"Missing intent: {intent}"
            assert intent_counts[intent] >= 100, f"Insufficient data for {intent}: {intent_counts[intent]}"
        
        # Test for Singapore-specific content
        singapore_terms = ["hdb", "condo", "singapore", "tropical", "town council"]
        singapore_examples = 0
        for example in training_data:
            if any(term in example.query.lower() for term in singapore_terms):
                singapore_examples += 1
        
        singapore_percentage = singapore_examples / len(training_data) * 100
        assert singapore_percentage >= 10, f"Insufficient Singapore context: {singapore_percentage:.1f}%"
        
        self.test_results["training_data_quality"] = {
            "total_examples": len(training_data),
            "intent_distribution": intent_counts,
            "singapore_context_percentage": singapore_percentage,
            "status": "PASSED"
        }
        
        print(f"✓ Training data quality test passed: {len(training_data)} examples")
    
    def test_intent_classification_accuracy(self):
        """Test intent classification accuracy on realistic queries"""
        print("Testing intent classification accuracy...")
        
        # Initialize classifier with fallback for testing
        classifier = DIYIntentClassificationSystem()
        
        correct_predictions = 0
        total_predictions = len(self.realistic_test_queries)
        results = []
        
        for query, expected_intent in self.realistic_test_queries:
            try:
                # Use fallback classification for testing without trained model
                predicted_intent, confidence = classifier.keyword_fallback_classify(query)
                is_correct = predicted_intent == expected_intent
                
                if is_correct:
                    correct_predictions += 1
                
                results.append({
                    "query": query,
                    "expected": expected_intent,
                    "predicted": predicted_intent,
                    "confidence": confidence,
                    "correct": is_correct
                })
                
            except Exception as e:
                print(f"Error classifying '{query}': {e}")
                results.append({
                    "query": query,
                    "expected": expected_intent,
                    "predicted": "error",
                    "confidence": 0.0,
                    "correct": False
                })
        
        accuracy = correct_predictions / total_predictions * 100
        
        self.test_results["classification_accuracy"] = {
            "accuracy_percentage": accuracy,
            "correct_predictions": correct_predictions,
            "total_predictions": total_predictions,
            "detailed_results": results,
            "status": "PASSED" if accuracy >= 70 else "FAILED"  # Lower threshold for fallback
        }
        
        print(f"✓ Classification accuracy: {accuracy:.1f}% ({correct_predictions}/{total_predictions})")
        return accuracy >= 70  # Minimum accuracy for fallback system
    
    def test_entity_extraction_accuracy(self):
        """Test entity extraction accuracy"""
        print("Testing entity extraction accuracy...")
        
        extractor = DIYEntityExtractor()
        
        test_cases = [
            ("I want to renovate my HDB bathroom with $2000 budget", 
             ["singapore_context", "room_location", "budget_range", "project_type"]),
            ("Need urgent help fixing leaky faucet", 
             ["urgency", "problem_type"]),
            ("DeWalt drill for wood cutting by beginner", 
             ["brand", "tool_category", "material_type", "skill_level"]),
            ("Professional renovation in condo living room", 
             ["skill_level", "project_type", "singapore_context", "room_location"]),
        ]
        
        total_expected_entities = 0
        total_found_entities = 0
        results = []
        
        for query, expected_entity_types in test_cases:
            entities = extractor.extract_entities(query)
            found_entity_types = [entity.entity_type.value for entity in entities]
            
            expected_found = sum(1 for et in expected_entity_types if et in found_entity_types)
            
            total_expected_entities += len(expected_entity_types)
            total_found_entities += expected_found
            
            results.append({
                "query": query,
                "expected_types": expected_entity_types,
                "found_types": found_entity_types,
                "matches": expected_found
            })
        
        entity_accuracy = total_found_entities / total_expected_entities * 100 if total_expected_entities > 0 else 0
        
        self.test_results["entity_extraction_accuracy"] = {
            "accuracy_percentage": entity_accuracy,
            "total_expected": total_expected_entities,
            "total_found": total_found_entities,
            "detailed_results": results,
            "status": "PASSED" if entity_accuracy >= 60 else "FAILED"
        }
        
        print(f"✓ Entity extraction accuracy: {entity_accuracy:.1f}%")
        return entity_accuracy >= 60
    
    def test_query_expansion_effectiveness(self):
        """Test query expansion system"""
        print("Testing query expansion effectiveness...")
        
        expander = DIYQueryExpander()
        
        test_queries = [
            "fix leak",
            "DeWalt drill", 
            "renovate bathroom",
            "how to install",
            "Makita vs Bosch"
        ]
        
        expansion_results = []
        
        for query in test_queries:
            expanded = expander.expand_query(query)
            variations = expander.get_query_variations(query)
            
            expansion_results.append({
                "original": query,
                "expanded": expanded.expanded_query,
                "expansion_terms": expanded.expansion_terms,
                "variations": variations,
                "confidence_boost": expanded.confidence_boost
            })
        
        # Check that expansions are working
        avg_expansion_terms = np.mean([len(result["expansion_terms"]) for result in expansion_results])
        avg_variations = np.mean([len(result["variations"]) for result in expansion_results])
        
        self.test_results["query_expansion"] = {
            "avg_expansion_terms": avg_expansion_terms,
            "avg_variations": avg_variations,
            "detailed_results": expansion_results,
            "status": "PASSED" if avg_expansion_terms >= 2 else "FAILED"
        }
        
        print(f"✓ Query expansion: avg {avg_expansion_terms:.1f} terms, {avg_variations:.1f} variations")
        return avg_expansion_terms >= 2
    
    def test_response_time_performance(self):
        """Test response time performance (<500ms requirement)"""
        print("Testing response time performance...")
        
        classifier = DIYIntentClassificationSystem()
        extractor = DIYEntityExtractor()
        expander = DIYQueryExpander()
        
        response_times = []
        
        # Test with realistic queries
        for query, expected_intent in self.realistic_test_queries[:20]:  # Test subset
            start_time = time.time()
            
            try:
                # Simulate full pipeline
                expanded = expander.expand_query(query)
                predicted_intent, confidence = classifier.keyword_fallback_classify(expanded.expanded_query)
                entities = extractor.extract_entities(query)
                
                processing_time = (time.time() - start_time) * 1000  # Convert to ms
                response_times.append(processing_time)
                
            except Exception as e:
                print(f"Performance test error for '{query}': {e}")
                response_times.append(1000)  # Penalty for errors
        
        avg_response_time = np.mean(response_times)
        max_response_time = np.max(response_times)
        under_500ms_count = sum(1 for t in response_times if t < 500)
        under_500ms_percentage = under_500ms_count / len(response_times) * 100
        
        self.test_results["response_time_performance"] = {
            "avg_response_time_ms": avg_response_time,
            "max_response_time_ms": max_response_time,
            "under_500ms_percentage": under_500ms_percentage,
            "detailed_times": response_times,
            "status": "PASSED" if under_500ms_percentage >= 90 else "FAILED"
        }
        
        print(f"✓ Response time: avg {avg_response_time:.1f}ms, {under_500ms_percentage:.1f}% under 500ms")
        return under_500ms_percentage >= 90
    
    def test_edge_cases_robustness(self):
        """Test system robustness with edge cases"""
        print("Testing edge cases robustness...")
        
        classifier = DIYIntentClassificationSystem()
        extractor = DIYEntityExtractor()
        
        successful_classifications = 0
        total_edge_cases = len(self.edge_case_queries)
        results = []
        
        for query, expected_intent in self.edge_case_queries:
            try:
                predicted_intent, confidence = classifier.keyword_fallback_classify(query)
                entities = extractor.extract_entities(query)
                
                # Success if no errors occur
                successful_classifications += 1
                results.append({
                    "query": query,
                    "expected": expected_intent,
                    "predicted": predicted_intent,
                    "confidence": confidence,
                    "entities_count": len(entities),
                    "status": "success"
                })
                
            except Exception as e:
                results.append({
                    "query": query,
                    "expected": expected_intent,
                    "error": str(e),
                    "status": "error"
                })
        
        robustness_percentage = successful_classifications / total_edge_cases * 100
        
        self.test_results["edge_cases_robustness"] = {
            "robustness_percentage": robustness_percentage,
            "successful_cases": successful_classifications,
            "total_cases": total_edge_cases,
            "detailed_results": results,
            "status": "PASSED" if robustness_percentage >= 85 else "FAILED"
        }
        
        print(f"✓ Edge cases robustness: {robustness_percentage:.1f}% success rate")
        return robustness_percentage >= 85
    
    def test_singapore_context_handling(self):
        """Test Singapore-specific context handling"""
        print("Testing Singapore context handling...")
        
        extractor = DIYEntityExtractor()
        singapore_queries = [
            "renovate HDB bathroom",
            "fix aircon in tropical weather", 
            "Town Council approval needed",
            "condo maintenance issues",
            "void deck renovation project"
        ]
        
        singapore_entities_found = []
        
        for query in singapore_queries:
            entities = extractor.extract_entities(query)
            sg_entities = [e for e in entities if e.entity_type == EntityType.SINGAPORE_CONTEXT]
            singapore_entities_found.append(len(sg_entities))
        
        avg_sg_entities = np.mean(singapore_entities_found)
        queries_with_sg_context = sum(1 for count in singapore_entities_found if count > 0)
        sg_context_percentage = queries_with_sg_context / len(singapore_queries) * 100
        
        self.test_results["singapore_context"] = {
            "avg_singapore_entities": avg_sg_entities,
            "queries_with_context_percentage": sg_context_percentage,
            "detailed_results": singapore_entities_found,
            "status": "PASSED" if sg_context_percentage >= 80 else "FAILED"
        }
        
        print(f"✓ Singapore context: {sg_context_percentage:.1f}% queries recognized")
        return sg_context_percentage >= 80
    
    def test_api_endpoints(self, base_url: str = "http://localhost:8000"):
        """Test API endpoints (requires running server)"""
        print("Testing API endpoints...")
        
        try:
            # Test health endpoint
            health_response = requests.get(f"{base_url}/health", timeout=5)
            health_check = health_response.status_code == 200
            
            # Test classification endpoint
            test_payload = {
                "query": "I want to renovate my bathroom",
                "use_expansion": True,
                "include_entities": True
            }
            
            classify_response = requests.post(
                f"{base_url}/classify", 
                json=test_payload,
                timeout=10
            )
            classify_check = classify_response.status_code == 200
            
            response_data = classify_response.json() if classify_check else {}
            
            # Test batch endpoint
            batch_payload = {
                "queries": ["fix leak", "DeWalt drill", "how to install tiles"],
                "use_expansion": True,
                "include_entities": True
            }
            
            batch_response = requests.post(
                f"{base_url}/classify/batch", 
                json=batch_payload,
                timeout=15
            )
            batch_check = batch_response.status_code == 200
            
            self.test_results["api_endpoints"] = {
                "health_endpoint": health_check,
                "classify_endpoint": classify_check,
                "batch_endpoint": batch_check,
                "sample_response": response_data,
                "status": "PASSED" if all([health_check, classify_check, batch_check]) else "FAILED"
            }
            
            print(f"✓ API endpoints: Health={health_check}, Classify={classify_check}, Batch={batch_check}")
            return all([health_check, classify_check, batch_check])
            
        except requests.exceptions.RequestException as e:
            print(f"✗ API endpoints test failed: {e}")
            self.test_results["api_endpoints"] = {
                "error": str(e),
                "status": "FAILED"
            }
            return False
    
    def run_comprehensive_tests(self, test_api: bool = False):
        """Run all tests and generate comprehensive report"""
        print("=" * 80)
        print("RUNNING COMPREHENSIVE INTENT CLASSIFICATION TEST SUITE")
        print("=" * 80)
        
        self.setup_test_environment()
        
        # Core functionality tests
        tests = [
            ("Training Data Quality", self.test_training_data_quality),
            ("Intent Classification Accuracy", self.test_intent_classification_accuracy),
            ("Entity Extraction Accuracy", self.test_entity_extraction_accuracy),
            ("Query Expansion Effectiveness", self.test_query_expansion_effectiveness),
            ("Response Time Performance", self.test_response_time_performance),
            ("Edge Cases Robustness", self.test_edge_cases_robustness),
            ("Singapore Context Handling", self.test_singapore_context_handling),
        ]
        
        if test_api:
            tests.append(("API Endpoints", lambda: self.test_api_endpoints()))
        
        # Run tests
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_function in tests:
            print(f"\\n{test_name}...")
            try:
                result = test_function()
                if result:
                    passed_tests += 1
                    print(f"✓ {test_name}: PASSED")
                else:
                    print(f"✗ {test_name}: FAILED")
            except Exception as e:
                print(f"✗ {test_name}: ERROR - {e}")
                self.test_results[test_name.lower().replace(" ", "_")] = {
                    "error": str(e),
                    "status": "ERROR"
                }
        
        # Generate final report
        self.generate_test_report(passed_tests, total_tests)
        
        return passed_tests, total_tests
    
    def generate_test_report(self, passed_tests: int, total_tests: int):
        """Generate comprehensive test report"""
        print("\\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        
        overall_success_rate = passed_tests / total_tests * 100
        
        print(f"Overall Success Rate: {overall_success_rate:.1f}% ({passed_tests}/{total_tests})")
        print(f"Tests Passed: {passed_tests}")
        print(f"Tests Failed: {total_tests - passed_tests}")
        
        # Detailed results
        print("\\nDetailed Results:")
        for test_name, results in self.test_results.items():
            status = results.get("status", "UNKNOWN")
            print(f"  {test_name}: {status}")
            
            if "accuracy_percentage" in results:
                print(f"    Accuracy: {results['accuracy_percentage']:.1f}%")
            if "avg_response_time_ms" in results:
                print(f"    Avg Response Time: {results['avg_response_time_ms']:.1f}ms")
        
        # Performance summary
        if "response_time_performance" in self.test_results:
            perf = self.test_results["response_time_performance"]
            print(f"\\nPerformance Summary:")
            print(f"  Average Response Time: {perf['avg_response_time_ms']:.1f}ms")
            print(f"  Under 500ms: {perf['under_500ms_percentage']:.1f}%")
        
        # Save results to file
        report_path = Path(__file__).parent / "test_results.json"
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\\nDetailed results saved to: {report_path}")
        
        # Determine overall system readiness
        if overall_success_rate >= 85:
            print("\\n🎉 SYSTEM READY FOR PRODUCTION")
        elif overall_success_rate >= 70:
            print("\\n⚠️  SYSTEM NEEDS MINOR IMPROVEMENTS")
        else:
            print("\\n❌ SYSTEM NEEDS MAJOR IMPROVEMENTS")
        
        print("=" * 80)


def run_realistic_customer_query_tests():
    """Run tests with realistic customer queries"""
    test_suite = IntentClassificationTestSuite()
    
    # Additional realistic queries for comprehensive testing
    real_world_queries = [
        "I want to renovate my bathroom",
        "fix squeaky floors", 
        "install new toilet",
        "DeWalt vs Makita drill comparison",
        "how to use a circular saw safely",
        "best budget drill for home DIY",
        "emergency plumbing repair needed",
        "planning kitchen cabinet installation",
        "learn tile installation techniques",
        "professional vs DIY tool recommendations"
    ]
    
    print("Testing with realistic customer queries...")
    
    classifier = DIYIntentClassificationSystem()
    extractor = DIYEntityExtractor()
    expander = DIYQueryExpander()
    
    results = []
    total_time = 0
    
    for query in real_world_queries:
        start_time = time.time()
        
        # Full pipeline test
        expanded = expander.expand_query(query)
        intent, confidence = classifier.keyword_fallback_classify(expanded.expanded_query)
        entities = extractor.extract_entities(query)
        
        processing_time = (time.time() - start_time) * 1000
        total_time += processing_time
        
        results.append({
            "query": query,
            "intent": intent,
            "confidence": confidence,
            "entities_count": len(entities),
            "processing_time_ms": processing_time,
            "expansion_terms": len(expanded.expansion_terms)
        })
        
        print(f"Query: '{query}'")
        print(f"  Intent: {intent} (confidence: {confidence:.3f})")
        print(f"  Entities: {len(entities)}")
        print(f"  Time: {processing_time:.1f}ms")
        print()
    
    avg_time = total_time / len(real_world_queries)
    under_500ms = sum(1 for r in results if r["processing_time_ms"] < 500)
    under_500ms_percent = under_500ms / len(results) * 100
    
    print(f"Summary:")
    print(f"  Total queries: {len(real_world_queries)}")
    print(f"  Average response time: {avg_time:.1f}ms")
    print(f"  Under 500ms: {under_500ms_percent:.1f}%")
    
    return results


if __name__ == "__main__":
    # Run comprehensive test suite
    test_suite = IntentClassificationTestSuite()
    passed, total = test_suite.run_comprehensive_tests(test_api=False)
    
    print("\\n" + "=" * 40)
    print("RUNNING REALISTIC CUSTOMER QUERY TESTS")
    print("=" * 40)
    
    # Run realistic query tests
    realistic_results = run_realistic_customer_query_tests()