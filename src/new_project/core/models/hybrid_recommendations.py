"""
Hybrid Recommendation Data Models
=================================

Data models for the hybrid recommendation pipeline including request/response
models, component scoring, and confidence metrics.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import time


@dataclass
class HybridRecommendationRequest:
    """Request model for hybrid recommendations"""
    user_query: str
    user_skill_level: str
    budget: float
    workspace: str
    project_type: str
    safety_requirements: Optional[List[str]] = field(default_factory=list)
    preferred_brands: Optional[List[str]] = field(default_factory=list)
    existing_tools: Optional[List[str]] = field(default_factory=list)
    timeline: Optional[str] = None
    
    def __post_init__(self):
        """Validate hybrid recommendation request data"""
        if not self.user_query or not self.user_query.strip():
            raise ValueError("User query cannot be empty")
            
        if self.user_skill_level not in ["beginner", "intermediate", "advanced"]:
            raise ValueError("User skill level must be beginner, intermediate, or advanced")
            
        if self.budget < 0:
            raise ValueError("Budget must be non-negative")
            
        if not self.workspace or not self.workspace.strip():
            raise ValueError("Workspace cannot be empty")
            
        if not self.project_type or not self.project_type.strip():
            raise ValueError("Project type cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for processing"""
        return {
            "user_query": self.user_query,
            "user_skill_level": self.user_skill_level,
            "budget": self.budget,
            "workspace": self.workspace,
            "project_type": self.project_type,
            "safety_requirements": self.safety_requirements,
            "preferred_brands": self.preferred_brands,
            "existing_tools": self.existing_tools,
            "timeline": self.timeline
        }


@dataclass
class ComponentScore:
    """Score from a specific recommendation component"""
    component: str
    score: float
    weight: float
    
    def __post_init__(self):
        """Validate component score data"""
        if not self.component or not self.component.strip():
            raise ValueError("Component name cannot be empty")
            
        if not (0.0 <= self.score <= 1.0):
            raise ValueError("Score must be between 0.0 and 1.0")
            
        if not (0.0 <= self.weight <= 1.0):
            raise ValueError("Weight must be between 0.0 and 1.0")
    
    def weighted_score(self) -> float:
        """Calculate weighted score"""
        return self.score * self.weight


@dataclass
class RecommendationResult:
    """Individual recommendation result"""
    name: str
    confidence_score: float
    sources: List[str]
    price: Optional[float] = None
    safety_rating: Optional[float] = None
    reasoning: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate recommendation result data"""
        if not self.name or not self.name.strip():
            raise ValueError("Recommendation name cannot be empty")
            
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
            
        if not self.sources or len(self.sources) == 0:
            raise ValueError("Must have at least one source")
            
        if self.price is not None and self.price < 0:
            raise ValueError("Price must be non-negative")
            
        if self.safety_rating is not None and not (0.0 <= self.safety_rating <= 5.0):
            raise ValueError("Safety rating must be between 0.0 and 5.0")


@dataclass
class ConfidenceMetrics:
    """Confidence metrics for recommendation quality assessment"""
    knowledge_graph_confidence: float
    vector_database_confidence: float
    openai_confidence: float
    weighted_confidence: float
    consensus_score: float
    uncertainty_score: float
    
    def __post_init__(self):
        """Validate confidence metrics data"""
        confidence_scores = [
            self.knowledge_graph_confidence,
            self.vector_database_confidence,
            self.openai_confidence,
            self.weighted_confidence,
            self.consensus_score,
            self.uncertainty_score
        ]
        
        for score in confidence_scores:
            if not (0.0 <= score <= 1.0):
                raise ValueError("All confidence scores must be between 0.0 and 1.0")


@dataclass
class HybridRecommendationResponse:
    """Response model for hybrid recommendations"""
    recommendations: List[RecommendationResult]
    total_confidence: float
    component_scores: List[ComponentScore]
    processing_time_ms: int
    from_cache: bool = False
    warnings: Optional[List[str]] = field(default_factory=list)
    confidence_metrics: Optional[ConfidenceMetrics] = None
    
    def __post_init__(self):
        """Validate hybrid recommendation response data"""
        if not self.recommendations or len(self.recommendations) == 0:
            raise ValueError("Must have at least one recommendation")
            
        if not (0.0 <= self.total_confidence <= 1.0):
            raise ValueError("Total confidence must be between 0.0 and 1.0")
            
        if not self.component_scores or len(self.component_scores) == 0:
            raise ValueError("Must have at least one component score")
            
        if self.processing_time_ms < 0:
            raise ValueError("Processing time must be non-negative")
            
        # Validate that component weights sum to approximately 1.0
        total_weight = sum(score.weight for score in self.component_scores)
        if not (0.95 <= total_weight <= 1.05):  # Allow small floating point errors
            raise ValueError(f"Component weights must sum to 1.0, got {total_weight}")
    
    @classmethod
    def create_with_timestamp(cls, recommendations: List[RecommendationResult], 
                            total_confidence: float, component_scores: List[ComponentScore],
                            start_time: float, **kwargs) -> "HybridRecommendationResponse":
        """Create response with calculated processing time"""
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return cls(
            recommendations=recommendations,
            total_confidence=total_confidence,
            component_scores=component_scores,
            processing_time_ms=processing_time_ms,
            **kwargs
        )
    
    def get_recommendations_by_confidence(self, min_confidence: float = 0.0) -> List[RecommendationResult]:
        """Get recommendations filtered by minimum confidence score"""
        return [rec for rec in self.recommendations if rec.confidence_score >= min_confidence]
    
    def get_recommendations_by_source(self, source: str) -> List[RecommendationResult]:
        """Get recommendations that include a specific source"""
        return [rec for rec in self.recommendations if source in rec.sources]
    
    def get_component_score(self, component: str) -> Optional[ComponentScore]:
        """Get score for a specific component"""
        for score in self.component_scores:
            if score.component == component:
                return score
        return None
    
    def calculate_weighted_confidence(self) -> float:
        """Calculate overall weighted confidence from component scores"""
        if not self.component_scores:
            return 0.0
        
        total_weighted_score = sum(score.weighted_score() for score in self.component_scores)
        return min(1.0, total_weighted_score)  # Cap at 1.0
    
    def get_performance_category(self) -> str:
        """Get performance category based on processing time"""
        if self.processing_time_ms < 500:
            return "excellent"
        elif self.processing_time_ms < 1000:
            return "good"
        elif self.processing_time_ms < 2000:
            return "acceptable"
        else:
            return "slow"
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to summary dictionary for logging/analysis"""
        return {
            "recommendation_count": len(self.recommendations),
            "total_confidence": self.total_confidence,
            "processing_time_ms": self.processing_time_ms,
            "performance_category": self.get_performance_category(),
            "from_cache": self.from_cache,
            "component_count": len(self.component_scores),
            "warning_count": len(self.warnings) if self.warnings else 0,
            "top_recommendation": self.recommendations[0].name if self.recommendations else None,
            "top_confidence": self.recommendations[0].confidence_score if self.recommendations else 0.0
        }