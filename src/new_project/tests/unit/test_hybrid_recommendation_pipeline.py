"""
Unit Tests for Hybrid Recommendation Pipeline
===========================================

Tests the hybrid recommendation pipeline that combines Neo4j knowledge graph,
ChromaDB vector database, and OpenAI GPT-4 integration for comprehensive
tool recommendations with mocking for fast unit tests.

Test Coverage:
- Pipeline initialization and component coordination
- Multi-source data integration and ranking
- Confidence scoring and result merging
- Safety compliance integration
- Performance optimization and caching
- Error handling and fallback mechanisms
- Performance constraints (<1s per test)
"""

import pytest
import time
import json
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional, Tuple

# Test framework imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import windows_patch  # Apply Windows compatibility for Kailash SDK

# Import the service under test (will be implemented)
from src.new_project.core.services.hybrid_recommendation_pipeline import (
    HybridRecommendationPipeline, RecommendationEngine, ResultMerger
)
from src.new_project.core.models.hybrid_recommendations import (
    HybridRecommendationRequest, HybridRecommendationResponse,
    ComponentScore, RecommendationResult, ConfidenceMetrics
)


class TestHybridRecommendationPipeline:
    """Test hybrid recommendation pipeline initialization and configuration"""
    
    @pytest.fixture
    def mock_services(self):
        """Mock all service dependencies"""
        mock_neo4j_service = MagicMock()
        mock_vector_service = MagicMock()
        mock_openai_service = MagicMock()
        
        return mock_neo4j_service, mock_vector_service, mock_openai_service
    
    @pytest.fixture
    def hybrid_pipeline(self, mock_services):
        """Create hybrid recommendation pipeline with mocked services"""
        mock_neo4j, mock_vector, mock_openai = mock_services
        
        pipeline = HybridRecommendationPipeline(
            knowledge_graph_service=mock_neo4j,
            vector_database_service=mock_vector,
            openai_service=mock_openai,
            confidence_threshold=0.7,
            max_recommendations=10
        )
        
        return pipeline, mock_neo4j, mock_vector, mock_openai
    
    def test_pipeline_initialization(self, hybrid_pipeline):
        """Test pipeline initializes with proper configuration"""
        pipeline, mock_neo4j, mock_vector, mock_openai = hybrid_pipeline
        
        assert pipeline is not None
        assert pipeline.confidence_threshold == 0.7
        assert pipeline.max_recommendations == 10
        assert hasattr(pipeline, 'knowledge_graph_service')
        assert hasattr(pipeline, 'vector_database_service')
        assert hasattr(pipeline, 'openai_service')
        assert hasattr(pipeline, 'result_merger')
        assert hasattr(pipeline, 'cache')
    
    def test_component_availability_check(self, hybrid_pipeline):
        """Test checking availability of all pipeline components"""
        pipeline, mock_neo4j, mock_vector, mock_openai = hybrid_pipeline
        
        # Mock successful component checks
        mock_neo4j.health_check.return_value = True
        mock_vector.health_check.return_value = True
        mock_openai.health_check.return_value = True
        
        status = pipeline.check_component_health()
        
        assert status["knowledge_graph"] is True
        assert status["vector_database"] is True
        assert status["openai_integration"] is True
        assert status["overall_healthy"] is True
    
    def test_component_failure_handling(self, hybrid_pipeline):
        """Test handling when one component is unavailable"""
        pipeline, mock_neo4j, mock_vector, mock_openai = hybrid_pipeline
        
        # Mock one component failure
        mock_neo4j.health_check.return_value = False
        mock_vector.health_check.return_value = True
        mock_openai.health_check.return_value = True
        
        status = pipeline.check_component_health()
        
        assert status["knowledge_graph"] is False
        assert status["vector_database"] is True
        assert status["openai_integration"] is True
        assert status["overall_healthy"] is False
    
    def test_request_validation(self, hybrid_pipeline):
        """Test validation of recommendation requests"""
        pipeline, mock_neo4j, mock_vector, mock_openai = hybrid_pipeline
        
        # Valid request
        valid_request = HybridRecommendationRequest(
            user_query="I need to cut wood planks for a deck",
            user_skill_level="intermediate",
            budget=500,
            workspace="garage",
            project_type="deck_building",
            safety_requirements=["OSHA_compliant"],
            preferred_brands=["DeWalt", "Makita"]
        )
        
        is_valid, errors = pipeline.validate_request(valid_request)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_request_validation(self, hybrid_pipeline):
        """Test validation of invalid recommendation requests"""
        pipeline, mock_neo4j, mock_vector, mock_openai = hybrid_pipeline
        
        # Invalid request (missing required fields)
        invalid_request = HybridRecommendationRequest(
            user_query="",  # Empty query
            user_skill_level="invalid_level",  # Invalid skill level
            budget=-100,  # Negative budget
            workspace="",  # Empty workspace
            project_type=""  # Empty project type
        )
        
        is_valid, errors = pipeline.validate_request(invalid_request)
        assert is_valid is False
        assert len(errors) > 0
        assert any("user_query" in error for error in errors)
        assert any("skill_level" in error for error in errors)
        assert any("budget" in error for error in errors)


class TestRecommendationEngine:
    """Test the core recommendation engine operations"""
    
    @pytest.fixture
    def recommendation_engine(self):
        """Create recommendation engine with mocked services"""
        mock_neo4j = MagicMock()
        mock_vector = MagicMock()
        mock_openai = MagicMock()
        
        engine = RecommendationEngine(
            knowledge_graph_service=mock_neo4j,
            vector_database_service=mock_vector,
            openai_service=mock_openai
        )
        
        return engine, mock_neo4j, mock_vector, mock_openai
    
    def test_knowledge_graph_recommendations(self, recommendation_engine):
        """Test getting recommendations from knowledge graph"""
        engine, mock_neo4j, mock_vector, mock_openai = recommendation_engine
        
        # Mock knowledge graph results
        mock_neo4j.find_tools_for_task.return_value = [
            {"name": "Circular Saw", "safety_rating": 4.2, "categories": ["cutting_tools"]},
            {"name": "Jigsaw", "safety_rating": 3.8, "categories": ["cutting_tools"]},
            {"name": "Hand Saw", "safety_rating": 3.5, "categories": ["hand_tools"]}
        ]
        
        request = HybridRecommendationRequest(
            user_query="cut wood planks",
            user_skill_level="intermediate",
            budget=300,
            workspace="garage",
            project_type="deck_building"
        )
        
        kg_results = engine.get_knowledge_graph_recommendations(request)
        
        # Verify knowledge graph was queried
        mock_neo4j.find_tools_for_task.assert_called_once()
        
        # Verify results structure
        assert len(kg_results) == 3
        assert kg_results[0]["name"] == "Circular Saw"
        assert kg_results[0]["source"] == "knowledge_graph"
        assert kg_results[0]["confidence_score"] > 0
    
    def test_vector_database_recommendations(self, recommendation_engine):
        """Test getting recommendations from vector database"""
        engine, mock_neo4j, mock_vector, mock_openai = recommendation_engine
        
        # Mock vector database results
        mock_vector.similarity_search_products.return_value = [
            {
                "product_code": "TOOL-001",
                "name": "DeWalt Circular Saw",
                "category": "cutting_tools",
                "similarity_score": 0.85,
                "price": 199.99
            },
            {
                "product_code": "TOOL-002", 
                "name": "Makita Jigsaw",
                "category": "cutting_tools",
                "similarity_score": 0.78,
                "price": 149.99
            }
        ]
        
        request = HybridRecommendationRequest(
            user_query="circular saw for cutting deck boards",
            user_skill_level="intermediate",
            budget=500,
            workspace="garage",
            project_type="deck_building"
        )
        
        vector_results = engine.get_vector_database_recommendations(request)
        
        # Verify vector database was queried
        mock_vector.similarity_search_products.assert_called_once()
        
        # Verify results structure
        assert len(vector_results) == 2
        assert vector_results[0]["name"] == "DeWalt Circular Saw"
        assert vector_results[0]["source"] == "vector_database"
        assert vector_results[0]["confidence_score"] == 0.85
    
    def test_openai_recommendations(self, recommendation_engine):
        """Test getting recommendations from OpenAI"""
        engine, mock_neo4j, mock_vector, mock_openai = recommendation_engine
        
        # Mock OpenAI response
        from core.models.openai_integration import ToolRecommendationResponse
        mock_response = ToolRecommendationResponse(
            recommendations=["circular_saw", "safety_glasses", "measuring_tape"],
            reasoning="For cutting wood planks, you'll need a circular saw for efficient cuts...",
            confidence_score=0.88,
            safety_notes=["Wear eye protection", "Ensure proper ventilation"],
            estimated_cost=275
        )
        mock_openai.get_tool_recommendations.return_value = mock_response
        
        request = HybridRecommendationRequest(
            user_query="I need to cut wood planks for building a deck",
            user_skill_level="intermediate",
            budget=500,
            workspace="garage",
            project_type="deck_building"
        )
        
        openai_results = engine.get_openai_recommendations(request)
        
        # Verify OpenAI was queried
        mock_openai.get_tool_recommendations.assert_called_once()
        
        # Verify results structure
        assert len(openai_results) == 3
        assert openai_results[0]["name"] == "circular_saw"
        assert openai_results[0]["source"] == "openai"
        assert openai_results[0]["confidence_score"] == 0.88
        assert openai_results[0]["reasoning"] is not None
    
    def test_safety_requirements_integration(self, recommendation_engine):
        """Test integration of safety requirements into recommendations"""
        engine, mock_neo4j, mock_vector, mock_openai = recommendation_engine
        
        # Mock safety assessment
        from core.models.openai_integration import SafetyAssessmentResponse
        mock_safety_response = SafetyAssessmentResponse(
            safety_score=8,
            required_ppe=["safety_glasses", "hearing_protection"],
            osha_compliance=["1926.95", "1926.52"],
            risk_factors=["flying_debris", "noise_exposure"],
            mitigation_strategies=["Use dust collection system"],
            training_required=False
        )
        mock_openai.assess_safety_requirements.return_value = mock_safety_response
        
        request = HybridRecommendationRequest(
            user_query="cut wood with power tools",
            user_skill_level="beginner",
            budget=300,
            workspace="garage",
            project_type="woodworking",
            safety_requirements=["OSHA_compliant"]
        )
        
        safety_results = engine.get_safety_recommendations(request)
        
        # Verify safety assessment was performed
        mock_openai.assess_safety_requirements.assert_called_once()
        
        # Verify safety results structure
        assert safety_results["safety_score"] == 8
        assert "safety_glasses" in safety_results["required_ppe"]
        assert "1926.95" in safety_results["osha_compliance"]
        assert not safety_results["training_required"]
    
    def test_parallel_component_execution(self, recommendation_engine):
        """Test parallel execution of all recommendation components"""
        engine, mock_neo4j, mock_vector, mock_openai = recommendation_engine
        
        # Mock all services to return results
        mock_neo4j.find_tools_for_task.return_value = [
            {"name": "KG Tool 1", "safety_rating": 4.0}
        ]
        mock_vector.similarity_search_products.return_value = [
            {"name": "Vector Tool 1", "similarity_score": 0.8}
        ]
        
        from core.models.openai_integration import ToolRecommendationResponse
        mock_openai.get_tool_recommendations.return_value = ToolRecommendationResponse(
            recommendations=["AI Tool 1"],
            reasoning="AI reasoning",
            confidence_score=0.9,
            safety_notes=[]
        )
        
        request = HybridRecommendationRequest(
            user_query="test query",
            user_skill_level="intermediate",
            budget=500,
            workspace="garage",
            project_type="test"
        )
        
        # Execute all components in parallel
        with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
            mock_future = MagicMock()
            mock_future.result.side_effect = [
                [{"name": "KG Tool 1", "source": "knowledge_graph"}],
                [{"name": "Vector Tool 1", "source": "vector_database"}],
                [{"name": "AI Tool 1", "source": "openai"}]
            ]
            mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future
            
            results = engine.get_all_recommendations_parallel(request)
        
        # Verify all components were executed
        assert len(results) == 3
        sources = [result["source"] for result in results]
        assert "knowledge_graph" in sources
        assert "vector_database" in sources  
        assert "openai" in sources


class TestResultMerger:
    """Test result merging and ranking algorithms"""
    
    @pytest.fixture
    def result_merger(self):
        """Create result merger for testing"""
        return ResultMerger(
            confidence_threshold=0.6,
            max_results=10,
            scoring_weights={
                "knowledge_graph": 0.3,
                "vector_database": 0.4,
                "openai": 0.3
            }
        )
    
    def test_result_deduplication(self, result_merger):
        """Test deduplication of results from multiple sources"""
        results = [
            {
                "name": "Circular Saw",
                "source": "knowledge_graph",
                "confidence_score": 0.8,
                "details": {"kg_specific": "data"}
            },
            {
                "name": "Circular Saw",  # Duplicate
                "source": "vector_database",
                "confidence_score": 0.85,
                "details": {"vector_specific": "data"}
            },
            {
                "name": "Jigsaw",
                "source": "openai",
                "confidence_score": 0.75,
                "details": {"ai_specific": "data"}
            }
        ]
        
        deduplicated = result_merger.deduplicate_results(results)
        
        # Should have 2 unique tools
        assert len(deduplicated) == 2
        tool_names = [result["name"] for result in deduplicated]
        assert "Circular Saw" in tool_names
        assert "Jigsaw" in tool_names
        
        # Circular saw should have merged data from both sources
        circular_saw = next(r for r in deduplicated if r["name"] == "Circular Saw")
        assert "sources" in circular_saw
        assert len(circular_saw["sources"]) == 2
    
    def test_confidence_scoring(self, result_merger):
        """Test confidence score calculation for merged results"""
        merged_result = {
            "name": "Circular Saw",
            "sources": [
                {"source": "knowledge_graph", "confidence_score": 0.8, "weight": 0.3},
                {"source": "vector_database", "confidence_score": 0.85, "weight": 0.4},
                {"source": "openai", "confidence_score": 0.9, "weight": 0.3}
            ]
        }
        
        final_confidence = result_merger.calculate_weighted_confidence(merged_result)
        
        # Expected: (0.8 * 0.3) + (0.85 * 0.4) + (0.9 * 0.3) = 0.85
        expected_confidence = (0.8 * 0.3) + (0.85 * 0.4) + (0.9 * 0.3)
        assert abs(final_confidence - expected_confidence) < 0.01
    
    def test_ranking_algorithm(self, result_merger):
        """Test ranking algorithm for final recommendations"""
        results = [
            {
                "name": "Tool A",
                "weighted_confidence": 0.85,
                "safety_score": 8,
                "price": 200,
                "user_rating": 4.5
            },
            {
                "name": "Tool B", 
                "weighted_confidence": 0.75,
                "safety_score": 9,
                "price": 150,
                "user_rating": 4.8
            },
            {
                "name": "Tool C",
                "weighted_confidence": 0.9,
                "safety_score": 7,
                "price": 300,
                "user_rating": 4.2
            }
        ]
        
        ranked_results = result_merger.rank_results(results)
        
        # Verify results are properly ranked
        assert len(ranked_results) == 3
        
        # First result should have highest overall score
        assert ranked_results[0]["final_rank"] == 1
        assert ranked_results[1]["final_rank"] == 2
        assert ranked_results[2]["final_rank"] == 3
        
        # Verify ranking factors are considered
        for result in ranked_results:
            assert "ranking_score" in result
            assert result["ranking_score"] > 0
    
    def test_budget_filtering(self, result_merger):
        """Test filtering results based on budget constraints"""
        results = [
            {"name": "Expensive Tool", "price": 800, "confidence_score": 0.9},
            {"name": "Moderate Tool", "price": 400, "confidence_score": 0.8},
            {"name": "Budget Tool", "price": 150, "confidence_score": 0.7}
        ]
        
        budget = 500
        filtered_results = result_merger.filter_by_budget(results, budget)
        
        # Should only include tools within budget
        assert len(filtered_results) == 2
        tool_names = [result["name"] for result in filtered_results]
        assert "Moderate Tool" in tool_names
        assert "Budget Tool" in tool_names
        assert "Expensive Tool" not in tool_names
    
    def test_skill_level_filtering(self, result_merger):
        """Test filtering results based on user skill level"""
        results = [
            {
                "name": "Professional Tool",
                "difficulty_level": "advanced",
                "confidence_score": 0.9
            },
            {
                "name": "Intermediate Tool",
                "difficulty_level": "intermediate", 
                "confidence_score": 0.8
            },
            {
                "name": "Beginner Tool",
                "difficulty_level": "beginner",
                "confidence_score": 0.7
            }
        ]
        
        user_skill_level = "intermediate"
        filtered_results = result_merger.filter_by_skill_level(results, user_skill_level)
        
        # Should include tools appropriate for intermediate and below
        assert len(filtered_results) == 2
        tool_names = [result["name"] for result in filtered_results]
        assert "Intermediate Tool" in tool_names
        assert "Beginner Tool" in tool_names
        assert "Professional Tool" not in tool_names
    
    def test_confidence_threshold_filtering(self, result_merger):
        """Test filtering results based on confidence threshold"""
        results = [
            {"name": "High Confidence Tool", "confidence_score": 0.85},
            {"name": "Medium Confidence Tool", "confidence_score": 0.65},
            {"name": "Low Confidence Tool", "confidence_score": 0.45}
        ]
        
        # Result merger has confidence_threshold=0.6
        filtered_results = result_merger.filter_by_confidence(results)
        
        # Should only include tools above threshold
        assert len(filtered_results) == 2
        tool_names = [result["name"] for result in filtered_results]
        assert "High Confidence Tool" in tool_names
        assert "Medium Confidence Tool" in tool_names
        assert "Low Confidence Tool" not in tool_names


class TestHybridRecommendationWorkflow:
    """Test complete hybrid recommendation workflow"""
    
    @pytest.fixture
    def complete_pipeline(self):
        """Create complete pipeline with all mocked services"""
        mock_neo4j = MagicMock()
        mock_vector = MagicMock()
        mock_openai = MagicMock()
        
        # Mock knowledge graph results
        mock_neo4j.find_tools_for_task.return_value = [
            {"name": "Circular Saw", "safety_rating": 4.2, "price": 199.99}
        ]
        
        # Mock vector database results
        mock_vector.similarity_search_products.return_value = [
            {"name": "DeWalt Circular Saw", "similarity_score": 0.85, "price": 199.99}
        ]
        
        # Mock OpenAI results
        from core.models.openai_integration import ToolRecommendationResponse
        mock_openai.get_tool_recommendations.return_value = ToolRecommendationResponse(
            recommendations=["circular_saw", "safety_glasses"],
            reasoning="For deck building, you need reliable cutting tools",
            confidence_score=0.88,
            safety_notes=["Wear eye protection"],
            estimated_cost=250
        )
        
        pipeline = HybridRecommendationPipeline(
            knowledge_graph_service=mock_neo4j,
            vector_database_service=mock_vector,
            openai_service=mock_openai
        )
        
        return pipeline, mock_neo4j, mock_vector, mock_openai
    
    def test_complete_recommendation_workflow(self, complete_pipeline):
        """Test complete end-to-end recommendation workflow"""
        pipeline, mock_neo4j, mock_vector, mock_openai = complete_pipeline
        
        request = HybridRecommendationRequest(
            user_query="I need tools to build a deck in my backyard",
            user_skill_level="intermediate",
            budget=800,
            workspace="backyard",
            project_type="deck_building",
            safety_requirements=["OSHA_compliant"],
            preferred_brands=["DeWalt", "Makita"]
        )
        
        response = pipeline.get_recommendations(request)
        
        # Verify all components were called
        mock_neo4j.find_tools_for_task.assert_called()
        mock_vector.similarity_search_products.assert_called()
        mock_openai.get_tool_recommendations.assert_called()
        
        # Verify response structure
        assert isinstance(response, HybridRecommendationResponse)
        assert len(response.recommendations) > 0
        assert response.total_confidence > 0
        assert response.processing_time_ms > 0
        assert len(response.component_scores) == 3
        
        # Verify each recommendation has required fields
        for recommendation in response.recommendations:
            assert "name" in recommendation
            assert "confidence_score" in recommendation
            assert "sources" in recommendation
            assert "price" in recommendation
    
    def test_caching_mechanism(self, complete_pipeline):
        """Test caching mechanism for repeated requests"""
        pipeline, mock_neo4j, mock_vector, mock_openai = complete_pipeline
        
        request = HybridRecommendationRequest(
            user_query="circular saw recommendations",
            user_skill_level="intermediate",
            budget=500,
            workspace="garage",
            project_type="woodworking"
        )
        
        # First request - should hit all services
        response1 = pipeline.get_recommendations(request)
        first_call_count = mock_neo4j.find_tools_for_task.call_count
        
        # Second identical request - should use cache
        response2 = pipeline.get_recommendations(request)  
        second_call_count = mock_neo4j.find_tools_for_task.call_count
        
        # Verify caching worked
        assert first_call_count == second_call_count  # No additional calls
        assert response1.recommendations == response2.recommendations
        assert response2.from_cache is True
    
    def test_fallback_mechanism(self, complete_pipeline):
        """Test fallback mechanism when components fail"""
        pipeline, mock_neo4j, mock_vector, mock_openai = complete_pipeline
        
        # Mock one component failure
        mock_neo4j.find_tools_for_task.side_effect = Exception("Neo4j connection failed")
        
        request = HybridRecommendationRequest(
            user_query="tool recommendations",
            user_skill_level="intermediate",
            budget=500,
            workspace="garage",
            project_type="general"
        )
        
        response = pipeline.get_recommendations(request)
        
        # Should still get recommendations from working components
        assert isinstance(response, HybridRecommendationResponse)
        assert len(response.recommendations) > 0
        assert "knowledge_graph" not in [score.component for score in response.component_scores]
        assert len(response.warnings) > 0
        assert any("Neo4j" in warning for warning in response.warnings)


class TestHybridRecommendationPerformance:
    """Test performance requirements for hybrid recommendation pipeline"""
    
    @pytest.fixture
    def fast_pipeline(self):
        """Create pipeline with fast mocked responses"""
        mock_neo4j = MagicMock()
        mock_vector = MagicMock()
        mock_openai = MagicMock()
        
        # Mock fast responses
        mock_neo4j.find_tools_for_task.return_value = [{"name": "Tool 1", "price": 100}]
        mock_vector.similarity_search_products.return_value = [{"name": "Tool 1", "similarity_score": 0.8}]
        
        from core.models.openai_integration import ToolRecommendationResponse
        mock_openai.get_tool_recommendations.return_value = ToolRecommendationResponse(
            recommendations=["tool_1"],
            reasoning="Fast response",
            confidence_score=0.8,
            safety_notes=[]
        )
        
        pipeline = HybridRecommendationPipeline(
            knowledge_graph_service=mock_neo4j,
            vector_database_service=mock_vector,
            openai_service=mock_openai
        )
        
        return pipeline
    
    def test_recommendation_pipeline_performance(self, fast_pipeline, performance_monitor):
        """Test that complete recommendation pipeline meets <2s requirement"""
        pipeline = fast_pipeline
        
        request = HybridRecommendationRequest(
            user_query="Performance test query",
            user_skill_level="intermediate",
            budget=500,
            workspace="garage", 
            project_type="test"
        )
        
        # Measure performance
        performance_monitor.start("hybrid_pipeline")
        response = pipeline.get_recommendations(request)
        duration = performance_monitor.stop("hybrid_pipeline")
        
        # Assert performance requirement - hybrid pipeline gets 2s budget
        performance_monitor.assert_within_threshold(2.0, "hybrid_pipeline")
        assert response is not None
        assert len(response.recommendations) > 0
    
    def test_parallel_execution_performance(self, fast_pipeline, performance_monitor):
        """Test that parallel execution improves performance"""
        pipeline = fast_pipeline
        
        request = HybridRecommendationRequest(
            user_query="Parallel execution test",
            user_skill_level="intermediate",
            budget=500,
            workspace="garage",
            project_type="test"
        )
        
        # Test parallel execution
        performance_monitor.start("parallel_execution")
        response = pipeline.get_recommendations_parallel(request)
        duration = performance_monitor.stop("parallel_execution")
        
        # Should be significantly faster than sequential
        performance_monitor.assert_within_threshold(1.0, "parallel_execution")
        assert response is not None
    
    def test_caching_performance_improvement(self, fast_pipeline, performance_monitor):
        """Test that caching provides significant performance improvement"""
        pipeline = fast_pipeline
        
        request = HybridRecommendationRequest(
            user_query="Caching test query",
            user_skill_level="intermediate",
            budget=500,
            workspace="garage",
            project_type="test"
        )
        
        # First request (cache miss)
        performance_monitor.start("cache_miss")
        response1 = pipeline.get_recommendations(request)
        cache_miss_duration = performance_monitor.stop("cache_miss")
        
        # Second request (cache hit)
        performance_monitor.start("cache_hit")
        response2 = pipeline.get_recommendations(request)
        cache_hit_duration = performance_monitor.stop("cache_hit")
        
        # Cache hit should be much faster
        assert cache_hit_duration < cache_miss_duration * 0.1  # At least 10x faster
        assert response2.from_cache is True


class TestHybridRecommendationModels:
    """Test data models for hybrid recommendations"""
    
    def test_hybrid_recommendation_request_model(self):
        """Test HybridRecommendationRequest model validation"""
        request = HybridRecommendationRequest(
            user_query="I need tools for deck building",
            user_skill_level="intermediate",
            budget=800,
            workspace="backyard",
            project_type="deck_building",
            safety_requirements=["OSHA_compliant"],
            preferred_brands=["DeWalt", "Makita"],
            existing_tools=["drill", "measuring_tape"],
            timeline="2_weeks"
        )
        
        assert request.user_query == "I need tools for deck building"
        assert request.user_skill_level == "intermediate"
        assert request.budget == 800
        assert len(request.preferred_brands) == 2
        assert len(request.existing_tools) == 2
        
        # Test serialization
        request_dict = request.to_dict()
        assert request_dict["user_query"] == "I need tools for deck building"
        assert request_dict["budget"] == 800
    
    def test_hybrid_recommendation_response_model(self):
        """Test HybridRecommendationResponse model validation"""
        component_scores = [
            ComponentScore(component="knowledge_graph", score=0.8, weight=0.3),
            ComponentScore(component="vector_database", score=0.85, weight=0.4),
            ComponentScore(component="openai", score=0.9, weight=0.3)
        ]
        
        recommendations = [
            RecommendationResult(
                name="Circular Saw",
                confidence_score=0.85,
                sources=["knowledge_graph", "vector_database"],
                price=199.99,
                safety_rating=4.2
            )
        ]
        
        response = HybridRecommendationResponse(
            recommendations=recommendations,
            total_confidence=0.85,
            component_scores=component_scores,
            processing_time_ms=1250,
            from_cache=False,
            warnings=[]
        )
        
        assert len(response.recommendations) == 1
        assert response.total_confidence == 0.85
        assert len(response.component_scores) == 3
        assert response.processing_time_ms == 1250
        assert not response.from_cache
    
    def test_confidence_metrics_model(self):
        """Test ConfidenceMetrics model for tracking confidence calculations"""
        metrics = ConfidenceMetrics(
            knowledge_graph_confidence=0.8,
            vector_database_confidence=0.85,
            openai_confidence=0.9,
            weighted_confidence=0.85,
            consensus_score=0.88,
            uncertainty_score=0.12
        )
        
        assert metrics.knowledge_graph_confidence == 0.8
        assert metrics.weighted_confidence == 0.85
        assert metrics.consensus_score == 0.88
        assert metrics.uncertainty_score == 0.12
    
    def test_invalid_confidence_scores(self):
        """Test validation of confidence score ranges"""
        with pytest.raises(ValueError):
            ComponentScore(
                component="test",
                score=1.5,  # Should be 0.0-1.0
                weight=0.3
            )
        
        with pytest.raises(ValueError):
            ComponentScore(
                component="test",
                score=0.8,
                weight=1.5  # Should be 0.0-1.0
            )


if __name__ == "__main__":
    # Run unit tests with performance monitoring
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--durations=10",
        "-m", "unit"
    ])