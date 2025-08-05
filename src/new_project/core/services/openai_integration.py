"""
OpenAI GPT-4 Integration Service
===============================

Service for managing OpenAI GPT-4 integration including prompt templating,
response parsing, and intelligent analysis.
"""

from typing import Dict, List, Any, Optional
import logging
import json
import time
from dataclasses import dataclass

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    # Mock classes for development/testing
    class openai:
        class OpenAI:
            def __init__(self, api_key: str = None):
                self.chat = MockChat()
        
        class ChatCompletion:
            pass
    
    class MockChat:
        def __init__(self):
            self.completions = MockCompletions()
    
    class MockCompletions:
        def create(self, **kwargs):
            return MockResponse()
    
    class MockResponse:
        def __init__(self):
            self.choices = [MockChoice()]
            self.usage = MockUsage()
    
    class MockChoice:
        def __init__(self):
            self.message = MockMessage()
    
    class MockMessage:
        def __init__(self):
            self.content = json.dumps({
                "recommendations": ["mock_tool"],
                "reasoning": "Mock reasoning",
                "confidence_score": 0.8,
                "safety_notes": []
            })
    
    class MockUsage:
        def __init__(self):
            self.total_tokens = 100
            self.prompt_tokens = 80
            self.completion_tokens = 20

from ..models.openai_integration import (
    ToolRecommendationRequest, ToolRecommendationResponse,
    SafetyAssessmentRequest, SafetyAssessmentResponse,
    ProjectAnalysisRequest, ProjectAnalysisResponse
)

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplates:
    """OpenAI prompt templates for different types of requests"""
    
    def __init__(self):
        self.templates = {
            "tool_recommendation": """
You are an expert DIY and tool recommendation assistant. Based on the following requirements, provide tool recommendations.

Task: {task}
User Skill Level: {user_skill_level}
Budget: ${budget}
Workspace: {workspace}
Project Type: {project_type}
Preferred Brands: {preferred_brands}
Existing Tools: {existing_tools}

Provide recommendations in JSON format with the following structure:
{{
    "recommendations": ["tool1", "tool2", "tool3"],
    "reasoning": "Detailed explanation of why these tools are recommended",
    "confidence_score": 0.85,
    "safety_notes": ["safety note 1", "safety note 2"],
    "estimated_cost": 250.00,
    "alternative_options": ["alternative1", "alternative2"]
}}

Consider safety, efficiency, budget constraints, and user skill level in your recommendations.
""",
            
            "safety_assessment": """
You are a safety expert specializing in tool safety and OSHA compliance. Assess the safety requirements for the following scenario.

Tools: {tools}
Task: {task}
User Experience: {user_experience}
Workspace Conditions: {workspace_conditions}
Materials: {materials}

Provide safety assessment in JSON format:
{{
    "safety_score": 8,
    "required_ppe": ["safety_glasses", "hearing_protection"],
    "osha_compliance": ["1926.95", "1926.52"],
    "risk_factors": ["flying_debris", "noise_exposure"],
    "mitigation_strategies": ["Use dust collection", "Maintain proper ventilation"],
    "training_required": false
}}

Focus on OSHA and ANSI compliance, specific safety requirements, and risk mitigation.
""",
            
            "project_analysis": """
You are a project management expert for DIY and construction projects. Analyze the following project for complexity and requirements.

Project Description: {project_description}
Materials: {materials}
Timeline: {timeline}
Budget: ${budget}
User Skill Level: {user_skill_level}

Provide analysis in JSON format:
{{
    "complexity_score": 6,
    "estimated_time_hours": 24,
    "skill_level_required": "intermediate",
    "critical_steps": ["step1", "step2", "step3"],
    "potential_challenges": ["challenge1", "challenge2"],
    "recommended_sequence": ["phase1", "phase2", "phase3"],
    "cost_estimate": 1200.00
}}

Consider realistic time estimates, skill requirements, potential challenges, and optimal sequencing.
""",
            
            "requirement_analysis": """
You are an expert at understanding and analyzing DIY project requirements from natural language descriptions.

User Query: {user_query}
Space Dimensions: {space_dimensions}
Load Requirements: {load_requirements}
Skill Level: {skill_level}

Extract and analyze the requirements in JSON format:
{{
    "intent": "requirement_analysis",
    "extracted_requirements": {{
        "primary_task": "build shelves",
        "space_constraints": "6ft x 3ft x 8ft",
        "load_capacity": "books and storage boxes",
        "material_preferences": []
    }},
    "clarifying_questions": ["What material preference?", "Any weight limits?"],
    "confidence": 0.9
}}

Focus on extracting specific, actionable requirements from the user's description.
""",
            
            "compatibility_check": """
You are a tool compatibility expert. Assess how well the given tools work together for the specified task.

Primary Tool: {primary_tool}
Additional Tools: {additional_tools}
Task: {task}
Materials: {materials}

Provide compatibility assessment in JSON format:
{{
    "compatibility_score": 0.9,
    "compatible_combinations": [["tool1", "tool2"], ["tool1", "tool3"]],
    "incompatible_combinations": [["tool2", "tool3"]],
    "optimization_suggestions": ["Use tool1 with accessory X", "Consider tool4 instead of tool3"],
    "workflow_integration": "Detailed workflow explanation"
}}

Consider tool interoperability, workflow efficiency, and optimal usage patterns.
""",
            
            "skill_assessment": """
You are a skill assessment expert for DIY and construction tasks. Evaluate if the user's skills match the proposed task.

Proposed Task: {proposed_task}
User Experience: {user_experience}
Available Tools: {available_tools}
Project Timeline: {project_timeline}

Provide skill assessment in JSON format:
{{
    "skill_match_score": 0.75,
    "recommended_skill_level": "intermediate",
    "skill_gaps": ["advanced measuring", "precision cutting"],
    "learning_requirements": ["Watch tutorial on precision cuts", "Practice on scrap material"],
    "task_modifications": ["Use pre-cut materials", "Get professional help for complex cuts"],
    "success_probability": 0.8
}}

Be honest about skill requirements and provide constructive guidance for skill development.
"""
        }
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names"""
        return list(self.templates.keys())
    
    def generate_prompt(self, template_name: str, data: Dict[str, Any]) -> str:
        """Generate prompt from template and data"""
        if template_name not in self.templates:
            raise ValueError(f"Invalid template name: {template_name}")
        
        template = self.templates[template_name]
        
        try:
            # Check for required variables based on template
            if template_name == "tool_recommendation":
                required_vars = ["task", "user_skill_level", "budget", "workspace", "project_type"]
                for var in required_vars:
                    if var not in data:
                        raise ValueError(f"Missing required variable for {template_name}: {var}")
                
                # Provide defaults for optional variables
                data.setdefault("preferred_brands", data.get("preferred_brands", []))
                data.setdefault("existing_tools", data.get("existing_tools", []))
            
            elif template_name == "safety_assessment":
                required_vars = ["tools", "task", "user_experience", "workspace_conditions"]
                for var in required_vars:
                    if var not in data:
                        raise ValueError(f"Missing required variable for {template_name}: {var}")
                
                data.setdefault("materials", data.get("materials", []))
            
            # Format template with data
            formatted_prompt = template.format(**data)
            return formatted_prompt
            
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}")


class OpenAIIntegrationService:
    """Service for OpenAI GPT-4 integration"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", max_tokens: int = 1000, temperature: float = 0.7):
        """Initialize OpenAI client"""
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not available, using mock implementation")
        
        try:
            if OPENAI_AVAILABLE:
                self.client = openai.OpenAI(api_key=api_key)
            else:
                self.client = openai.OpenAI()
            
            self.templates = PromptTemplates()
            self.token_usage_stats = {
                "total_tokens": 0,
                "requests_made": 0,
                "average_tokens_per_request": 0
            }
            
            logger.info(f"Initialized OpenAI client with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            # Make a simple test request
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False
    
    def _make_completion_request(self, prompt: str) -> Dict[str, Any]:
        """Make completion request to OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Update token usage stats
            if hasattr(response, 'usage') and response.usage:
                self.token_usage_stats["total_tokens"] += response.usage.total_tokens
                self.token_usage_stats["requests_made"] += 1
                self.token_usage_stats["average_tokens_per_request"] = (
                    self.token_usage_stats["total_tokens"] / self.token_usage_stats["requests_made"]
                )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                parsed_response = json.loads(content)
                return parsed_response
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {content}")
                raise ValueError(f"Invalid JSON response from OpenAI: {e}")
                
        except Exception as e:
            logger.error(f"OpenAI API request failed: {e}")
            raise
    
    def get_tool_recommendations(self, request: ToolRecommendationRequest) -> ToolRecommendationResponse:
        """Get tool recommendations from OpenAI"""
        # Generate prompt
        prompt = self.templates.generate_prompt("tool_recommendation", request.to_dict())
        
        # Make API request
        response_data = self._make_completion_request(prompt)
        
        # Validate response structure
        required_fields = ["recommendations", "reasoning", "confidence_score", "safety_notes"]
        for field in required_fields:
            if field not in response_data:
                raise ValueError(f"OpenAI response missing required field: {field}")
        
        # Create response object
        return ToolRecommendationResponse(
            recommendations=response_data["recommendations"],
            reasoning=response_data["reasoning"],
            confidence_score=response_data["confidence_score"],
            safety_notes=response_data["safety_notes"],
            estimated_cost=response_data.get("estimated_cost"),
            alternative_options=response_data.get("alternative_options", [])
        )
    
    def assess_safety_requirements(self, request: SafetyAssessmentRequest) -> SafetyAssessmentResponse:
        """Get safety assessment from OpenAI"""
        # Generate prompt
        prompt = self.templates.generate_prompt("safety_assessment", request.to_dict())
        
        # Make API request
        response_data = self._make_completion_request(prompt)
        
        # Validate response structure
        required_fields = ["safety_score", "required_ppe", "osha_compliance", "risk_factors", "mitigation_strategies", "training_required"]
        for field in required_fields:
            if field not in response_data:
                raise ValueError(f"OpenAI response missing required field: {field}")
        
        # Create response object
        return SafetyAssessmentResponse(
            safety_score=response_data["safety_score"],
            required_ppe=response_data["required_ppe"],
            osha_compliance=response_data["osha_compliance"],
            risk_factors=response_data["risk_factors"],
            mitigation_strategies=response_data["mitigation_strategies"],
            training_required=response_data["training_required"]
        )
    
    def analyze_project_complexity(self, request: ProjectAnalysisRequest) -> ProjectAnalysisResponse:
        """Get project complexity analysis from OpenAI"""
        # Generate prompt
        prompt = self.templates.generate_prompt("project_analysis", request.to_dict())
        
        # Make API request
        response_data = self._make_completion_request(prompt)
        
        # Validate response structure
        required_fields = ["complexity_score", "estimated_time_hours", "skill_level_required", "critical_steps", "potential_challenges", "recommended_sequence", "cost_estimate"]
        for field in required_fields:
            if field not in response_data:
                raise ValueError(f"OpenAI response missing required field: {field}")
        
        # Create response object
        return ProjectAnalysisResponse(
            complexity_score=response_data["complexity_score"],
            estimated_time_hours=response_data["estimated_time_hours"],
            skill_level_required=response_data["skill_level_required"],
            critical_steps=response_data["critical_steps"],
            potential_challenges=response_data["potential_challenges"],
            recommended_sequence=response_data["recommended_sequence"],
            cost_estimate=response_data["cost_estimate"]
        )
    
    def process_natural_language_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query to extract requirements"""
        # Create a simple requirement analysis request
        data = {
            "user_query": query,
            "space_dimensions": "",
            "load_requirements": "",
            "skill_level": "unknown"
        }
        
        # Generate prompt
        prompt = self.templates.generate_prompt("requirement_analysis", data)
        
        # Make API request
        response_data = self._make_completion_request(prompt)
        
        return response_data
    
    def get_tool_recommendations_with_retry(self, request: ToolRecommendationRequest, max_retries: int = 3) -> ToolRecommendationResponse:
        """Get tool recommendations with retry logic for rate limiting"""
        retries = 0
        
        while retries < max_retries:
            try:
                return self.get_tool_recommendations(request)
            except Exception as e:
                if "rate limit" in str(e).lower() and retries < max_retries - 1:
                    retries += 1
                    wait_time = 2 ** retries  # Exponential backoff
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {retries}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    raise
        
        raise Exception(f"Failed after {max_retries} retries")
    
    def get_token_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics"""
        return self.token_usage_stats.copy()
    
    def optimize_prompt_length(self, prompt: str, max_length: int = 3000) -> str:
        """Optimize prompt length for token efficiency"""
        if len(prompt) <= max_length:
            return prompt
        
        # Simple truncation strategy - could be more sophisticated
        truncated = prompt[:max_length]
        
        # Try to end at a complete sentence
        last_period = truncated.rfind('.')
        if last_period > max_length * 0.8:  # If we can keep at least 80% of content
            truncated = truncated[:last_period + 1]
        
        logger.warning(f"Prompt truncated from {len(prompt)} to {len(truncated)} characters")
        return truncated