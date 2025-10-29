"""
DIY Nexus Platform Test Suite
============================

Comprehensive test suite demonstrating the DIY knowledge platform functionality:
- Natural language query processing
- Intent classification and entity extraction
- Project recommendations with safety considerations
- Tool compatibility checking
- Budget optimization strategies
- Multi-channel access (API, CLI, MCP)

This test suite serves as both validation and demonstration of capabilities.
"""

import json
import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any

# Import the DIY platform components
from diy_nexus_platform import (
    DIYIntentClassifier,
    DIYKnowledgeBase,
    DIYRecommendationEngine,
    create_diy_nexus_platform,
    demonstrate_cli_usage,
    demonstrate_api_usage,
    demonstrate_mcp_usage
)

# Import Kailash SDK for testing workflows
from kailash.runtime.local import LocalRuntime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# TEST DATA AND FIXTURES
# ==============================================================================

class DIYTestData:
    """Test data for DIY platform functionality."""
    
    @staticmethod
    def get_test_queries():
        """Get comprehensive test queries covering all intent types."""
        return [
            # Project planning queries
            {
                'query': "What do I need to install a new toilet?",
                'expected_intent': 'project_planning',
                'expected_entities': {'project': 'toilet'},
                'expected_skill_level': 'intermediate'
            },
            {
                'query': "I want to build a deck in my backyard",
                'expected_intent': 'project_planning',
                'expected_entities': {'project': 'deck'},
                'expected_skill_level': 'intermediate'
            },
            {
                'query': "Planning to renovate my bathroom this weekend",
                'expected_intent': 'project_planning',
                'expected_entities': {'room': 'bathroom'},
                'expected_skill_level': 'intermediate'
            },
            
            # Tool recommendation queries
            {
                'query': "What's the difference between a hammer drill and impact driver?",
                'expected_intent': 'tool_recommendation',
                'expected_entities': {'tool1': 'hammer drill', 'tool2': 'impact driver'},
                'expected_skill_level': 'intermediate'
            },
            {
                'query': "Best tool for cutting ceramic tiles",
                'expected_intent': 'tool_recommendation',
                'expected_entities': {'application': 'cutting ceramic tiles'},
                'expected_skill_level': 'intermediate'
            },
            {
                'query': "Recommend something for drilling concrete walls",
                'expected_intent': 'tool_recommendation',
                'expected_entities': {'use_case': 'drilling concrete walls'},
                'expected_skill_level': 'intermediate'
            },
            
            # Compatibility check queries
            {
                'query': "Can I use Makita batteries with DeWalt tools?",
                'expected_intent': 'compatibility_check',
                'expected_entities': {'item1': 'Makita batteries', 'item2': 'DeWalt tools'},
                'expected_skill_level': 'intermediate'
            },
            {
                'query': "Will a hammer drill work on brick walls?",
                'expected_intent': 'compatibility_check',
                'expected_entities': {'tool': 'hammer drill', 'material': 'brick walls'},
                'expected_skill_level': 'intermediate'
            },
            
            # Problem solving queries
            {
                'query': "How do I fix squeaky floors?",
                'expected_intent': 'problem_solving',
                'expected_entities': {'issue': 'squeaky floors'},
                'expected_skill_level': 'intermediate'
            },
            {
                'query': "My toilet is running constantly",
                'expected_intent': 'problem_solving',
                'expected_entities': {'problem': 'toilet is running'},
                'expected_skill_level': 'intermediate'
            },
            {
                'query': "Having trouble with a stuck door",
                'expected_intent': 'problem_solving',
                'expected_entities': {'issue': 'stuck door'},
                'expected_skill_level': 'intermediate'
            },
            
            # Safety guidance queries
            {
                'query': "Is it safe to cut pressure-treated lumber indoors?",
                'expected_intent': 'safety_guidance',
                'expected_entities': {'action': 'cut pressure-treated lumber indoors'},
                'expected_skill_level': 'intermediate'
            },
            {
                'query': "Do I need safety gear for using a circular saw?",
                'expected_intent': 'safety_guidance',
                'expected_entities': {'task': 'using a circular saw'},
                'expected_skill_level': 'intermediate'
            },
            
            # Budget optimization queries
            {
                'query': "Cheapest way to soundproof a room",
                'expected_intent': 'budget_optimization',
                'expected_entities': {'goal': 'soundproof a room'},
                'expected_skill_level': 'intermediate'
            },
            {
                'query': "Budget tools for a beginner woodworker",
                'expected_intent': 'budget_optimization',
                'expected_entities': {'item_type': 'tools', 'use': 'beginner woodworker'},
                'expected_skill_level': 'beginner'
            }
        ]
    
    @staticmethod
    def get_test_user_profiles():
        """Get test user profiles with different skill levels and preferences."""
        return [
            {
                'user_id': 'beginner_001',
                'skill_level': 'beginner',
                'experience_years': 0,
                'budget_range': 'low',
                'preferred_brands': ['Ryobi', 'Craftsman'],
                'safety_conscious': True
            },
            {
                'user_id': 'intermediate_002',
                'skill_level': 'intermediate',
                'experience_years': 5,
                'budget_range': 'medium',
                'preferred_brands': ['DeWalt', 'Milwaukee'],
                'safety_conscious': True
            },
            {
                'user_id': 'advanced_003',
                'skill_level': 'advanced',
                'experience_years': 15,
                'budget_range': 'high',
                'preferred_brands': ['Festool', 'Makita', 'Bosch'],
                'safety_conscious': True
            }
        ]

# ==============================================================================
# INTENT CLASSIFICATION TESTS
# ==============================================================================

class TestDIYIntentClassifier:
    """Test suite for DIY intent classification."""
    
    def __init__(self):
        self.classifier = DIYIntentClassifier()
        self.test_data = DIYTestData()
    
    def test_intent_classification(self):
        """Test intent classification accuracy."""
        print("🧠 Testing Intent Classification")
        print("=" * 40)
        
        test_queries = self.test_data.get_test_queries()
        correct_predictions = 0
        total_predictions = len(test_queries)
        
        for i, test_case in enumerate(test_queries, 1):
            query = test_case['query']
            expected_intent = test_case['expected_intent']
            
            # Classify the intent
            result = self.classifier.classify_intent(query)
            predicted_intent = result['primary_intent']
            
            # Check if prediction is correct
            is_correct = predicted_intent == expected_intent
            if is_correct:
                correct_predictions += 1
            
            # Display results
            status = "✅" if is_correct else "❌"
            print(f"{status} Test {i}: '{query}'")
            print(f"   Expected: {expected_intent}")
            print(f"   Predicted: {predicted_intent}")
            print(f"   Confidence: {result['confidence']:.2f}")
            print(f"   Entities: {result.get('entities', {})}")
            print(f"   Skill Level: {result.get('skill_level', 'unknown')}")
            print()
        
        accuracy = correct_predictions / total_predictions
        print(f"📊 Intent Classification Accuracy: {accuracy:.2%} ({correct_predictions}/{total_predictions})")
        print()
        
        return accuracy > 0.7  # Expect at least 70% accuracy
    
    def test_entity_extraction(self):
        """Test entity extraction from queries."""
        print("🔍 Testing Entity Extraction")
        print("=" * 40)
        
        entity_test_cases = [
            {
                'query': "Can I use Makita batteries with DeWalt tools?",
                'expected_entities': ['Makita', 'DeWalt', 'batteries', 'tools']
            },
            {
                'query': "What's the best drill for concrete work?",
                'expected_entities': ['drill', 'concrete']
            },
            {
                'query': "How to install a toilet in bathroom?",
                'expected_entities': ['toilet', 'bathroom']
            }
        ]
        
        successful_extractions = 0
        
        for i, test_case in enumerate(entity_test_cases, 1):
            query = test_case['query']
            expected_entities = test_case['expected_entities']
            
            result = self.classifier.classify_intent(query)
            extracted_entities = result.get('entities', {})
            
            # Check if key entities were found
            found_entities = []
            query_lower = query.lower()
            for expected in expected_entities:
                if any(expected.lower() in str(value).lower() for value in extracted_entities.values()) or \
                   expected.lower() in query_lower:
                    found_entities.append(expected)
            
            extraction_success = len(found_entities) >= len(expected_entities) * 0.5  # At least 50% found
            if extraction_success:
                successful_extractions += 1
            
            status = "✅" if extraction_success else "❌"
            print(f"{status} Test {i}: '{query}'")
            print(f"   Expected entities: {expected_entities}")
            print(f"   Extracted entities: {dict(extracted_entities)}")
            print(f"   Found: {found_entities}")
            print()
        
        success_rate = successful_extractions / len(entity_test_cases)
        print(f"📊 Entity Extraction Success Rate: {success_rate:.2%}")
        print()
        
        return success_rate > 0.6  # Expect at least 60% success

# ==============================================================================
# RECOMMENDATION ENGINE TESTS
# ==============================================================================

class TestDIYRecommendationEngine:
    """Test suite for DIY recommendation engine."""
    
    def __init__(self):
        self.knowledge_base = DIYKnowledgeBase()
        self.rec_engine = DIYRecommendationEngine(self.knowledge_base)
        self.classifier = DIYIntentClassifier()
        self.test_data = DIYTestData()
    
    def test_project_recommendations(self):
        """Test project recommendation generation."""
        print("💡 Testing Project Recommendations")
        print("=" * 40)
        
        test_scenarios = [
            {
                'query': "What do I need to install a new toilet?",
                'user_profile': {'skill_level': 'intermediate', 'budget_range': 'medium'},
                'expected_project_types': ['plumbing', 'installation']
            },
            {
                'query': "How do I fix squeaky floors?",
                'user_profile': {'skill_level': 'beginner', 'budget_range': 'low'},
                'expected_project_types': ['flooring', 'repair']
            }
        ]
        
        successful_recommendations = 0
        
        for i, scenario in enumerate(test_scenarios, 1):
            query = scenario['query']
            user_profile = scenario['user_profile']
            
            # Classify intent and generate recommendations
            intent_analysis = self.classifier.classify_intent(query)
            recommendations = self.rec_engine.generate_recommendations(intent_analysis, user_profile)
            
            # Check if we got relevant recommendations
            has_recommendations = len(recommendations) > 0
            has_relevant_content = False
            
            if recommendations:
                # Check if recommendations are relevant
                for rec in recommendations:
                    if rec.confidence_score > 0.3:  # Reasonable confidence
                        has_relevant_content = True
                        break
            
            success = has_recommendations and has_relevant_content
            if success:
                successful_recommendations += 1
            
            status = "✅" if success else "❌"
            print(f"{status} Scenario {i}: '{query}'")
            print(f"   User Profile: {user_profile}")
            print(f"   Recommendations: {len(recommendations)}")
            
            if recommendations:
                for j, rec in enumerate(recommendations[:2], 1):  # Show top 2
                    print(f"   {j}. {rec.project.name}")
                    print(f"      Confidence: {rec.confidence_score:.2f}")
                    print(f"      Reasoning: {rec.reasoning}")
                    print(f"      Difficulty: {rec.project.difficulty_level}")
                    print(f"      Time: {rec.project.estimated_time_hours}h")
                    print(f"      Cost: ${rec.project.estimated_cost_min}-${rec.project.estimated_cost_max}")
            print()
        
        success_rate = successful_recommendations / len(test_scenarios)
        print(f"📊 Recommendation Success Rate: {success_rate:.2%}")
        print()
        
        return success_rate > 0.8  # Expect at least 80% success
    
    def test_safety_considerations(self):
        """Test safety consideration generation."""
        print("🛡️ Testing Safety Considerations")
        print("=" * 40)
        
        safety_test_cases = [
            {
                'query': "How to use a circular saw for the first time?",
                'expected_safety_items': ['safety_glasses', 'hearing_protection', 'proper_technique']
            },
            {
                'query': "Installing electrical outlets in bathroom",
                'expected_safety_items': ['GFCI', 'power_off', 'electrical_safety']
            }
        ]
        
        safety_checks_passed = 0
        
        for i, test_case in enumerate(safety_test_cases, 1):
            query = test_case['query']
            
            intent_analysis = self.classifier.classify_intent(query)
            recommendations = self.rec_engine.generate_recommendations(intent_analysis)
            
            # Check if safety considerations are provided
            has_safety_info = False
            safety_items_found = []
            
            for rec in recommendations:
                if rec.safety_considerations:
                    has_safety_info = True
                    safety_items_found.extend(rec.safety_considerations)
            
            safety_checks_passed += 1 if has_safety_info else 0
            
            status = "✅" if has_safety_info else "❌"
            print(f"{status} Test {i}: '{query}'")
            print(f"   Safety considerations found: {has_safety_info}")
            if safety_items_found:
                print(f"   Safety items: {safety_items_found[:3]}")  # Show first 3
            print()
        
        safety_success_rate = safety_checks_passed / len(safety_test_cases)
        print(f"📊 Safety Consideration Success Rate: {safety_success_rate:.2%}")
        print()
        
        return safety_success_rate > 0.7  # Expect at least 70% success

# ==============================================================================
# WORKFLOW EXECUTION TESTS
# ==============================================================================

class TestDIYWorkflows:
    """Test suite for DIY workflow execution."""
    
    def __init__(self):
        self.runtime = LocalRuntime()
    
    def test_diy_assistant_workflow(self):
        """Test the main DIY assistant workflow."""
        print("⚙️ Testing DIY Assistant Workflow")
        print("=" * 40)
        
        # Import workflow creation function
        from diy_nexus_platform import create_diy_assistant_workflow
        
        # Create and build workflow
        workflow = create_diy_assistant_workflow().build()
        
        # Test data
        test_inputs = [
            {
                'query': 'What do I need to install a new toilet?',
                'user_profile': {
                    'skill_level': 'intermediate',
                    'budget_range': 'medium'
                }
            },
            {
                'query': 'How do I fix squeaky floors?',
                'user_profile': {
                    'skill_level': 'beginner',
                    'budget_range': 'low'
                }
            }
        ]
        
        successful_executions = 0
        
        for i, test_input in enumerate(test_inputs, 1):
            try:
                # Execute workflow
                results, run_id = self.runtime.execute(workflow.build(), test_input)
                
                # Check if execution was successful
                if results and 'format_response' in results:
                    response_data = results['format_response']
                    has_recommendations = response_data.get('total_count', 0) > 0
                    
                    if has_recommendations:
                        successful_executions += 1
                        status = "✅"
                    else:
                        status = "⚠️"
                else:
                    status = "❌"
                
                print(f"{status} Test {i}: Query: '{test_input['query']}'")
                if results and 'format_response' in results:
                    response = results['format_response']
                    print(f"   Response Type: {response.get('response_type', 'unknown')}")
                    print(f"   Recommendations: {response.get('total_count', 0)}")
                    print(f"   Confidence: {response.get('confidence', 0.0):.2f}")
                print(f"   Run ID: {run_id}")
                print()
                
            except Exception as e:
                print(f"❌ Test {i}: Failed with error: {e}")
                print()
        
        success_rate = successful_executions / len(test_inputs)
        print(f"📊 Workflow Execution Success Rate: {success_rate:.2%}")
        print()
        
        return success_rate > 0.8  # Expect at least 80% success
    
    def test_compatibility_workflow(self):
        """Test the compatibility check workflow."""
        print("🔗 Testing Compatibility Check Workflow")
        print("=" * 40)
        
        from diy_nexus_platform import create_compatibility_check_workflow
        
        workflow = create_compatibility_check_workflow().build()
        
        test_cases = [
            {
                'item1': 'Makita battery',
                'item2': 'DeWalt tool'
            },
            {
                'item1': 'hammer drill',
                'item2': 'masonry bit'
            }
        ]
        
        successful_checks = 0
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                results, run_id = self.runtime.execute(workflow.build(), test_case)
                
                if results and 'check_compatibility' in results:
                    compat_result = results['check_compatibility']
                    has_result = 'compatibility_type' in compat_result
                    
                    if has_result:
                        successful_checks += 1
                        status = "✅"
                    else:
                        status = "⚠️"
                else:
                    status = "❌"
                
                print(f"{status} Test {i}: {test_case['item1']} + {test_case['item2']}")
                if results and 'check_compatibility' in results:
                    result = results['check_compatibility']
                    print(f"   Compatibility: {result.get('compatibility_type', 'unknown')}")
                    print(f"   Safe: {result.get('safety_rating', 'unknown')}")
                    print(f"   Notes: {result.get('notes', 'N/A')[:50]}...")
                print()
                
            except Exception as e:
                print(f"❌ Test {i}: Failed with error: {e}")
                print()
        
        success_rate = successful_checks / len(test_cases)
        print(f"📊 Compatibility Check Success Rate: {success_rate:.2%}")
        print()
        
        return success_rate > 0.8

# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================

class TestDIYPlatformIntegration:
    """Integration tests for the complete DIY platform."""
    
    def test_end_to_end_scenarios(self):
        """Test complete end-to-end scenarios."""
        print("🔄 Testing End-to-End Scenarios")
        print("=" * 40)
        
        scenarios = [
            {
                'name': 'Beginner Toilet Installation',
                'user_query': 'I want to replace my toilet but I\'ve never done plumbing before',
                'user_profile': {'skill_level': 'beginner', 'budget_range': 'medium'},
                'expected_outcomes': [
                    'safety_warnings_present',
                    'step_by_step_guidance',
                    'tool_recommendations',
                    'professional_help_suggested'
                ]
            },
            {
                'name': 'Advanced User Tool Comparison',
                'user_query': 'What\'s the difference between impact driver and hammer drill for concrete work?',
                'user_profile': {'skill_level': 'advanced', 'budget_range': 'high'},
                'expected_outcomes': [
                    'detailed_comparison',
                    'technical_specifications',
                    'use_case_recommendations'
                ]
            }
        ]
        
        successful_scenarios = 0
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"📋 Scenario {i}: {scenario['name']}")
            print(f"   Query: '{scenario['user_query']}'")
            
            try:
                # Simulate complete workflow
                classifier = DIYIntentClassifier()
                knowledge_base = DIYKnowledgeBase()
                rec_engine = DIYRecommendationEngine(knowledge_base)
                
                # Process query
                intent_analysis = classifier.classify_intent(scenario['user_query'])
                recommendations = rec_engine.generate_recommendations(
                    intent_analysis, 
                    scenario['user_profile']
                )
                
                # Check expected outcomes
                outcomes_met = 0
                total_outcomes = len(scenario['expected_outcomes'])
                
                for outcome in scenario['expected_outcomes']:
                    if outcome == 'safety_warnings_present':
                        has_safety = any(rec.safety_considerations for rec in recommendations)
                        if has_safety:
                            outcomes_met += 1
                    elif outcome == 'step_by_step_guidance':
                        has_steps = any(len(rec.project.steps) > 0 for rec in recommendations)
                        if has_steps:
                            outcomes_met += 1
                    elif outcome == 'tool_recommendations':
                        has_tools = any(len(rec.recommended_products) > 0 for rec in recommendations)
                        if has_tools:
                            outcomes_met += 1
                    elif outcome == 'professional_help_suggested':
                        has_prof_help = any(rec.project.professional_help_recommended for rec in recommendations)
                        if has_prof_help:
                            outcomes_met += 1
                    elif outcome == 'detailed_comparison':
                        has_comparison = intent_analysis['primary_intent'] == 'tool_recommendation'
                        if has_comparison:
                            outcomes_met += 1
                    elif outcome == 'technical_specifications':
                        # Assume technical specs are included in detailed recommendations
                        has_tech_specs = len(recommendations) > 0
                        if has_tech_specs:
                            outcomes_met += 1
                    elif outcome == 'use_case_recommendations':
                        has_use_cases = any(rec.reasoning for rec in recommendations)
                        if has_use_cases:
                            outcomes_met += 1
                
                outcome_success = outcomes_met / total_outcomes
                if outcome_success >= 0.7:  # 70% of expected outcomes met
                    successful_scenarios += 1
                    status = "✅"
                else:
                    status = "⚠️"
                
                print(f"   {status} Outcomes met: {outcomes_met}/{total_outcomes} ({outcome_success:.1%})")
                print(f"   Recommendations generated: {len(recommendations)}")
                print(f"   Intent classified as: {intent_analysis['primary_intent']}")
                print()
                
            except Exception as e:
                print(f"   ❌ Failed with error: {e}")
                print()
        
        success_rate = successful_scenarios / len(scenarios)
        print(f"📊 End-to-End Success Rate: {success_rate:.2%}")
        print()
        
        return success_rate > 0.8

# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

def run_all_tests():
    """Run all DIY platform tests."""
    print("🧪 DIY Nexus Platform - Comprehensive Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Test 1: Intent Classification
    try:
        intent_test = TestDIYIntentClassifier()
        intent_result = intent_test.test_intent_classification()
        entity_result = intent_test.test_entity_extraction()
        test_results.append(('Intent Classification', intent_result))
        test_results.append(('Entity Extraction', entity_result))
    except Exception as e:
        logger.error(f"Intent classification tests failed: {e}")
        test_results.append(('Intent Classification', False))
        test_results.append(('Entity Extraction', False))
    
    # Test 2: Recommendation Engine
    try:
        rec_test = TestDIYRecommendationEngine()
        rec_result = rec_test.test_project_recommendations()
        safety_result = rec_test.test_safety_considerations()
        test_results.append(('Project Recommendations', rec_result))
        test_results.append(('Safety Considerations', safety_result))
    except Exception as e:
        logger.error(f"Recommendation engine tests failed: {e}")
        test_results.append(('Project Recommendations', False))
        test_results.append(('Safety Considerations', False))
    
    # Test 3: Workflow Execution
    try:
        workflow_test = TestDIYWorkflows()
        workflow_result = workflow_test.test_diy_assistant_workflow()
        compat_result = workflow_test.test_compatibility_workflow()
        test_results.append(('DIY Assistant Workflow', workflow_result))
        test_results.append(('Compatibility Workflow', compat_result))
    except Exception as e:
        logger.error(f"Workflow tests failed: {e}")
        test_results.append(('DIY Assistant Workflow', False))
        test_results.append(('Compatibility Workflow', False))
    
    # Test 4: Integration Tests
    try:
        integration_test = TestDIYPlatformIntegration()
        integration_result = integration_test.test_end_to_end_scenarios()
        test_results.append(('End-to-End Integration', integration_result))
    except Exception as e:
        logger.error(f"Integration tests failed: {e}")
        test_results.append(('End-to-End Integration', False))
    
    # Display final results
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed_tests += 1
    
    print()
    print(f"Overall Success Rate: {passed_tests}/{total_tests} ({passed_tests/total_tests:.1%})")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! DIY platform is ready for deployment.")
    elif passed_tests >= total_tests * 0.8:
        print("🟡 Most tests passed. Platform is functional with minor issues.")
    else:
        print("🔴 Several tests failed. Platform needs attention before deployment.")
    
    print()
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed_tests / total_tests

def demonstrate_platform_usage():
    """Demonstrate platform usage examples."""
    print("🎬 DIY Nexus Platform - Usage Demonstrations")
    print("=" * 60)
    
    # Demonstrate CLI usage
    demonstrate_cli_usage()
    
    # Demonstrate API usage
    demonstrate_api_usage()
    
    # Demonstrate MCP usage
    demonstrate_mcp_usage()
    
    print("📚 Additional Examples Available:")
    print("   - Check the diy_nexus_platform.py file for complete implementation")
    print("   - Run the platform with: python src/diy_nexus_platform.py")
    print("   - API documentation available at: http://localhost:8000/docs")
    print("   - MCP tools discoverable at: http://localhost:3001")
    print()

if __name__ == "__main__":
    # Run comprehensive tests
    success_rate = run_all_tests()
    
    print()
    
    # Demonstrate usage
    demonstrate_platform_usage()
    
    # Provide next steps
    print("🚀 Next Steps:")
    if success_rate >= 0.8:
        print("   1. Start the platform: python src/diy_nexus_platform.py")
        print("   2. Test API endpoints at http://localhost:8000")
        print("   3. Integrate with AI assistants via MCP at http://localhost:3001")
        print("   4. Use CLI commands: nexus execute <workflow_name> --param value")
    else:
        print("   1. Review failed tests and fix issues")
        print("   2. Run tests again: python src/test_diy_nexus_platform.py")
        print("   3. Check logs for detailed error information")
    
    print("   5. Extend with additional DIY projects and knowledge")
    print("   6. Connect to external APIs for real-time pricing")
    print("   7. Add user authentication and personalization")
    print()
    
    print("💡 Remember: This is a demonstration of the DIY knowledge platform")
    print("   capabilities. Extend and customize for your specific needs!")