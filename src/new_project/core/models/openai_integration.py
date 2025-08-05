"""
OpenAI Integration Data Models
==============================

Data models for OpenAI GPT-4 integration including request/response models
for tool recommendations, safety assessments, and project analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class ToolRecommendationRequest:
    """Request model for tool recommendations from OpenAI"""
    task: str
    user_skill_level: str
    budget: float
    workspace: str
    project_type: str
    preferred_brands: Optional[List[str]] = field(default_factory=list)
    existing_tools: Optional[List[str]] = field(default_factory=list)
    safety_requirements: Optional[List[str]] = field(default_factory=list)
    timeline: Optional[str] = None
    
    def __post_init__(self):
        """Validate tool recommendation request data"""
        if not self.task or not self.task.strip():
            raise ValueError("Task cannot be empty")
            
        if self.user_skill_level not in ["beginner", "intermediate", "advanced"]:
            raise ValueError("User skill level must be beginner, intermediate, or advanced")
            
        if self.budget < 0:
            raise ValueError("Budget must be non-negative")
            
        if not self.workspace or not self.workspace.strip():
            raise ValueError("Workspace cannot be empty")
            
        if not self.project_type or not self.project_type.strip():
            raise ValueError("Project type cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls"""
        return {
            "task": self.task,
            "user_skill_level": self.user_skill_level,
            "budget": self.budget,
            "workspace": self.workspace,
            "project_type": self.project_type,
            "preferred_brands": self.preferred_brands,
            "existing_tools": self.existing_tools,
            "safety_requirements": self.safety_requirements,
            "timeline": self.timeline
        }


@dataclass
class ToolRecommendationResponse:
    """Response model for tool recommendations from OpenAI"""
    recommendations: List[str]
    reasoning: str
    confidence_score: float
    safety_notes: List[str]
    estimated_cost: Optional[float] = None
    alternative_options: Optional[List[str]] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate tool recommendation response data"""
        if not self.recommendations or len(self.recommendations) == 0:
            raise ValueError("Must have at least one recommendation")
            
        if not self.reasoning or not self.reasoning.strip():
            raise ValueError("Reasoning cannot be empty")
            
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
            
        if not isinstance(self.safety_notes, list):
            raise ValueError("Safety notes must be a list")
            
        if self.estimated_cost is not None and self.estimated_cost < 0:
            raise ValueError("Estimated cost must be non-negative")


@dataclass
class SafetyAssessmentRequest:
    """Request model for safety assessment from OpenAI"""
    tools: List[str]
    task: str
    user_experience: str
    workspace_conditions: str
    materials: Optional[List[str]] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate safety assessment request data"""
        if not self.tools or len(self.tools) == 0:
            raise ValueError("Must specify at least one tool")
            
        if not self.task or not self.task.strip():
            raise ValueError("Task cannot be empty")
            
        if self.user_experience not in ["beginner", "intermediate", "advanced"]:
            raise ValueError("User experience must be beginner, intermediate, or advanced")
            
        if not self.workspace_conditions or not self.workspace_conditions.strip():
            raise ValueError("Workspace conditions cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls"""
        return {
            "tools": self.tools,
            "task": self.task,
            "user_experience": self.user_experience,
            "workspace_conditions": self.workspace_conditions,
            "materials": self.materials
        }


@dataclass
class SafetyAssessmentResponse:
    """Response model for safety assessment from OpenAI"""
    safety_score: int  # 1-10 scale
    required_ppe: List[str]
    osha_compliance: List[str]
    risk_factors: List[str]
    mitigation_strategies: List[str]
    training_required: bool
    
    def __post_init__(self):
        """Validate safety assessment response data"""
        if not (1 <= self.safety_score <= 10):
            raise ValueError("Safety score must be between 1 and 10")
            
        if not isinstance(self.required_ppe, list):
            raise ValueError("Required PPE must be a list")
            
        if not isinstance(self.osha_compliance, list):
            raise ValueError("OSHA compliance must be a list")
            
        if not isinstance(self.risk_factors, list):
            raise ValueError("Risk factors must be a list")
            
        if not isinstance(self.mitigation_strategies, list):
            raise ValueError("Mitigation strategies must be a list")
            
        if not isinstance(self.training_required, bool):
            raise ValueError("Training required must be a boolean")


@dataclass
class ProjectAnalysisRequest:
    """Request model for project analysis from OpenAI"""
    project_description: str
    materials: List[str]
    timeline: str
    budget: float
    user_skill_level: str
    
    def __post_init__(self):
        """Validate project analysis request data"""
        if not self.project_description or not self.project_description.strip():
            raise ValueError("Project description cannot be empty")
            
        if not self.materials or len(self.materials) == 0:
            raise ValueError("Must specify at least one material")
            
        if not self.timeline or not self.timeline.strip():
            raise ValueError("Timeline cannot be empty")
            
        if self.budget < 0:
            raise ValueError("Budget must be non-negative")
            
        if self.user_skill_level not in ["beginner", "intermediate", "advanced"]:
            raise ValueError("User skill level must be beginner, intermediate, or advanced")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls"""
        return {
            "project_description": self.project_description,
            "materials": self.materials,
            "timeline": self.timeline,
            "budget": self.budget,
            "user_skill_level": self.user_skill_level
        }


@dataclass
class ProjectAnalysisResponse:
    """Response model for project analysis from OpenAI"""
    complexity_score: int  # 1-10 scale
    estimated_time_hours: int
    skill_level_required: str
    critical_steps: List[str]
    potential_challenges: List[str]
    recommended_sequence: List[str]
    cost_estimate: float
    
    def __post_init__(self):
        """Validate project analysis response data"""
        if not (1 <= self.complexity_score <= 10):
            raise ValueError("Complexity score must be between 1 and 10")
            
        if self.estimated_time_hours <= 0:
            raise ValueError("Estimated time must be positive")
            
        if self.skill_level_required not in ["beginner", "intermediate", "advanced"]:
            raise ValueError("Skill level required must be beginner, intermediate, or advanced")
            
        if not isinstance(self.critical_steps, list):
            raise ValueError("Critical steps must be a list")
            
        if not isinstance(self.potential_challenges, list):
            raise ValueError("Potential challenges must be a list")
            
        if not isinstance(self.recommended_sequence, list):
            raise ValueError("Recommended sequence must be a list")
            
        if self.cost_estimate < 0:
            raise ValueError("Cost estimate must be non-negative")