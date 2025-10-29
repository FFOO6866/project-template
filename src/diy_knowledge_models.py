"""
Extended DIY Knowledge Models
============================

Additional DataFlow models specifically for DIY knowledge platform:
- DIY Projects with step-by-step guidance
- Tool compatibility matrix
- Community knowledge and tips
- Safety recommendations and warnings
- Project cost estimations
- Skill assessments and certifications

These models extend the core product models to provide rich DIY-specific functionality.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

# Import base DataFlow configuration
try:
    from src.new_project.core.models import db, Field
except ImportError:
    # Fallback for testing
    class Field:
        @staticmethod
        def primary_key(): return Field()
        @staticmethod
        def foreign_key(ref): return Field()
        @staticmethod
        def unique(): return Field()
        @staticmethod
        def index(): return Field()
        @staticmethod
        def default_factory(func): return Field()
        @staticmethod
        def null(): return Field()
        @staticmethod
        def max_length(length): return Field()
    
    class DataFlow:
        def model(self, cls): return cls
    
    db = DataFlow()

# ==============================================================================
# DIY PROJECT MODELS
# ==============================================================================

@db.model
class DIYProject:
    """Comprehensive DIY project definitions with step-by-step guidance."""
    
    # Primary identification
    id: int = Field.primary_key()
    project_code: str = Field(unique=True, max_length=50, index=True)
    name: str = Field(max_length=255, index=True)
    slug: str = Field(unique=True, max_length=255, index=True)
    description: str = Field()
    long_description: str = Field()
    
    # Project classification
    category: str = Field(max_length=100, index=True)  # plumbing, electrical, carpentry, etc.
    subcategory: str = Field(max_length=100, index=True)
    project_type: str = Field(max_length=50, index=True)  # repair, installation, upgrade, maintenance
    
    # Difficulty and skill requirements
    difficulty_level: str = Field(max_length=20, index=True)  # beginner, intermediate, advanced, expert
    required_skills: List[str] = Field(default_factory=list)  # JSON array
    skill_level_required: str = Field(max_length=20, index=True)
    
    # Time and cost estimates
    estimated_time_hours: float = Field(index=True)
    time_range_min: float = Field()
    time_range_max: float = Field()
    estimated_cost_min: Decimal = Field(index=True)
    estimated_cost_max: Decimal = Field(index=True)
    
    # Location and context
    room_types: List[str] = Field(default_factory=list)  # JSON array
    indoor_outdoor: str = Field(max_length=10, index=True)  # indoor, outdoor, both
    seasonal_relevance: List[str] = Field(default_factory=list)  # JSON array
    
    # Safety and legal requirements
    safety_level: str = Field(max_length=20, index=True)  # low, medium, high, critical
    permits_required: bool = Field(default=False, index=True)
    professional_help_recommended: bool = Field(default=False, index=True)
    insurance_considerations: str = Field()
    
    # Tools and materials
    tools_required: List[str] = Field(default_factory=list)  # JSON array
    materials_needed: List[str] = Field(default_factory=list)  # JSON array
    optional_tools: List[str] = Field(default_factory=list)  # JSON array
    consumables: List[str] = Field(default_factory=list)  # JSON array
    
    # Project guidance
    step_by_step_guide: Dict[str, Any] = Field(default_factory=dict)  # JSONB
    tips_and_tricks: List[str] = Field(default_factory=list)  # JSON array
    common_mistakes: List[str] = Field(default_factory=list)  # JSON array
    troubleshooting_guide: Dict[str, Any] = Field(default_factory=dict)  # JSONB
    quality_checkpoints: List[str] = Field(default_factory=list)  # JSON array
    
    # Safety information
    safety_warnings: List[str] = Field(default_factory=list)  # JSON array
    ppe_requirements: List[str] = Field(default_factory=list)  # JSON array
    hazard_analysis: Dict[str, Any] = Field(default_factory=dict)  # JSONB
    
    # Project metadata
    popularity_score: int = Field(default=0, index=True)
    success_rate: Optional[float] = Field()  # 0.0-1.0
    difficulty_rating: Optional[float] = Field()  # Community-rated difficulty
    completion_rate: Optional[float] = Field()  # Percentage who complete
    
    # Content and media
    video_tutorials: List[str] = Field(default_factory=list)  # JSON array of URLs
    image_gallery: List[str] = Field(default_factory=list)  # JSON array of URLs
    reference_links: List[str] = Field(default_factory=list)  # JSON array of URLs
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now, index=True)
    published_at: Optional[datetime] = Field(index=True)
    last_reviewed_at: Optional[datetime] = Field(index=True)
    reviewed_by: Optional[str] = Field(max_length=100)
    
    __dataflow__ = {
        'audit_log': True,
        'versioned': True,
        'search_fields': ['name', 'description', 'long_description'],
        'jsonb_fields': ['step_by_step_guide', 'troubleshooting_guide', 'hazard_analysis'],
        'full_text_search': True
    }
    
    __indexes__ = [
        {'name': 'idx_diy_project_code', 'fields': ['project_code'], 'unique': True},
        {'name': 'idx_diy_project_category_difficulty', 'fields': ['category', 'difficulty_level']},
        {'name': 'idx_diy_project_time_cost', 'fields': ['estimated_time_hours', 'estimated_cost_min']},
        {'name': 'idx_diy_project_safety_permits', 'fields': ['safety_level', 'permits_required']},
        {'name': 'idx_diy_project_popularity', 'fields': ['popularity_score', 'success_rate']},
        {'name': 'idx_diy_project_published', 'fields': ['published_at'], 'condition': 'published_at IS NOT NULL'},
        {'name': 'idx_diy_project_skills_gin', 'fields': ['required_skills'], 'type': 'gin'},
        {'name': 'idx_diy_project_tools_gin', 'fields': ['tools_required'], 'type': 'gin'},
        {'name': 'idx_diy_project_search_text', 'fields': ['name', 'description'], 'type': 'gin', 'options': 'gin_trgm_ops'}
    ]


@db.model
class ProjectStep:
    """Individual steps within DIY projects with detailed instructions."""
    
    # Primary identification
    id: int = Field.primary_key()
    project_id: int = Field(foreign_key="DIYProject.id", index=True)
    
    # Step details
    step_number: int = Field(index=True)
    title: str = Field(max_length=255)
    description: str = Field()
    detailed_instructions: str = Field()
    
    # Time and difficulty for this step
    estimated_minutes: int = Field()
    difficulty_level: str = Field(max_length=20)
    
    # Tools and materials for this step
    tools_for_step: List[str] = Field(default_factory=list)  # JSON array
    materials_for_step: List[str] = Field(default_factory=list)  # JSON array
    
    # Safety for this step
    safety_precautions: List[str] = Field(default_factory=list)  # JSON array
    ppe_for_step: List[str] = Field(default_factory=list)  # JSON array
    
    # Quality control
    quality_checkpoints: List[str] = Field(default_factory=list)  # JSON array
    common_errors: List[str] = Field(default_factory=list)  # JSON array
    
    # Media and references
    images: List[str] = Field(default_factory=list)  # JSON array
    videos: List[str] = Field(default_factory=list)  # JSON array
    diagrams: List[str] = Field(default_factory=list)  # JSON array
    
    # Dependencies and flow
    depends_on_steps: List[int] = Field(default_factory=list)  # JSON array of step IDs
    optional_step: bool = Field(default=False)
    can_be_done_in_parallel: bool = Field(default=False)
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    __dataflow__ = {
        'audit_log': True,
        'search_fields': ['title', 'description', 'detailed_instructions'],
        'jsonb_fields': ['tools_for_step', 'materials_for_step', 'safety_precautions']
    }
    
    __indexes__ = [
        {'name': 'idx_project_step_project_number', 'fields': ['project_id', 'step_number'], 'unique': True},
        {'name': 'idx_project_step_difficulty', 'fields': ['difficulty_level', 'estimated_minutes']},
        {'name': 'idx_project_step_optional', 'fields': ['optional_step', 'can_be_done_in_parallel']}
    ]


# ==============================================================================
# TOOL COMPATIBILITY MODELS
# ==============================================================================

@db.model
class ToolCompatibility:
    """Tool and product compatibility matrix with safety considerations."""
    
    # Primary identification
    id: int = Field.primary_key()
    
    # Product relationships
    product1_id: int = Field(foreign_key="Product.id", index=True)
    product2_id: int = Field(foreign_key="Product.id", index=True)
    
    # Alternative: text-based for flexibility
    tool1_name: str = Field(max_length=255, index=True)
    tool2_name: str = Field(max_length=255, index=True)
    brand1: str = Field(max_length=100, index=True)
    brand2: str = Field(max_length=100, index=True)
    
    # Compatibility assessment
    compatibility_type: str = Field(max_length=50, index=True)  # compatible, incompatible, requires_adapter, conditional
    compatibility_level: str = Field(max_length=20, index=True)  # perfect, good, fair, poor, dangerous
    compatibility_score: float = Field(index=True)  # 0.0-1.0
    
    # Safety considerations
    safety_rating: str = Field(max_length=20, index=True)  # safe, caution, unsafe, dangerous
    safety_notes: str = Field()
    risk_factors: List[str] = Field(default_factory=list)  # JSON array
    
    # Compatibility details
    notes: str = Field()
    limitations: str = Field()
    special_requirements: str = Field()
    adapter_required: str = Field(max_length=255)
    
    # Verification and confidence
    verified_by_expert: bool = Field(default=False, index=True)
    verification_source: str = Field(max_length=255)
    confidence_score: float = Field()  # 0.0-1.0
    last_verified_date: Optional[datetime] = Field(index=True)
    
    # Usage context
    use_case_context: str = Field()  # When this compatibility applies
    environmental_factors: List[str] = Field(default_factory=list)  # JSON array
    
    # Community feedback
    user_reports_count: int = Field(default=0)
    positive_reports: int = Field(default=0)
    negative_reports: int = Field(default=0)
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(max_length=100)
    
    __dataflow__ = {
        'audit_log': True,
        'search_fields': ['tool1_name', 'tool2_name', 'notes'],
        'jsonb_fields': ['risk_factors', 'environmental_factors']
    }
    
    __indexes__ = [
        {'name': 'idx_tool_compat_products', 'fields': ['product1_id', 'product2_id']},
        {'name': 'idx_tool_compat_names', 'fields': ['tool1_name', 'tool2_name']},
        {'name': 'idx_tool_compat_brands', 'fields': ['brand1', 'brand2']},
        {'name': 'idx_tool_compat_type_level', 'fields': ['compatibility_type', 'compatibility_level']},
        {'name': 'idx_tool_compat_safety', 'fields': ['safety_rating', 'verified_by_expert']},
        {'name': 'idx_tool_compat_score', 'fields': ['compatibility_score', 'confidence_score']},
        {'name': 'idx_tool_compat_verified', 'fields': ['verified_by_expert', 'last_verified_date']}
    ]


# ==============================================================================
# COMMUNITY KNOWLEDGE MODELS
# ==============================================================================

@db.model
class CommunityTip:
    """Community-contributed tips, tricks, and advice."""
    
    # Primary identification
    id: int = Field.primary_key()
    
    # Tip content
    title: str = Field(max_length=255, index=True)
    description: str = Field()
    detailed_instructions: str = Field()
    tip_type: str = Field(max_length=50, index=True)  # technique, safety, cost_saving, troubleshooting
    
    # Context and applicability
    related_project_id: Optional[int] = Field(foreign_key="DIYProject.id", index=True)
    applicable_tools: List[str] = Field(default_factory=list)  # JSON array
    applicable_materials: List[str] = Field(default_factory=list)  # JSON array
    skill_level: str = Field(max_length=20, index=True)
    
    # Category and tags
    category: str = Field(max_length=100, index=True)
    tags: List[str] = Field(default_factory=list)  # JSON array
    
    # Community engagement
    upvotes: int = Field(default=0, index=True)
    downvotes: int = Field(default=0, index=True)
    view_count: int = Field(default=0)
    saved_count: int = Field(default=0)
    
    # Quality and moderation
    quality_score: float = Field()  # 0.0-1.0
    moderation_status: str = Field(default="pending", max_length=20, index=True)  # pending, approved, rejected
    flagged_count: int = Field(default=0)
    
    # Media attachments
    images: List[str] = Field(default_factory=list)  # JSON array
    videos: List[str] = Field(default_factory=list)  # JSON array
    
    # Attribution and source
    contributor_id: Optional[int] = Field(foreign_key="UserProfile.id", index=True)
    contributor_name: str = Field(max_length=100)
    source_type: str = Field(default="community", max_length=20)  # community, expert, manufacturer
    external_source: Optional[str] = Field(max_length=500)
    
    # Effectiveness tracking
    tried_count: int = Field(default=0)
    success_count: int = Field(default=0)
    failure_count: int = Field(default=0)
    success_rate: Optional[float] = Field()
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now)
    published_at: Optional[datetime] = Field(index=True)
    
    __dataflow__ = {
        'audit_log': True,
        'search_fields': ['title', 'description', 'detailed_instructions'],
        'jsonb_fields': ['applicable_tools', 'applicable_materials', 'tags'],
        'full_text_search': True
    }
    
    __indexes__ = [
        {'name': 'idx_community_tip_type_category', 'fields': ['tip_type', 'category']},
        {'name': 'idx_community_tip_engagement', 'fields': ['upvotes', 'quality_score']},
        {'name': 'idx_community_tip_moderation', 'fields': ['moderation_status', 'published_at']},
        {'name': 'idx_community_tip_contributor', 'fields': ['contributor_id', 'created_at']},
        {'name': 'idx_community_tip_success', 'fields': ['success_rate', 'tried_count']},
        {'name': 'idx_community_tip_tags_gin', 'fields': ['tags'], 'type': 'gin'}
    ]


@db.model
class ExpertAdvice:
    """Professional expert advice and best practices."""
    
    # Primary identification
    id: int = Field.primary_key()
    
    # Expert identification
    expert_id: int = Field(foreign_key="UserProfile.id", index=True)
    expert_name: str = Field(max_length=100, index=True)
    expert_credentials: str = Field(max_length=255)
    expert_specialization: str = Field(max_length=100, index=True)
    
    # Advice content
    title: str = Field(max_length=255, index=True)
    advice_text: str = Field()
    context: str = Field()  # When/where this advice applies
    
    # Classification
    advice_type: str = Field(max_length=50, index=True)  # best_practice, safety, technique, troubleshooting
    expertise_area: str = Field(max_length=100, index=True)
    complexity_level: str = Field(max_length=20, index=True)
    
    # Applicability
    related_projects: List[int] = Field(default_factory=list)  # JSON array of project IDs
    applicable_tools: List[str] = Field(default_factory=list)  # JSON array
    skill_level_required: str = Field(max_length=20, index=True)
    
    # Professional validation
    peer_reviewed: bool = Field(default=False, index=True)
    reviewed_by: Optional[str] = Field(max_length=100)
    review_date: Optional[datetime] = Field(index=True)
    certification_level: str = Field(max_length=50)
    
    # Industry standards compliance
    compliant_standards: List[str] = Field(default_factory=list)  # JSON array
    regulatory_notes: str = Field()
    
    # Usage and feedback
    view_count: int = Field(default=0)
    helpful_votes: int = Field(default=0)
    not_helpful_votes: int = Field(default=0)
    implementation_reports: int = Field(default=0)
    
    # Media and documentation
    supporting_documents: List[str] = Field(default_factory=list)  # JSON array
    reference_standards: List[str] = Field(default_factory=list)  # JSON array
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    published_at: Optional[datetime] = Field(index=True)
    expires_at: Optional[datetime] = Field(index=True)
    
    __dataflow__ = {
        'audit_log': True,
        'versioned': True,
        'search_fields': ['title', 'advice_text', 'context'],
        'jsonb_fields': ['related_projects', 'applicable_tools', 'compliant_standards']
    }
    
    __indexes__ = [
        {'name': 'idx_expert_advice_expert', 'fields': ['expert_id', 'expert_specialization']},
        {'name': 'idx_expert_advice_type_area', 'fields': ['advice_type', 'expertise_area']},
        {'name': 'idx_expert_advice_reviewed', 'fields': ['peer_reviewed', 'review_date']},
        {'name': 'idx_expert_advice_helpful', 'fields': ['helpful_votes', 'view_count']},
        {'name': 'idx_expert_advice_published', 'fields': ['published_at'], 'condition': 'published_at IS NOT NULL'},
        {'name': 'idx_expert_advice_expires', 'fields': ['expires_at'], 'condition': 'expires_at IS NOT NULL'}
    ]


# ==============================================================================
# COST ESTIMATION MODELS
# ==============================================================================

@db.model
class ProjectCostEstimate:
    """Detailed cost estimates for DIY projects with regional variations."""
    
    # Primary identification
    id: int = Field.primary_key()
    project_id: int = Field(foreign_key="DIYProject.id", index=True)
    
    # Geographic context
    region: str = Field(max_length=50, index=True)  # US_Northeast, US_Southeast, etc.
    city: Optional[str] = Field(max_length=100, index=True)
    postal_code: Optional[str] = Field(max_length=20, index=True)
    
    # Cost breakdown
    total_cost_min: Decimal = Field(index=True)
    total_cost_max: Decimal = Field(index=True)
    total_cost_average: Decimal = Field(index=True)
    
    # Component costs
    materials_cost_min: Decimal = Field()
    materials_cost_max: Decimal = Field()
    tools_cost_min: Decimal = Field()
    tools_cost_max: Decimal = Field()
    labor_cost_min: Optional[Decimal] = Field()  # If hiring help
    labor_cost_max: Optional[Decimal] = Field()
    permit_costs: Optional[Decimal] = Field()
    
    # Cost factors
    complexity_multiplier: float = Field(default=1.0)
    regional_cost_multiplier: float = Field(default=1.0)
    seasonal_multiplier: float = Field(default=1.0)
    
    # Detailed cost items as JSONB
    cost_breakdown: Dict[str, Any] = Field(default_factory=dict)  # JSONB
    
    # Cost-saving opportunities
    diy_savings_potential: Decimal = Field()
    bulk_purchase_savings: Decimal = Field()
    seasonal_savings: Decimal = Field()
    
    # Market data
    price_volatility: str = Field(max_length=20)  # stable, moderate, high
    market_trends: str = Field()
    last_market_update: datetime = Field(default_factory=datetime.now, index=True)
    
    # Quality levels and alternatives
    budget_option_cost: Optional[Decimal] = Field()
    standard_option_cost: Optional[Decimal] = Field()
    premium_option_cost: Optional[Decimal] = Field()
    
    # Data sources and confidence
    data_sources: List[str] = Field(default_factory=list)  # JSON array
    confidence_level: float = Field()  # 0.0-1.0
    sample_size: int = Field(default=0)
    
    # Temporal information
    estimate_date: datetime = Field(default_factory=datetime.now, index=True)
    valid_until: datetime = Field(index=True)
    
    __dataflow__ = {
        'audit_log': True,
        'search_fields': ['region', 'city'],
        'jsonb_fields': ['cost_breakdown', 'data_sources']
    }
    
    __indexes__ = [
        {'name': 'idx_cost_estimate_project_region', 'fields': ['project_id', 'region']},
        {'name': 'idx_cost_estimate_total_cost', 'fields': ['total_cost_average', 'estimate_date']},
        {'name': 'idx_cost_estimate_location', 'fields': ['region', 'city', 'postal_code']},
        {'name': 'idx_cost_estimate_valid', 'fields': ['valid_until'], 'condition': 'valid_until > CURRENT_TIMESTAMP'},
        {'name': 'idx_cost_estimate_confidence', 'fields': ['confidence_level', 'sample_size']}
    ]


# Export all DIY-specific models
__all__ = [
    'DIYProject', 'ProjectStep', 'ToolCompatibility', 
    'CommunityTip', 'ExpertAdvice', 'ProjectCostEstimate'
]

# Model validation for DIY models
def validate_diy_model_integrity():
    """Validate DIY model integrity and relationships."""
    diy_models = [
        DIYProject, ProjectStep, ToolCompatibility,
        CommunityTip, ExpertAdvice, ProjectCostEstimate
    ]
    
    for model in diy_models:
        # Verify DataFlow configuration
        assert hasattr(model, '__dataflow__'), f"{model.__name__} missing DataFlow configuration"
        
        # Verify primary key exists
        assert hasattr(model, 'id'), f"{model.__name__} missing primary key field"
        
        # Verify timestamps
        if hasattr(model, 'created_at'):
            assert hasattr(model, 'updated_at'), f"{model.__name__} has created_at but missing updated_at"
    
    return True

# Initialize validation
if __name__ != "__main__":
    try:
        validate_diy_model_integrity()
    except Exception as e:
        print(f"DIY model integrity validation failed: {e}")