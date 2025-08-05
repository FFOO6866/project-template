"""
Unit Tests for OpenAI GPT-4 Integration
======================================

Tests the OpenAI GPT-4 integration service with mocking for fast unit tests.
Validates prompt templating, response parsing, and error handling.

Test Coverage:
- OpenAI client initialization and configuration
- Prompt template management and generation
- Response parsing and validation
- Tool recommendation analysis
- Safety assessment and compliance
- Error handling and rate limiting
- Performance constraints (<1s per test)
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional

# Test framework imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import windows_patch  # Apply Windows compatibility for Kailash SDK

# Import the service under test (will be implemented)
from src.new_project.core.services.openai_integration import OpenAIIntegrationService, PromptTemplates
from src.new_project.core.models.openai_integration import (
    ToolRecommendationRequest, ToolRecommendationResponse,
    SafetyAssessmentRequest, SafetyAssessmentResponse,
    ProjectAnalysisRequest, ProjectAnalysisResponse
)


class TestPromptTemplates:
    """Test prompt template management and generation"""
    
    def test_prompt_template_initialization(self):
        """Test that all required prompt templates are defined"""
        templates = PromptTemplates()
        
        expected_templates = [
            "tool_recommendation", "safety_assessment", "project_analysis",
            "requirement_analysis", "compatibility_check", "skill_assessment"
        ]
        
        available_templates = templates.get_available_templates()
        
        assert set(expected_templates) == set(available_templates), \
            f"Expected templates {expected_templates}, got {available_templates}"
    
    def test_tool_recommendation_template(self):
        """Test tool recommendation prompt template"""
        templates = PromptTemplates()
        
        request_data = {
            "task": "Cut wood planks for deck construction",
            "user_skill_level": "intermediate",
            "budget": 500,
            "workspace": "garage",
            "project_type": "deck_building"
        }
        
        prompt = templates.generate_prompt("tool_recommendation", request_data)
        
        assert "tool recommendation" in prompt.lower()
        assert "cut wood planks" in prompt.lower()
        assert "intermediate" in prompt
        assert "500" in prompt
        assert "deck construction" in prompt
    
    def test_safety_assessment_template(self):
        """Test safety assessment prompt template"""
        templates = PromptTemplates()
        
        request_data = {
            "tools": ["circular_saw", "drill", "safety_glasses"],
            "task": "Cut wood planks",
            "user_experience": "beginner",
            "workspace_conditions": "indoor_garage"
        }
        
        prompt = templates.generate_prompt("safety_assessment", request_data)
        
        assert "safety assessment" in prompt.lower()
        assert "circular_saw" in prompt
        assert "beginner" in prompt
        assert "OSHA" in prompt or "safety" in prompt
    
    def test_project_analysis_template(self):
        """Test project analysis prompt template"""
        templates = PromptTemplates()
        
        request_data = {
            "project_description": "Build a 10x12 foot deck with railing",
            "materials": ["pressure_treated_lumber", "deck_screws", "railing_posts"],
            "timeline": "2_weeks",
            "budget": 1500
        }
        
        prompt = templates.generate_prompt("project_analysis", request_data)
        
        assert "project analysis" in prompt.lower()
        assert "10x12" in prompt
        assert "deck" in prompt
        assert "1500" in prompt
    
    def test_requirement_analysis_template(self):
        """Test requirement analysis prompt template"""
        templates = PromptTemplates()
        
        request_data = {
            "user_query": "I need to build shelves in my closet",
            "space_dimensions": "6ft x 3ft x 8ft",
            "load_requirements": "books and storage boxes",
            "skill_level": "beginner"
        }
        
        prompt = templates.generate_prompt("requirement_analysis", request_data)
        
        assert "requirement analysis" in prompt.lower()
        assert "shelves" in prompt
        assert "6ft x 3ft x 8ft" in prompt
        assert "beginner" in prompt
    
    def test_compatibility_check_template(self):
        """Test compatibility check prompt template"""
        templates = PromptTemplates()
        
        request_data = {
            "primary_tool": "circular_saw",
            "additional_tools": ["saw_guide", "clamps", "measuring_tape"],
            "task": "precise wood cutting",
            "materials": ["plywood", "2x4_lumber"]
        }
        
        prompt = templates.generate_prompt("compatibility_check", request_data)
        
        assert "compatibility" in prompt.lower()
        assert "circular_saw" in prompt
        assert "saw_guide" in prompt
        assert "precise wood cutting" in prompt
    
    def test_skill_assessment_template(self):
        """Test skill assessment prompt template"""
        templates = PromptTemplates()
        
        request_data = {
            "proposed_task": "Install hardwood flooring",
            "user_experience": ["basic_carpentry", "painting", "tile_work"],
            "available_tools": ["miter_saw", "nail_gun", "level"],
            "project_timeline": "1_week"
        }
        
        prompt = templates.generate_prompt("skill_assessment", request_data)
        
        assert "skill assessment" in prompt.lower()
        assert "hardwood flooring" in prompt
        assert "basic_carpentry" in prompt
        assert "miter_saw" in prompt
    
    def test_invalid_template_name(self):
        """Test error handling for invalid template names"""
        templates = PromptTemplates()
        
        with pytest.raises(ValueError) as exc_info:
            templates.generate_prompt("invalid_template", {})
        
        assert "invalid template" in str(exc_info.value).lower()
    
    def test_missing_template_variables(self):
        """Test error handling for missing template variables"""
        templates = PromptTemplates()
        
        # Missing required variables for tool_recommendation template
        incomplete_data = {
            "task": "Cut wood"
            # Missing: user_skill_level, budget, workspace, project_type
        }
        
        with pytest.raises(ValueError) as exc_info:
            templates.generate_prompt("tool_recommendation", incomplete_data)
        
        assert "missing required" in str(exc_info.value).lower()


class TestOpenAIIntegrationService:
    """Test OpenAI integration service operations with mocking"""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for unit tests"""
        with patch('core.services.openai_integration.openai.OpenAI') as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            
            # Mock successful API response
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "recommendations": ["circular_saw", "safety_glasses"],
                "reasoning": "Based on the task requirements...",
                "confidence_score": 0.85,
                "safety_notes": ["Wear eye protection", "Ensure proper ventilation"]
            })
            mock_response.usage.total_tokens = 150
            
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            yield mock_client, mock_response
    
    @pytest.fixture
    def openai_service(self, mock_openai_client):
        """Create OpenAI integration service with mocked client"""
        mock_client, mock_response = mock_openai_client
        
        service = OpenAIIntegrationService(
            api_key="test_api_key",
            model="gpt-4",
            max_tokens=1000,
            temperature=0.7
        )
        return service, mock_client
    
    def test_service_initialization(self, openai_service):
        """Test service initializes with proper configuration"""
        service, mock_client = openai_service
        
        assert service is not None
        assert service.model == "gpt-4"
        assert service.max_tokens == 1000
        assert service.temperature == 0.7
        assert hasattr(service, 'client')
        assert hasattr(service, 'templates')
    
    def test_tool_recommendation_analysis(self, openai_service):
        """Test tool recommendation analysis"""
        service, mock_client = openai_service
        
        request = ToolRecommendationRequest(
            task="Cut wood planks for deck construction",
            user_skill_level="intermediate",
            budget=500,
            workspace="garage",
            project_type="deck_building",
            preferred_brands=["DeWalt", "Makita"],
            existing_tools=["drill", "measuring_tape"]
        )
        
        response = service.get_tool_recommendations(request)
        
        # Verify OpenAI API was called
        mock_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_client.chat.completions.create.call_args
        
        assert kwargs["model"] == "gpt-4"
        assert kwargs["max_tokens"] == 1000
        assert kwargs["temperature"] == 0.7
        assert "messages" in kwargs
        
        # Verify prompt contains request data
        prompt_content = kwargs["messages"][0]["content"]
        assert "cut wood planks" in prompt_content.lower()
        assert "intermediate" in prompt_content.lower()
        assert "500" in prompt_content
        
        # Verify response structure
        assert isinstance(response, ToolRecommendationResponse)
        assert len(response.recommendations) == 2
        assert "circular_saw" in response.recommendations
        assert response.confidence_score == 0.85
        assert len(response.safety_notes) == 2
    
    def test_safety_assessment_analysis(self, openai_service):
        """Test safety assessment analysis"""
        service, mock_client = openai_service
        
        # Mock safety assessment response
        mock_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "safety_score": 8,
            "required_ppe": ["safety_glasses", "hearing_protection"],
            "osha_compliance": ["1926.95", "1926.52"],
            "risk_factors": ["flying_debris", "noise_exposure"],
            "mitigation_strategies": ["Use dust collection", "Maintain tool properly"],
            "training_required": False
        })
        
        request = SafetyAssessmentRequest(
            tools=["circular_saw", "drill"],
            task="Cut and assemble deck frame",
            user_experience="intermediate", 
            workspace_conditions="outdoor_deck_area",
            materials=["pressure_treated_lumber"]
        )
        
        response = service.assess_safety_requirements(request)
        
        # Verify OpenAI API was called
        mock_client.chat.completions.create.assert_called_once()
        
        # Verify response structure
        assert isinstance(response, SafetyAssessmentResponse)
        assert response.safety_score == 8
        assert "safety_glasses" in response.required_ppe
        assert "1926.95" in response.osha_compliance
        assert len(response.risk_factors) == 2
        assert not response.training_required
    
    def test_project_analysis(self, openai_service):
        """Test project complexity and timeline analysis"""
        service, mock_client = openai_service
        
        # Mock project analysis response
        mock_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "complexity_score": 6,
            "estimated_time_hours": 24,
            "skill_level_required": "intermediate",
            "critical_steps": ["Foundation preparation", "Frame assembly", "Deck board installation"],
            "potential_challenges": ["Weather dependency", "Permit requirements"],
            "recommended_sequence": ["Planning", "Foundation", "Frame", "Decking", "Railing"],
            "cost_estimate": 1200
        })
        
        request = ProjectAnalysisRequest(
            project_description="Build a 12x16 foot deck with composite decking and metal railing", 
            materials=["composite_decking", "metal_railing", "concrete_footings"],
            timeline="3_weeks",
            budget=2000,
            user_skill_level="intermediate"
        )
        
        response = service.analyze_project_complexity(request)
        
        # Verify OpenAI API was called
        mock_client.chat.completions.create.assert_called_once()
        
        # Verify response structure
        assert isinstance(response, ProjectAnalysisResponse)
        assert response.complexity_score == 6
        assert response.estimated_time_hours == 24
        assert response.skill_level_required == "intermediate"
        assert len(response.critical_steps) == 3
        assert response.cost_estimate == 1200
    
    def test_natural_language_query_processing(self, openai_service):
        """Test processing natural language queries"""
        service, mock_client = openai_service
        
        # Mock query processing response
        mock_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "intent": "tool_recommendation",
            "extracted_requirements": {
                "task": "drill holes",
                "material": "concrete",
                "hole_size": "1/2 inch",
                "quantity": "multiple"
            },
            "clarifying_questions": ["What is the concrete thickness?", "Indoor or outdoor use?"],
            "confidence": 0.9
        })
        
        query = "I need to drill some half-inch holes in concrete for mounting brackets"
        
        response = service.process_natural_language_query(query)
        
        # Verify OpenAI API was called
        mock_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_client.chat.completions.create.call_args
        
        # Verify query is in prompt
        prompt_content = kwargs["messages"][0]["content"]
        assert "drill" in prompt_content.lower()
        assert "concrete" in prompt_content.lower()
        
        # Verify response structure
        assert response["intent"] == "tool_recommendation"
        assert response["extracted_requirements"]["task"] == "drill holes"
        assert response["confidence"] == 0.9
        assert len(response["clarifying_questions"]) == 2
    
    def test_response_validation_and_parsing(self, openai_service):
        """Test response validation and parsing"""
        service, mock_client = openai_service
        
        # Test with valid JSON response
        valid_response = json.dumps({
            "recommendations": ["tool1", "tool2"],
            "confidence_score": 0.8,
            "reasoning": "Valid reasoning"
        })
        mock_client.chat.completions.create.return_value.choices[0].message.content = valid_response
        
        request = ToolRecommendationRequest(
            task="test task",
            user_skill_level="beginner",
            budget=100,
            workspace="garage",
            project_type="test"
        )
        
        response = service.get_tool_recommendations(request)
        assert response.confidence_score == 0.8
    
    def test_error_handling_invalid_json_response(self, openai_service):
        """Test error handling for invalid JSON responses"""
        service, mock_client = openai_service
        
        # Mock invalid JSON response
        mock_client.chat.completions.create.return_value.choices[0].message.content = "Invalid JSON response"
        
        request = ToolRecommendationRequest(
            task="test task",
            user_skill_level="beginner",
            budget=100,
            workspace="garage",
            project_type="test"
        )
        
        with pytest.raises(ValueError) as exc_info:
            service.get_tool_recommendations(request)
        
        assert "invalid json" in str(exc_info.value).lower()
    
    def test_error_handling_api_failure(self, openai_service):
        """Test error handling for OpenAI API failures"""
        service, mock_client = openai_service
        
        # Mock API failure
        mock_client.chat.completions.create.side_effect = Exception("API rate limit exceeded")
        
        request = ToolRecommendationRequest(
            task="test task",
            user_skill_level="beginner",
            budget=100,
            workspace="garage",
            project_type="test"
        )
        
        with pytest.raises(Exception) as exc_info:
            service.get_tool_recommendations(request)
        
        assert "API rate limit exceeded" in str(exc_info.value)
    
    def test_rate_limiting_and_retry_logic(self, openai_service):
        """Test rate limiting and retry logic"""
        service, mock_client = openai_service
        
        # Mock rate limit error followed by success
        rate_limit_error = Exception("Rate limit exceeded")
        success_response = MagicMock()
        success_response.choices = [MagicMock()]
        success_response.choices[0].message.content = json.dumps({
            "recommendations": ["tool1"],
            "confidence_score": 0.8,
            "reasoning": "Success after retry"
        })
        
        mock_client.chat.completions.create.side_effect = [rate_limit_error, success_response]
        
        request = ToolRecommendationRequest(
            task="test task",
            user_skill_level="beginner",
            budget=100,
            workspace="garage",
            project_type="test"
        )
        
        with patch('time.sleep'):  # Mock sleep for faster testing
            response = service.get_tool_recommendations_with_retry(request, max_retries=2)
        
        # Verify retry was attempted
        assert mock_client.chat.completions.create.call_count == 2
        assert response.confidence_score == 0.8
    
    def test_token_usage_tracking(self, openai_service):
        """Test token usage tracking and optimization"""
        service, mock_client = openai_service
        
        # Mock response with token usage
        mock_client.chat.completions.create.return_value.usage.total_tokens = 250
        mock_client.chat.completions.create.return_value.usage.prompt_tokens = 200
        mock_client.chat.completions.create.return_value.usage.completion_tokens = 50
        
        request = ToolRecommendationRequest(
            task="test task",
            user_skill_level="beginner",
            budget=100,
            workspace="garage",
            project_type="test"
        )
        
        response = service.get_tool_recommendations(request)
        
        # Verify token usage is tracked
        usage_stats = service.get_token_usage_stats()
        assert usage_stats["total_tokens"] >= 250
        assert usage_stats["requests_made"] >= 1
    
    def test_prompt_optimization(self, openai_service):
        """Test prompt length optimization and truncation"""
        service, mock_client = openai_service
        
        # Test with very long task description
        request = ToolRecommendationRequest(
            task="A" * 5000,  # Very long task description
            user_skill_level="beginner",
            budget=100,
            workspace="garage",
            project_type="test"
        )
        
        service.get_tool_recommendations(request)
        
        # Verify prompt was optimized/truncated
        args, kwargs = mock_client.chat.completions.create.call_args
        prompt_content = kwargs["messages"][0]["content"]
        assert len(prompt_content) < 4000  # Should be truncated


class TestOpenAIIntegrationPerformance:
    """Test performance requirements for OpenAI integration"""
    
    @pytest.fixture
    def openai_service(self):
        """Create OpenAI service with mocked fast responses"""
        with patch('core.services.openai_integration.openai.OpenAI') as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            
            # Mock fast response
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "recommendations": ["tool1"],
                "confidence_score": 0.8,
                "reasoning": "Fast response"
            })
            mock_response.usage.total_tokens = 100
            
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            service = OpenAIIntegrationService(api_key="test_key")
            return service, mock_client
    
    def test_tool_recommendation_performance(self, openai_service, performance_monitor):
        """Test that tool recommendations complete within performance threshold"""
        service, mock_client = openai_service
        
        request = ToolRecommendationRequest(
            task="Performance test task",
            user_skill_level="intermediate", 
            budget=500,
            workspace="garage",
            project_type="test"
        )
        
        # Measure performance
        performance_monitor.start("tool_recommendation")
        response = service.get_tool_recommendations(request)
        duration = performance_monitor.stop("tool_recommendation")
        
        # Assert performance requirement
        performance_monitor.assert_within_threshold(1.0, "tool_recommendation")
        assert response is not None
    
    def test_safety_assessment_performance(self, openai_service, performance_monitor):
        """Test that safety assessments complete within performance threshold"""
        service, mock_client = openai_service
        
        # Mock safety response
        mock_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "safety_score": 8,
            "required_ppe": ["safety_glasses"],
            "osha_compliance": ["1926.95"],
            "risk_factors": ["debris"],
            "mitigation_strategies": ["use protection"],
            "training_required": False
        })
        
        request = SafetyAssessmentRequest(
            tools=["circular_saw"],
            task="Cut wood",
            user_experience="intermediate",
            workspace_conditions="garage",
            materials=["wood"]
        )
        
        # Measure performance
        performance_monitor.start("safety_assessment")
        response = service.assess_safety_requirements(request)
        duration = performance_monitor.stop("safety_assessment")
        
        # Assert performance requirement
        performance_monitor.assert_within_threshold(1.0, "safety_assessment")
        assert response is not None
    
    def test_query_processing_performance(self, openai_service, performance_monitor):
        """Test that natural language query processing meets performance requirements"""
        service, mock_client = openai_service
        
        # Mock query processing response
        mock_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "intent": "tool_recommendation",
            "extracted_requirements": {"task": "drill"},
            "confidence": 0.9
        })
        
        query = "I need to drill holes in wood"
        
        # Measure performance
        performance_monitor.start("query_processing")
        response = service.process_natural_language_query(query)
        duration = performance_monitor.stop("query_processing")
        
        # Assert performance requirement
        performance_monitor.assert_within_threshold(1.0, "query_processing")
        assert response is not None


class TestOpenAIIntegrationModels:
    """Test data models for OpenAI integration"""
    
    def test_tool_recommendation_request_model(self):
        """Test ToolRecommendationRequest model validation"""
        request = ToolRecommendationRequest(
            task="Cut wood planks",
            user_skill_level="intermediate",
            budget=500,
            workspace="garage",
            project_type="deck_building",
            preferred_brands=["DeWalt"],
            existing_tools=["drill"]
        )
        
        assert request.task == "Cut wood planks"
        assert request.user_skill_level == "intermediate"
        assert request.budget == 500
        assert len(request.preferred_brands) == 1
        
        # Test serialization
        request_dict = request.to_dict()
        assert request_dict["task"] == "Cut wood planks"
        assert request_dict["budget"] == 500
    
    def test_tool_recommendation_response_model(self):
        """Test ToolRecommendationResponse model validation"""
        response = ToolRecommendationResponse(
            recommendations=["circular_saw", "safety_glasses"],
            reasoning="Based on the cutting task requirements...",
            confidence_score=0.85,
            safety_notes=["Wear eye protection"],
            estimated_cost=250,
            alternative_options=["hand_saw"]
        )
        
        assert len(response.recommendations) == 2
        assert response.confidence_score == 0.85
        assert response.estimated_cost == 250
        assert "circular_saw" in response.recommendations
    
    def test_safety_assessment_request_model(self):
        """Test SafetyAssessmentRequest model validation"""
        request = SafetyAssessmentRequest(
            tools=["circular_saw", "drill"],
            task="Cut and assemble deck frame",
            user_experience="intermediate",
            workspace_conditions="outdoor_deck_area",
            materials=["pressure_treated_lumber"]
        )
        
        assert len(request.tools) == 2
        assert request.task == "Cut and assemble deck frame"
        assert request.user_experience == "intermediate"
        assert "circular_saw" in request.tools
    
    def test_safety_assessment_response_model(self):
        """Test SafetyAssessmentResponse model validation"""
        response = SafetyAssessmentResponse(
            safety_score=8,
            required_ppe=["safety_glasses", "hearing_protection"],
            osha_compliance=["1926.95", "1926.52"],
            risk_factors=["flying_debris", "noise_exposure"],
            mitigation_strategies=["Use dust collection"],
            training_required=False
        )
        
        assert response.safety_score == 8
        assert len(response.required_ppe) == 2
        assert len(response.osha_compliance) == 2
        assert not response.training_required
    
    def test_invalid_skill_level(self):
        """Test validation of skill level values"""
        with pytest.raises(ValueError):
            ToolRecommendationRequest(
                task="test task",
                user_skill_level="invalid_level",  # Should be beginner, intermediate, or advanced
                budget=100,
                workspace="garage",
                project_type="test"
            )
    
    def test_invalid_confidence_score(self):
        """Test validation of confidence score range"""
        with pytest.raises(ValueError):
            ToolRecommendationResponse(
                recommendations=["tool1"],
                reasoning="test",
                confidence_score=1.5,  # Should be 0.0-1.0
                safety_notes=[]
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