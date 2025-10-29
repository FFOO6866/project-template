"""
AI Context Enhancement Models
Rich contextual intelligence for sophisticated AI processing
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from dataflow import DataFlow

# Use the same DataFlow instance from production models
from .production_models import db

# Phase 3: AI Context Enhancement

@db.model
class ProductIntelligence:
    """Comprehensive product intelligence for AI-driven recommendations"""
    product_id: int  # FK to Product
    
    # Use Case & Application Context
    use_case_scenarios: List[Dict[str, Any]] = []  # Detailed application scenarios with contexts
    primary_applications: List[str] = []  # Construction, Manufacturing, Office, Home
    secondary_applications: List[str] = []  # Alternative uses
    industry_applications: List[str] = []  # Specific industries that use this product
    user_skill_requirements: str = "intermediate"  # beginner, intermediate, advanced, expert
    
    # Technical Intelligence
    technical_specifications: Dict[str, Any] = {}  # Detailed technical specs with AI context
    performance_benchmarks: Dict[str, Any] = {}  # Speed, efficiency, durability metrics
    technical_complexity: str = "moderate"  # simple, moderate, complex, highly_complex
    integration_requirements: List[str] = []  # What's needed to integrate/install
    dependency_products: List[int] = []  # Other product IDs this depends on
    
    # Installation & Setup
    installation_complexity: str = "moderate"  # simple, moderate, complex, expert
    installation_time_hours: Optional[Decimal] = None  # Estimated installation time
    tools_required: List[str] = []  # Tools needed for installation
    space_requirements: Optional[Dict[str, Any]] = None  # Physical space needed
    utility_requirements: List[str] = []  # Power, water, air, network requirements
    safety_precautions: List[str] = []  # Safety measures during installation
    
    # Operation & Maintenance
    maintenance_requirements: Dict[str, Any] = {}  # Schedule, costs, procedures
    maintenance_complexity: str = "standard"  # minimal, standard, intensive, specialized
    maintenance_frequency: str = "monthly"  # daily, weekly, monthly, quarterly, annually
    consumable_parts: List[Dict[str, Any]] = []  # Parts that need regular replacement
    service_life_years: Optional[int] = None  # Expected product lifespan
    
    # Safety & Compliance
    safety_ratings: List[Dict[str, Any]] = []  # OSHA, ANSI, CE compliance with details
    risk_factors: List[str] = []  # Potential hazards or risks
    protective_equipment_required: List[str] = []  # PPE needed
    safety_training_required: bool = False
    regulatory_compliance: List[str] = []  # Specific regulations this meets
    
    # Environmental & Sustainability
    environmental_impact: Dict[str, Any] = {}  # Carbon footprint, recycling info
    energy_efficiency_rating: Optional[str] = None  # Energy Star, etc.
    recyclability_score: Optional[Decimal] = None  # 1-10 scale
    hazardous_materials: List[str] = []  # Any dangerous substances
    disposal_requirements: Optional[str] = None  # Special disposal needed
    
    # Performance & Quality
    performance_metrics: Dict[str, Any] = {}  # Objective performance measures
    quality_indicators: Dict[str, Any] = {}  # Quality metrics and standards
    durability_rating: Optional[Decimal] = None  # 1-10 scale
    weather_resistance: Optional[str] = None  # Indoor, Outdoor, All-weather
    temperature_range: Optional[Dict[str, int]] = None  # Operating temperature range
    
    # Competitive Analysis
    competitive_alternatives: List[int] = []  # Alternative product IDs
    competitive_advantages: List[str] = []  # Why this product is better
    competitive_disadvantages: List[str] = []  # Weaknesses vs competitors
    unique_selling_points: List[str] = []  # What makes this product special
    market_differentiation: Optional[str] = None  # How it stands out
    
    # User Experience
    ease_of_use_rating: Optional[Decimal] = None  # 1-10 scale
    learning_curve: str = "moderate"  # easy, moderate, steep, very_steep
    user_interface_quality: Optional[Decimal] = None  # 1-10 scale (if applicable)
    documentation_quality: Optional[Decimal] = None  # 1-10 scale
    training_materials_available: bool = False
    
    # Training & Support Requirements
    training_requirements: Optional[str] = None  # User training needed
    training_duration_hours: Optional[int] = None
    certification_required: bool = False
    ongoing_support_needs: str = "standard"  # minimal, standard, intensive
    support_documentation: List[str] = []  # Manuals, guides, videos available
    
    # Customer Intelligence
    customer_feedback_summary: Dict[str, Any] = {}  # Aggregated reviews and ratings
    common_complaints: List[str] = []  # Frequent customer issues
    feature_requests: List[str] = []  # What customers want improved
    customer_satisfaction_score: Optional[Decimal] = None  # 1-10 scale
    repurchase_rate: Optional[Decimal] = None  # 0-100 percentage
    
    # Market Context
    market_maturity: str = "mature"  # emerging, growing, mature, declining
    adoption_rate: Optional[str] = None  # How quickly market adopts this type
    seasonality_patterns: List[Dict[str, Any]] = []  # Seasonal demand patterns
    economic_sensitivity: str = "moderate"  # low, moderate, high sensitivity to economy
    
    # Future & Evolution
    technology_evolution_risk: str = "low"  # low, moderate, high risk of obsolescence
    upgrade_path_available: bool = False
    next_generation_timeline: Optional[str] = None  # When next version expected
    legacy_compatibility: bool = True
    future_support_commitment: Optional[str] = None  # Vendor's support timeline
    
    # AI-Specific Context
    ai_tags: List[str] = []  # Tags for AI processing
    ai_recommendation_contexts: List[Dict[str, Any]] = []  # Contexts for recommendations
    decision_factors: Dict[str, Any] = {}  # Key factors for AI decision making
    compatibility_scores: Dict[int, Decimal] = {}  # Compatibility with other products (product_id: score)
    
    # Data Quality & Sources
    intelligence_completeness: Optional[Decimal] = None  # 0-100 percentage
    data_sources: List[str] = []  # Where this intelligence comes from
    last_intelligence_update: Optional[datetime] = None
    verification_status: str = "unverified"  # verified, unverified, needs_review
    
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True,
        'versioned': True  # Track intelligence evolution
    }
    
    __indexes__ = [
        {'name': 'idx_product_intel_product', 'fields': ['product_id'], 'unique': True},
        {'name': 'idx_product_intel_applications', 'fields': ['primary_applications'], 'type': 'gin'},
        {'name': 'idx_product_intel_complexity', 'fields': ['installation_complexity', 'technical_complexity']},
        {'name': 'idx_product_intel_safety', 'fields': ['safety_ratings'], 'type': 'gin'},
        {'name': 'idx_product_intel_competitive', 'fields': ['competitive_alternatives'], 'type': 'gin'},
        {'name': 'idx_product_intel_ai_tags', 'fields': ['ai_tags'], 'type': 'gin'},
        {'name': 'idx_product_intel_quality', 'fields': ['intelligence_completeness', 'verification_status']}
    ]

@db.model
class ProductCompatibilityMatrix:
    """Product-to-product compatibility and synergy intelligence"""
    product_a_id: int  # First product ID
    product_b_id: int  # Second product ID
    
    # Compatibility Assessment
    compatibility_type: str  # required, recommended, compatible, incompatible, unknown
    compatibility_score: Decimal  # 0-10 scale (10 = perfect synergy)
    compatibility_notes: Optional[str] = None
    
    # Relationship Context
    relationship_type: str = "standalone"  # required, complementary, substitute, accessory, competitive
    usage_context: List[str] = []  # When these products work together
    performance_impact: Optional[str] = None  # improves, neutral, degrades
    
    # Technical Compatibility
    technical_compatibility: bool = True
    interface_requirements: List[str] = []  # Adapters, connectors needed
    integration_complexity: str = "simple"  # simple, moderate, complex
    
    # Use Case Synergies
    synergy_scenarios: List[Dict[str, Any]] = []  # Specific scenarios where they work well together
    combined_benefits: List[str] = []  # Benefits when used together
    potential_issues: List[str] = []  # Problems when used together
    
    # Market Intelligence
    frequently_bought_together: bool = False
    market_bundle_frequency: Optional[Decimal] = None  # 0-100 percentage
    price_synergy: Optional[str] = None  # discount_available, premium_pricing, neutral
    
    # AI Recommendation Context
    recommendation_strength: Decimal = Decimal('0.0')  # 0-10 scale for AI recommendations
    context_triggers: List[str] = []  # Conditions that trigger this relationship
    confidence_level: Optional[Decimal] = None  # AI confidence in this relationship
    
    # Data Sources
    evidence_sources: List[str] = []  # customer_data, technical_specs, market_research
    last_validated: Optional[datetime] = None
    validation_method: Optional[str] = None
    
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True
    }
    
    __indexes__ = [
        {'name': 'idx_compatibility_products', 'fields': ['product_a_id', 'product_b_id'], 'unique': True},
        {'name': 'idx_compatibility_type', 'fields': ['compatibility_type', 'compatibility_score']},
        {'name': 'idx_compatibility_relationship', 'fields': ['relationship_type']},
        {'name': 'idx_compatibility_recommendation', 'fields': ['recommendation_strength', 'confidence_level']},
        {'name': 'idx_compatibility_synergy', 'fields': ['synergy_scenarios'], 'type': 'gin'}
    ]

@db.model
class UseCaseIntelligence:
    """Detailed use case scenarios and application intelligence"""
    use_case_id: str  # Unique identifier for the use case
    use_case_name: str
    use_case_category: str  # Construction, Manufacturing, Office, Home, etc.
    
    # Use Case Details
    description: str
    detailed_scenario: str  # Full description of the scenario
    industry_context: List[str] = []  # Industries where this applies
    user_types: List[str] = []  # Professional, Consumer, Technician, Manager
    
    # Requirements & Constraints
    skill_level_required: str = "intermediate"  # beginner, intermediate, advanced, expert
    time_constraints: Optional[Dict[str, Any]] = None  # Typical timeframes
    budget_constraints: Optional[Dict[str, Any]] = None  # Budget considerations
    space_constraints: Optional[Dict[str, Any]] = None  # Physical space needs
    resource_requirements: List[str] = []  # People, tools, materials needed
    
    # Success Criteria
    success_metrics: List[Dict[str, Any]] = []  # How to measure success
    quality_requirements: List[str] = []  # Quality standards needed
    performance_expectations: Dict[str, Any] = {}  # Expected performance levels
    
    # Associated Products
    required_products: List[int] = []  # Must-have products for this use case
    recommended_products: List[int] = []  # Nice-to-have products
    alternative_products: List[List[int]] = []  # Alternative product combinations
    
    # Risk & Safety
    risk_factors: List[str] = []  # Potential risks in this use case
    safety_requirements: List[str] = []  # Safety measures needed
    compliance_requirements: List[str] = []  # Regulatory compliance needed
    
    # Market Intelligence
    market_frequency: str = "common"  # rare, occasional, common, very_common
    market_trend: str = "stable"  # growing, stable, declining
    seasonal_patterns: List[Dict[str, Any]] = []  # Seasonal variations
    geographic_relevance: List[str] = []  # Where this use case applies
    
    # AI Context
    ai_complexity_score: Decimal  # 1-10 scale for AI processing complexity
    decision_tree_factors: List[Dict[str, Any]] = []  # Factors for AI decision making
    recommendation_triggers: List[str] = []  # What triggers this use case recommendation
    
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True,
        'versioned': True
    }
    
    __indexes__ = [
        {'name': 'idx_usecase_id', 'fields': ['use_case_id'], 'unique': True},
        {'name': 'idx_usecase_category', 'fields': ['use_case_category', 'market_frequency']},
        {'name': 'idx_usecase_industry', 'fields': ['industry_context'], 'type': 'gin'},
        {'name': 'idx_usecase_products', 'fields': ['required_products'], 'type': 'gin'},
        {'name': 'idx_usecase_skill', 'fields': ['skill_level_required', 'ai_complexity_score']},
        {'name': 'idx_usecase_triggers', 'fields': ['recommendation_triggers'], 'type': 'gin'}
    ]

# Export all models for use in other modules
__all__ = [
    'ProductIntelligence', 
    'ProductCompatibilityMatrix', 
    'UseCaseIntelligence'
]