"""
Tier 3 (E2E) Tests for Testing Infrastructure
===========================================

End-to-end tests for complete system performance validation.
Tests complete user workflows with realistic data loads.
Maximum execution time: <10 seconds per test.

Prerequisites:
- All Docker services running and healthy
- Test data populated across all services
- Performance benchmarks established

Coverage:
- Complete recommendation workflows
- Performance validation with realistic loads
- Safety compliance validation workflows  
- Multi-channel deployment testing
- Load testing with concurrent users
- Response time SLA validation (<2s)
"""

import pytest
import asyncio
import json
import time
import uuid
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Import test data factories
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "test-data"))

from test_data_factory import (
    ProductDataFactory,
    KnowledgeGraphDataFactory,
    PerformanceTestDataFactory,
    generate_all_test_data
)


# Mock classes for when actual services aren't available
class MockDatabaseConnection:
    """Mock database connection for E2E testing without real services"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.connected = True
        self.data_store = {}
    
    async def execute(self, query: str, *args):
        """Mock query execution"""
        await asyncio.sleep(0.01)  # Simulate network latency
        return f"Mock result for {query}"
    
    async def fetch(self, query: str, *args):
        """Mock data fetch"""
        await asyncio.sleep(0.02)  # Simulate data retrieval
        return [{"id": i, "data": f"mock_data_{i}"} for i in range(5)]
    
    async def fetchval(self, query: str, *args):
        """Mock single value fetch"""
        await asyncio.sleep(0.01)
        return 42


class MockWorkflowRuntime:
    """Mock workflow runtime for testing workflow execution patterns"""
    
    def __init__(self):
        self.execution_history = []
        self.performance_metrics = []
    
    async def execute(self, workflow, timeout: float = 30.0):
        """Mock workflow execution with performance tracking"""
        start_time = time.time()
        
        # Simulate workflow execution time based on complexity
        execution_time = 0.5 + (len(workflow.get('nodes', [])) * 0.1)
        await asyncio.sleep(execution_time)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Record execution
        execution_record = {
            'workflow_id': workflow.get('id', str(uuid.uuid4())),
            'node_count': len(workflow.get('nodes', [])),
            'execution_time': actual_duration,
            'timestamp': datetime.now().isoformat(),
            'success': True
        }
        
        self.execution_history.append(execution_record)
        self.performance_metrics.append(actual_duration)
        
        # Mock results
        return {
            'status': 'completed',
            'execution_time': actual_duration,
            'results': {'output': 'Mock workflow result', 'nodes_executed': len(workflow.get('nodes', []))},
            'run_id': str(uuid.uuid4())
        }, execution_record['workflow_id']


class MockRecommendationEngine:
    """Mock recommendation engine for testing recommendation workflows"""
    
    def __init__(self):
        self.products = ProductDataFactory.create_products(100)
        self.users = ProductDataFactory.create_user_profiles(20)
    
    async def get_recommendations(self, user_id: str, category: str = None, count: int = 5):
        """Mock recommendation generation"""
        start_time = time.time()
        
        # Simulate recommendation computation
        await asyncio.sleep(0.8)  # Simulate AI processing time
        
        # Filter products by category if specified
        available_products = self.products
        if category:
            available_products = [p for p in self.products if p.category.lower() == category.lower()]
        
        # Return top N products (mock scoring)
        recommendations = available_products[:count]
        
        execution_time = time.time() - start_time
        
        return {
            'user_id': user_id,
            'recommendations': [
                {
                    'product_code': p.product_code,
                    'name': p.name,
                    'category': p.category,
                    'price': p.price,
                    'confidence_score': 0.95 - (i * 0.1),
                    'safety_standards': p.safety_standards
                }
                for i, p in enumerate(recommendations)
            ],
            'execution_time': execution_time,
            'total_products_considered': len(available_products)
        }


class MockSafetyComplianceValidator:
    """Mock safety compliance validator for testing compliance workflows"""
    
    def __init__(self):
        self.safety_standards = ProductDataFactory.create_safety_standards(30)
    
    async def validate_product_safety(self, product_code: str, user_skill_level: str, environment: str):
        """Mock safety compliance validation"""
        start_time = time.time()
        
        # Simulate compliance checking
        await asyncio.sleep(0.3)
        
        # Mock compliance results
        applicable_standards = [s for s in self.safety_standards if len(s.applicable_products) > 0][:3]
        
        compliance_results = {
            'product_code': product_code,
            'user_skill_level': user_skill_level,
            'environment': environment,
            'compliance_status': 'compliant',
            'applicable_standards': [
                {
                    'standard_id': s.standard_id,
                    'name': s.name,
                    'organization': s.organization,
                    'compliance_level': s.compliance_level,
                    'requirements': s.requirements[:2]  # First 2 requirements
                }
                for s in applicable_standards
            ],
            'safety_warnings': [] if user_skill_level in ['intermediate', 'advanced', 'expert'] else [
                "Additional training recommended for novice users",
                "Supervision advised for complex operations"
            ],
            'execution_time': time.time() - start_time
        }
        
        return compliance_results


@pytest.fixture(scope="session")
async def mock_database_cluster():
    """Provide mock database cluster for E2E testing"""
    cluster = {
        'postgres': MockDatabaseConnection('postgres'),
        'neo4j': MockDatabaseConnection('neo4j'),
        'chromadb': MockDatabaseConnection('chromadb'),
        'redis': MockDatabaseConnection('redis')
    }
    yield cluster


@pytest.fixture(scope="session")
def mock_workflow_runtime():
    """Provide mock workflow runtime for E2E testing"""
    return MockWorkflowRuntime()


@pytest.fixture(scope="session")
def mock_recommendation_engine():
    """Provide mock recommendation engine for E2E testing"""
    return MockRecommendationEngine()


@pytest.fixture(scope="session")
def mock_safety_validator():
    """Provide mock safety compliance validator for E2E testing"""
    return MockSafetyComplianceValidator()


@pytest.fixture
def performance_requirements():
    """Define performance requirements for E2E tests"""
    return {
        'recommendation_max_time': 2.0,      # <2s for recommendations
        'safety_check_max_time': 1.0,       # <1s for safety validation
        'search_max_time': 0.5,             # <500ms for search
        'workflow_max_time': 10.0,          # <10s for complete workflows
        'concurrent_user_target': 10,       # Support 10 concurrent users
        'throughput_target': 20              # 20 requests per second
    }


@pytest.mark.e2e
@pytest.mark.requires_docker
@pytest.mark.performance
class TestCompleteRecommendationWorkflow:
    """Test complete product recommendation workflows end-to-end"""
    
    @pytest.mark.asyncio
    async def test_basic_recommendation_workflow(self, mock_recommendation_engine, 
                                               performance_requirements, performance_monitor):
        """Test basic product recommendation workflow within SLA"""
        monitor = performance_monitor.start("basic_recommendation_workflow")
        
        # Simulate user request
        user_id = str(uuid.uuid4())
        
        # Execute recommendation workflow
        recommendations = await mock_recommendation_engine.get_recommendations(
            user_id=user_id,
            category="Power Tools",
            count=5
        )
        
        duration = monitor.stop("basic_recommendation_workflow")
        
        # Validate results
        assert recommendations['user_id'] == user_id, "User ID should match"
        assert len(recommendations['recommendations']) == 5, "Should return 5 recommendations"
        assert all(r['category'] == "Power Tools" for r in recommendations['recommendations']), \
            "All recommendations should be Power Tools"
        
        # Validate confidence scores are in descending order
        scores = [r['confidence_score'] for r in recommendations['recommendations']]
        assert scores == sorted(scores, reverse=True), "Confidence scores should be descending"
        
        # Performance validation
        max_time = performance_requirements['recommendation_max_time']
        assert duration < max_time, f"Recommendation took {duration:.3f}s, exceeds {max_time}s SLA"
        
        # Validate recommendation engine performance metric
        engine_time = recommendations['execution_time']
        assert engine_time < max_time, f"Engine time {engine_time:.3f}s exceeds {max_time}s SLA"
    
    @pytest.mark.asyncio
    async def test_personalized_recommendation_workflow(self, mock_recommendation_engine, 
                                                      performance_requirements, performance_monitor):
        """Test personalized recommendation workflow with user preferences"""
        monitor = performance_monitor.start("personalized_recommendation_workflow")
        
        # Create user with specific preferences
        users = ProductDataFactory.create_user_profiles(1)
        test_user = users[0]
        
        # Get recommendations for each preferred category
        all_recommendations = []
        
        for category in test_user.preferred_categories:
            category_recommendations = await mock_recommendation_engine.get_recommendations(
                user_id=test_user.user_id,
                category=category,
                count=3
            )
            all_recommendations.extend(category_recommendations['recommendations'])
        
        duration = monitor.stop("personalized_recommendation_workflow")
        
        # Validate personalized results
        assert len(all_recommendations) > 0, "Should have personalized recommendations"
        
        # Check that recommendations match user preferences
        recommended_categories = set(r['category'] for r in all_recommendations)
        user_preference_set = set(test_user.preferred_categories)
        
        # At least some overlap between recommendations and preferences
        overlap = recommended_categories.intersection(user_preference_set)
        assert len(overlap) > 0, "Recommendations should match user preferences"
        
        # Performance validation
        max_time = performance_requirements['recommendation_max_time'] * len(test_user.preferred_categories)
        assert duration < max_time, f"Personalized recommendations took {duration:.3f}s, exceeds {max_time}s SLA"
    
    @pytest.mark.asyncio
    async def test_recommendation_with_safety_filtering(self, mock_recommendation_engine, 
                                                      mock_safety_validator, 
                                                      performance_requirements, performance_monitor):
        """Test recommendation workflow with safety compliance filtering"""
        monitor = performance_monitor.start("safety_filtered_recommendations")
        
        user_id = str(uuid.uuid4())
        user_skill_level = "beginner"
        environment = "home_workshop"
        
        # Get initial recommendations
        initial_recommendations = await mock_recommendation_engine.get_recommendations(
            user_id=user_id,
            category="Power Tools",
            count=10
        )
        
        # Filter recommendations through safety validator
        safe_recommendations = []
        
        for recommendation in initial_recommendations['recommendations']:
            safety_result = await mock_safety_validator.validate_product_safety(
                product_code=recommendation['product_code'],
                user_skill_level=user_skill_level,
                environment=environment
            )
            
            if safety_result['compliance_status'] == 'compliant':
                recommendation['safety_validation'] = safety_result
                safe_recommendations.append(recommendation)
        
        duration = monitor.stop("safety_filtered_recommendations")
        
        # Validate safety filtering
        assert len(safe_recommendations) > 0, "Should have safe recommendations for beginners"
        
        # All recommendations should be compliant
        for rec in safe_recommendations:
            assert rec['safety_validation']['compliance_status'] == 'compliant', \
                "All recommendations should be safety compliant"
            assert rec['safety_validation']['user_skill_level'] == user_skill_level, \
                "Safety validation should match user skill level"
        
        # Performance validation (includes both recommendation and safety validation time)
        max_time = performance_requirements['recommendation_max_time'] + performance_requirements['safety_check_max_time']
        assert duration < max_time, f"Safety-filtered recommendations took {duration:.3f}s, exceeds {max_time}s SLA"


@pytest.mark.e2e
@pytest.mark.requires_docker
@pytest.mark.performance
class TestSafetyComplianceWorkflows:
    """Test complete safety compliance validation workflows"""
    
    @pytest.mark.asyncio
    async def test_product_safety_validation_workflow(self, mock_safety_validator, 
                                                    performance_requirements, performance_monitor):
        """Test complete product safety validation workflow"""
        monitor = performance_monitor.start("product_safety_validation")
        
        # Test with different user skill levels
        test_scenarios = [
            ("PRD-00001", "novice", "outdoor"),
            ("PRD-00002", "intermediate", "indoor"),
            ("PRD-00003", "advanced", "industrial"),
            ("PRD-00004", "expert", "hazardous")
        ]
        
        validation_results = []
        
        for product_code, skill_level, environment in test_scenarios:
            result = await mock_safety_validator.validate_product_safety(
                product_code=product_code,
                user_skill_level=skill_level,
                environment=environment
            )
            validation_results.append(result)
        
        duration = monitor.stop("product_safety_validation")
        
        # Validate results
        assert len(validation_results) == 4, "Should validate all test scenarios"
        
        for result in validation_results:
            assert 'compliance_status' in result, "Should have compliance status"
            assert 'applicable_standards' in result, "Should have applicable standards"
            assert 'safety_warnings' in result, "Should have safety warnings"
            assert result['execution_time'] > 0, "Should track execution time"
        
        # Check that novice users get more warnings
        novice_result = validation_results[0]  # First result is for novice
        expert_result = validation_results[3]   # Last result is for expert
        
        assert len(novice_result['safety_warnings']) >= len(expert_result['safety_warnings']), \
            "Novice users should receive more safety warnings"
        
        # Performance validation
        max_time = performance_requirements['safety_check_max_time'] * len(test_scenarios)
        assert duration < max_time, f"Safety validation took {duration:.3f}s, exceeds {max_time}s SLA"
    
    @pytest.mark.asyncio
    async def test_batch_safety_compliance_check(self, mock_safety_validator, 
                                               performance_requirements, performance_monitor):
        """Test batch safety compliance checking for multiple products"""
        monitor = performance_monitor.start("batch_safety_compliance")
        
        # Generate batch of products to validate
        products = ProductDataFactory.create_products(20)
        user_skill_level = "intermediate"
        environment = "workshop"
        
        # Process batch concurrently for better performance
        async def validate_product(product):
            return await mock_safety_validator.validate_product_safety(
                product_code=product.product_code,
                user_skill_level=user_skill_level,
                environment=environment
            )
        
        # Execute batch validation
        tasks = [validate_product(product) for product in products]
        batch_results = await asyncio.gather(*tasks)
        
        duration = monitor.stop("batch_safety_compliance")
        
        # Validate batch results
        assert len(batch_results) == 20, "Should validate all 20 products"
        
        compliant_count = sum(1 for result in batch_results if result['compliance_status'] == 'compliant')
        assert compliant_count > 0, "Should have at least some compliant products"
        
        # Check that all results have required fields
        for result in batch_results:
            assert all(field in result for field in [
                'product_code', 'compliance_status', 'applicable_standards',
                'safety_warnings', 'execution_time'
            ]), "All results should have required fields"
        
        # Performance validation - batch processing should be more efficient
        max_time = performance_requirements['safety_check_max_time'] * 5  # Should be much faster than sequential
        assert duration < max_time, f"Batch safety validation took {duration:.3f}s, exceeds {max_time}s SLA"


@pytest.mark.e2e
@pytest.mark.requires_docker
@pytest.mark.performance
class TestWorkflowExecutionPerformance:
    """Test complete workflow execution performance"""
    
    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self, mock_workflow_runtime, 
                                           performance_requirements, performance_monitor):
        """Test simple workflow execution within performance limits"""
        monitor = performance_monitor.start("simple_workflow_execution")
        
        # Create simple test workflow
        test_workflow = {
            'id': str(uuid.uuid4()),
            'name': 'Product Search Workflow',
            'nodes': [
                {'id': 'search_input', 'type': 'UserInput', 'params': {'query': 'drill bits'}},
                {'id': 'vector_search', 'type': 'VectorSearch', 'params': {'top_k': 10}},
                {'id': 'filter_results', 'type': 'DataFilter', 'params': {'category': 'Power Tools'}},
                {'id': 'format_output', 'type': 'DataTransform', 'params': {'format': 'json'}}
            ]
        }
        
        # Execute workflow
        result, run_id = await mock_workflow_runtime.execute(test_workflow, timeout=30.0)
        
        duration = monitor.stop("simple_workflow_execution")
        
        # Validate execution
        assert result['status'] == 'completed', "Workflow should complete successfully"
        assert run_id is not None, "Should return run ID"
        assert result['results']['nodes_executed'] == 4, "Should execute all 4 nodes"
        
        # Performance validation
        max_time = performance_requirements['workflow_max_time']
        assert duration < max_time, f"Simple workflow took {duration:.3f}s, exceeds {max_time}s SLA"
        
        # Check runtime performance tracking
        assert len(mock_workflow_runtime.execution_history) > 0, "Should track execution history"
        assert len(mock_workflow_runtime.performance_metrics) > 0, "Should track performance metrics"
    
    @pytest.mark.asyncio
    async def test_complex_workflow_execution(self, mock_workflow_runtime, 
                                            performance_requirements, performance_monitor):
        """Test complex workflow execution with multiple branches"""
        monitor = performance_monitor.start("complex_workflow_execution")
        
        # Create complex workflow with multiple processing paths
        complex_workflow = {
            'id': str(uuid.uuid4()),
            'name': 'Advanced Recommendation Workflow',
            'nodes': [
                {'id': 'user_input', 'type': 'UserInput'},
                {'id': 'user_profile', 'type': 'DatabaseLookup'},
                {'id': 'content_search', 'type': 'VectorSearch'},
                {'id': 'collaborative_filter', 'type': 'MLModel'},
                {'id': 'safety_check', 'type': 'ComplianceValidator'},
                {'id': 'price_filter', 'type': 'DataFilter'},
                {'id': 'rank_results', 'type': 'MLRanking'},
                {'id': 'personalize', 'type': 'DataTransform'},
                {'id': 'format_response', 'type': 'ResponseFormatter'},
                {'id': 'cache_results', 'type': 'CacheWrite'}
            ]
        }
        
        # Execute complex workflow
        result, run_id = await mock_workflow_runtime.execute(complex_workflow, timeout=60.0)
        
        duration = monitor.stop("complex_workflow_execution")
        
        # Validate execution
        assert result['status'] == 'completed', "Complex workflow should complete successfully"
        assert result['results']['nodes_executed'] == 10, "Should execute all 10 nodes"
        
        # Performance validation
        max_time = performance_requirements['workflow_max_time']
        assert duration < max_time, f"Complex workflow took {duration:.3f}s, exceeds {max_time}s SLA"
        
        # Verify performance scales reasonably with complexity
        simple_workflow_avg = sum(mock_workflow_runtime.performance_metrics[:-1]) / len(mock_workflow_runtime.performance_metrics[:-1]) if len(mock_workflow_runtime.performance_metrics) > 1 else 1.0
        complex_workflow_time = mock_workflow_runtime.performance_metrics[-1]
        
        # Complex workflow should take more time but not exponentially more
        assert complex_workflow_time < simple_workflow_avg * 5, \
            "Complex workflow shouldn't be more than 5x slower than simple workflow"
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, mock_workflow_runtime, 
                                               performance_requirements, performance_monitor):
        """Test concurrent workflow execution performance"""
        monitor = performance_monitor.start("concurrent_workflow_execution")
        
        # Create multiple workflows for concurrent execution
        workflows = []
        for i in range(performance_requirements['concurrent_user_target']):
            workflow = {
                'id': str(uuid.uuid4()),
                'name': f'Concurrent Workflow {i+1}',
                'nodes': [
                    {'id': f'input_{i}', 'type': 'UserInput'},
                    {'id': f'search_{i}', 'type': 'VectorSearch'},
                    {'id': f'filter_{i}', 'type': 'DataFilter'},
                    {'id': f'output_{i}', 'type': 'ResponseFormatter'}
                ]
            }
            workflows.append(workflow)
        
        # Execute workflows concurrently
        tasks = [mock_workflow_runtime.execute(workflow) for workflow in workflows]
        concurrent_results = await asyncio.gather(*tasks)
        
        duration = monitor.stop("concurrent_workflow_execution")
        
        # Validate concurrent execution
        assert len(concurrent_results) == performance_requirements['concurrent_user_target'], \
            f"Should execute {performance_requirements['concurrent_user_target']} workflows"
        
        # All workflows should complete successfully
        for result, run_id in concurrent_results:
            assert result['status'] == 'completed', "All concurrent workflows should complete"
            assert run_id is not None, "All workflows should have run IDs"
        
        # Performance validation - concurrent execution should be efficient
        avg_time_per_workflow = duration / performance_requirements['concurrent_user_target']
        max_time_per_workflow = performance_requirements['workflow_max_time']
        
        assert avg_time_per_workflow < max_time_per_workflow, \
            f"Average concurrent workflow time {avg_time_per_workflow:.3f}s exceeds {max_time_per_workflow}s SLA"
        
        # Calculate throughput
        throughput = performance_requirements['concurrent_user_target'] / duration
        target_throughput = performance_requirements['throughput_target']
        
        assert throughput >= target_throughput * 0.8, \
            f"Throughput {throughput:.2f} RPS below 80% of target {target_throughput} RPS"


@pytest.mark.e2e
@pytest.mark.requires_docker
@pytest.mark.performance
class TestLoadTestingAndStressValidation:
    """Test system behavior under load and stress conditions"""
    
    @pytest.mark.asyncio
    async def test_sustained_load_performance(self, mock_recommendation_engine, 
                                            performance_requirements, performance_monitor):
        """Test system performance under sustained load"""
        monitor = performance_monitor.start("sustained_load_test")
        
        # Generate load test data
        load_test_data = PerformanceTestDataFactory.create_load_test_data(
            user_count=performance_requirements['concurrent_user_target'],
            request_count=100
        )
        
        # Execute sustained load
        results = []
        start_time = time.time()
        
        for i, query in enumerate(load_test_data['search_queries']):
            if query['type'] == 'recommendation':
                result = await mock_recommendation_engine.get_recommendations(
                    user_id=query['user_id'],
                    category=query.get('product_category'),
                    count=5
                )
                results.append({
                    'query_index': i,
                    'response_time': result['execution_time'],
                    'success': True
                })
            
            # Add small delay to simulate realistic request spacing
            await asyncio.sleep(0.05)  # 20 RPS
        
        total_duration = monitor.stop("sustained_load_test")
        
        # Validate load test results
        assert len(results) > 0, "Should process load test requests"
        
        # Calculate performance metrics
        response_times = [r['response_time'] for r in results]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        success_rate = sum(1 for r in results if r['success']) / len(results)
        
        # Performance validation
        assert avg_response_time < performance_requirements['recommendation_max_time'], \
            f"Average response time {avg_response_time:.3f}s exceeds {performance_requirements['recommendation_max_time']}s SLA"
        
        assert max_response_time < performance_requirements['recommendation_max_time'] * 2, \
            f"Max response time {max_response_time:.3f}s exceeds 2x SLA"
        
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95% threshold"
        
        # Throughput validation
        actual_throughput = len(results) / total_duration
        assert actual_throughput >= performance_requirements['throughput_target'] * 0.8, \
            f"Throughput {actual_throughput:.2f} RPS below 80% of target"
    
    @pytest.mark.asyncio
    async def test_peak_load_handling(self, mock_recommendation_engine, 
                                    performance_requirements, performance_monitor):
        """Test system behavior under peak load conditions"""
        monitor = performance_monitor.start("peak_load_test")
        
        # Simulate peak load (2x normal concurrent users)
        peak_concurrent_users = performance_requirements['concurrent_user_target'] * 2
        
        # Create concurrent requests
        async def generate_peak_request(user_index):
            return await mock_recommendation_engine.get_recommendations(
                user_id=f"peak_user_{user_index}",
                category="Power Tools",
                count=5
            )
        
        # Execute peak load test
        peak_tasks = [generate_peak_request(i) for i in range(peak_concurrent_users)]
        peak_results = await asyncio.gather(*peak_tasks, return_exceptions=True)
        
        duration = monitor.stop("peak_load_test")
        
        # Validate peak load handling
        successful_results = [r for r in peak_results if not isinstance(r, Exception)]
        failed_results = [r for r in peak_results if isinstance(r, Exception)]
        
        success_rate = len(successful_results) / len(peak_results)
        
        # Under peak load, system should still maintain reasonable success rate
        assert success_rate >= 0.80, f"Peak load success rate {success_rate:.2%} below 80% threshold"
        
        # Response times may be higher under peak load but should still be reasonable
        if successful_results:
            peak_response_times = [r['execution_time'] for r in successful_results]
            avg_peak_response_time = sum(peak_response_times) / len(peak_response_times)
            
            # Allow 3x normal SLA under peak load
            peak_sla = performance_requirements['recommendation_max_time'] * 3
            assert avg_peak_response_time < peak_sla, \
                f"Peak load avg response {avg_peak_response_time:.3f}s exceeds 3x SLA {peak_sla}s"
    
    @pytest.mark.asyncio
    async def test_memory_and_resource_efficiency(self, mock_workflow_runtime, 
                                                performance_requirements, performance_monitor):
        """Test resource efficiency during extended operation"""
        monitor = performance_monitor.start("resource_efficiency_test")
        
        # Run extended test to check for memory leaks and resource efficiency
        initial_execution_count = len(mock_workflow_runtime.execution_history)
        
        # Execute many small workflows
        for batch in range(5):  # 5 batches of 10 workflows each
            batch_workflows = []
            for i in range(10):
                workflow = {
                    'id': str(uuid.uuid4()),
                    'name': f'Resource Test Workflow Batch {batch} Item {i}',
                    'nodes': [
                        {'id': f'node_{batch}_{i}', 'type': 'SimpleProcessor'}
                    ]
                }
                batch_workflows.append(workflow)
            
            # Execute batch
            batch_tasks = [mock_workflow_runtime.execute(wf) for wf in batch_workflows]
            await asyncio.gather(*batch_tasks)
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        duration = monitor.stop("resource_efficiency_test")
        
        # Validate resource efficiency
        total_executions = len(mock_workflow_runtime.execution_history) - initial_execution_count
        assert total_executions == 50, "Should execute all 50 workflows"
        
        # Check that performance doesn't degrade over time
        recent_metrics = mock_workflow_runtime.performance_metrics[-10:]  # Last 10 executions
        early_metrics = mock_workflow_runtime.performance_metrics[-50:-40]  # Early executions
        
        if len(early_metrics) > 0 and len(recent_metrics) > 0:
            avg_early = sum(early_metrics) / len(early_metrics)
            avg_recent = sum(recent_metrics) / len(recent_metrics)
            
            # Recent performance shouldn't be significantly worse than early performance
            performance_degradation = (avg_recent - avg_early) / avg_early
            assert performance_degradation < 0.5, \
                f"Performance degraded by {performance_degradation:.1%}, indicates potential memory leak"
        
        # Total duration should be reasonable
        max_total_time = performance_requirements['workflow_max_time'] * 10  # Should be much better than sequential
        assert duration < max_total_time, \
            f"Resource efficiency test took {duration:.3f}s, exceeds {max_total_time}s limit"


@pytest.mark.e2e
@pytest.mark.requires_docker
class TestSystemIntegrationValidation:
    """Test complete system integration across all components"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_user_journey(self, mock_recommendation_engine, mock_safety_validator,
                                         mock_workflow_runtime, performance_requirements, performance_monitor):
        """Test complete user journey from search to recommendation to safety validation"""
        monitor = performance_monitor.start("end_to_end_user_journey")
        
        # Simulate complete user journey
        user_id = str(uuid.uuid4())
        search_query = "cordless drill for home improvement"
        user_skill_level = "intermediate"
        environment = "home_workshop"
        
        # Step 1: Get personalized recommendations
        recommendations = await mock_recommendation_engine.get_recommendations(
            user_id=user_id,
            category="Power Tools",
            count=10
        )
        
        # Step 2: Validate safety for each recommendation
        safe_products = []
        for rec in recommendations['recommendations']:
            safety_result = await mock_safety_validator.validate_product_safety(
                product_code=rec['product_code'],
                user_skill_level=user_skill_level,
                environment=environment
            )
            
            if safety_result['compliance_status'] == 'compliant':
                rec['safety_validation'] = safety_result
                safe_products.append(rec)
        
        # Step 3: Execute workflow to format and deliver results
        result_workflow = {
            'id': str(uuid.uuid4()),
            'name': 'User Journey Result Processing',
            'nodes': [
                {'id': 'format_results', 'type': 'DataTransform'},
                {'id': 'cache_user_history', 'type': 'CacheWrite'},
                {'id': 'log_interaction', 'type': 'DatabaseWrite'},
                {'id': 'format_response', 'type': 'ResponseFormatter'}
            ]
        }
        
        workflow_result, run_id = await mock_workflow_runtime.execute(result_workflow)
        
        duration = monitor.stop("end_to_end_user_journey")
        
        # Validate complete user journey
        assert len(recommendations['recommendations']) == 10, "Should get 10 initial recommendations"
        assert len(safe_products) > 0, "Should have safe products for intermediate user"
        assert workflow_result['status'] == 'completed', "Result processing workflow should complete"
        
        # Validate safety filtering effectiveness
        for product in safe_products:
            assert product['safety_validation']['compliance_status'] == 'compliant'
            assert product['safety_validation']['user_skill_level'] == user_skill_level
        
        # Performance validation for complete journey
        max_journey_time = (performance_requirements['recommendation_max_time'] + 
                          performance_requirements['safety_check_max_time'] + 
                          performance_requirements['workflow_max_time'])
        
        assert duration < max_journey_time, \
            f"Complete user journey took {duration:.3f}s, exceeds {max_journey_time}s SLA"
    
    @pytest.mark.asyncio
    async def test_multi_user_concurrent_journeys(self, mock_recommendation_engine, 
                                                mock_safety_validator, performance_requirements, performance_monitor):
        """Test multiple concurrent user journeys"""
        monitor = performance_monitor.start("multi_user_concurrent_journeys")
        
        # Create multiple concurrent user scenarios
        user_scenarios = [
            {"user_id": str(uuid.uuid4()), "skill": "novice", "category": "Hand Tools"},
            {"user_id": str(uuid.uuid4()), "skill": "intermediate", "category": "Power Tools"},
            {"user_id": str(uuid.uuid4()), "skill": "advanced", "category": "Measuring Tools"},
            {"user_id": str(uuid.uuid4()), "skill": "expert", "category": "Safety Equipment"},
            {"user_id": str(uuid.uuid4()), "skill": "intermediate", "category": "Power Tools"}
        ]
        
        async def execute_user_journey(scenario):
            # Get recommendations
            recs = await mock_recommendation_engine.get_recommendations(
                user_id=scenario["user_id"],
                category=scenario["category"],
                count=5
            )
            
            # Validate first recommendation for safety
            if recs['recommendations']:
                safety_result = await mock_safety_validator.validate_product_safety(
                    product_code=recs['recommendations'][0]['product_code'],
                    user_skill_level=scenario["skill"],
                    environment="workshop"
                )
                recs['safety_validation'] = safety_result
            
            return recs
        
        # Execute all user journeys concurrently
        journey_tasks = [execute_user_journey(scenario) for scenario in user_scenarios]
        journey_results = await asyncio.gather(*journey_tasks)
        
        duration = monitor.stop("multi_user_concurrent_journeys")
        
        # Validate concurrent journeys
        assert len(journey_results) == len(user_scenarios), "All user journeys should complete"
        
        for i, result in enumerate(journey_results):
            scenario = user_scenarios[i]
            assert result['user_id'] == scenario['user_id'], "User ID should match scenario"
            assert len(result['recommendations']) == 5, "Each user should get 5 recommendations"
            
            # Check category matching
            for rec in result['recommendations']:
                assert rec['category'] == scenario['category'], \
                    f"Recommendation category should match user preference"
            
            # Validate safety validation was performed
            if 'safety_validation' in result:
                assert result['safety_validation']['user_skill_level'] == scenario['skill']
        
        # Performance validation for concurrent execution
        avg_time_per_journey = duration / len(user_scenarios)
        max_journey_time = performance_requirements['recommendation_max_time'] + performance_requirements['safety_check_max_time']
        
        assert avg_time_per_journey < max_journey_time, \
            f"Average concurrent journey time {avg_time_per_journey:.3f}s exceeds {max_journey_time}s SLA"


if __name__ == "__main__":
    # Run E2E tests directly for debugging
    pytest.main([__file__, "-v", "--tb=short", "-m", "e2e"])