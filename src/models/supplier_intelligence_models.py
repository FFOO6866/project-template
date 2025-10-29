"""
Supplier Intelligence Enhancement Models
Comprehensive AI-ready supplier/brand intelligence for PostgreSQL
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from dataflow import DataFlow

# Use the same DataFlow instance from production models
from .production_models import db

# Phase 1: Core Supplier Intelligence Enhancement

@db.model
class SupplierProfile:
    """Enhanced supplier business intelligence for AI processing"""
    supplier_id: int  # FK to Supplier
    
    # Business Intelligence
    company_size: str = "unknown"  # SME, Enterprise, Multinational, Startup
    annual_revenue: Optional[Decimal] = None
    annual_revenue_currency: str = "USD"
    employee_count: Optional[int] = None
    years_in_business: Optional[int] = None
    business_registration_number: Optional[str] = None
    tax_identification: Optional[str] = None
    
    # Industry & Capabilities
    primary_industries: List[str] = []  # JSON array - Manufacturing, Construction, IT, etc.
    secondary_industries: List[str] = []  # JSON array
    core_capabilities: List[str] = []  # JSON array - Manufacturing, Distribution, Services, Design
    specialized_services: List[str] = []  # JSON array - Custom fabrication, Installation, Training
    
    # Geographic & Operational
    headquarters_location: Optional[str] = None
    geographic_coverage: List[str] = []  # JSON array - Singapore, SEA, Global, specific countries
    service_regions: List[Dict[str, Any]] = []  # JSON array with region details and service levels
    distribution_network: Dict[str, Any] = {}  # Warehouses, distributors, partners
    
    # Certifications & Compliance
    certifications: List[Dict[str, Any]] = []  # JSON array - ISO, safety certs with details
    compliance_standards: List[str] = []  # OSHA, CE, UL, etc.
    quality_management_system: Optional[str] = None  # ISO 9001, Six Sigma, etc.
    environmental_certifications: List[str] = []  # ISO 14001, Carbon Neutral, etc.
    
    # Financial & Risk Assessment
    financial_rating: Optional[str] = None  # A+, A, B, C, D scale
    credit_score: Optional[int] = None
    payment_terms_standard: str = "net_30"  # net_15, net_30, net_60, etc.
    insurance_coverage: Optional[Dict[str, Any]] = None
    risk_assessment_score: Optional[Decimal] = None  # 1-10 scale
    
    # Operational Capabilities
    manufacturing_capacity: Optional[Dict[str, Any]] = None
    lead_time_performance: Optional[Dict[str, Any]] = None  # Average, best, worst by product type
    quality_control_processes: List[str] = []
    sustainability_practices: List[str] = []
    innovation_capabilities: List[str] = []
    
    # Market Position
    market_reputation: Optional[str] = None  # Excellent, Good, Fair, Poor
    customer_satisfaction_score: Optional[Decimal] = None  # 1-10 scale
    complaint_resolution_time: Optional[int] = None  # Hours
    return_policy_days: Optional[int] = None
    warranty_terms_standard: Optional[str] = None
    
    # Delivery & Logistics
    delivery_zones: List[Dict[str, Any]] = []  # Areas with lead times and costs
    shipping_methods: List[str] = []  # Standard, Express, White Glove, etc.
    minimum_order_values: Dict[str, Decimal] = {}  # By product category
    volume_discount_tiers: List[Dict[str, Any]] = []  # Pricing structures
    inventory_management_system: Optional[str] = None
    
    # Digital & Technology
    api_integration_available: bool = False
    api_documentation_url: Optional[str] = None
    edi_capabilities: bool = False
    digital_catalog_available: bool = False
    ecommerce_platform: Optional[str] = None
    
    # Contact & Support
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    technical_support_available: bool = True
    support_hours: Optional[str] = None
    account_manager_assigned: Optional[str] = None
    
    # Data Management
    data_source: str = "manual"  # manual, api, scraping, third_party
    data_quality_score: Optional[Decimal] = None  # 1-10 scale
    last_verified: Optional[datetime] = None
    verification_method: Optional[str] = None
    profile_completeness: Optional[Decimal] = None  # 0-100 percentage
    
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'multi_tenant': False,
        'audit_log': True,
        'versioned': True  # Track changes for relationship scoring
    }
    
    __indexes__ = [
        {'name': 'idx_supplier_profile_supplier', 'fields': ['supplier_id'], 'unique': True},
        {'name': 'idx_supplier_profile_size', 'fields': ['company_size']},
        {'name': 'idx_supplier_profile_industries', 'fields': ['primary_industries'], 'type': 'gin'},
        {'name': 'idx_supplier_profile_capabilities', 'fields': ['core_capabilities'], 'type': 'gin'},
        {'name': 'idx_supplier_profile_regions', 'fields': ['geographic_coverage'], 'type': 'gin'},
        {'name': 'idx_supplier_profile_certifications', 'fields': ['certifications'], 'type': 'gin'},
        {'name': 'idx_supplier_profile_financial', 'fields': ['financial_rating', 'risk_assessment_score']},
        {'name': 'idx_supplier_profile_quality', 'fields': ['data_quality_score', 'profile_completeness']}
    ]

@db.model
class SupplierPerformanceMetrics:
    """Real-time supplier performance tracking for AI decision making"""
    supplier_id: int  # FK to Supplier
    
    # Performance Metrics (rolling averages)
    on_time_delivery_rate: Optional[Decimal] = None  # 0-100 percentage
    order_accuracy_rate: Optional[Decimal] = None  # 0-100 percentage
    quality_score: Optional[Decimal] = None  # 1-10 scale
    response_time_hours: Optional[Decimal] = None  # Average response time
    
    # Volume & Relationship Metrics
    total_orders_count: int = 0
    total_order_value: Decimal = Decimal('0.00')
    total_order_currency: str = "USD"
    average_order_value: Optional[Decimal] = None
    relationship_duration_days: Optional[int] = None
    
    # Issue Tracking
    complaint_count: int = 0
    complaint_resolution_rate: Optional[Decimal] = None  # 0-100 percentage
    return_rate: Optional[Decimal] = None  # 0-100 percentage
    defect_rate: Optional[Decimal] = None  # 0-100 percentage
    
    # Pricing & Competitiveness
    price_competitiveness_score: Optional[Decimal] = None  # 1-10 scale
    price_stability_score: Optional[Decimal] = None  # 1-10 scale (less fluctuation = higher)
    discount_frequency: Optional[Decimal] = None  # 0-100 percentage of orders with discounts
    
    # Innovation & Collaboration
    new_product_introductions: int = 0
    collaborative_projects_count: int = 0
    technical_support_quality: Optional[Decimal] = None  # 1-10 scale
    
    # Market & Trends
    market_share_estimate: Optional[Decimal] = None  # 0-100 percentage in relevant categories
    growth_trend: Optional[str] = None  # growing, stable, declining
    capacity_utilization: Optional[Decimal] = None  # 0-100 percentage
    
    # Time-based Performance
    measurement_period_start: datetime
    measurement_period_end: datetime
    data_points_count: int = 0  # Number of orders/interactions in this period
    
    # Predictive Scores (AI-generated)
    reliability_prediction_score: Optional[Decimal] = None  # 1-10 scale
    future_availability_score: Optional[Decimal] = None  # 1-10 scale
    partnership_potential_score: Optional[Decimal] = None  # 1-10 scale
    
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True
    }
    
    __indexes__ = [
        {'name': 'idx_supplier_metrics_supplier', 'fields': ['supplier_id']},
        {'name': 'idx_supplier_metrics_period', 'fields': ['measurement_period_start', 'measurement_period_end']},
        {'name': 'idx_supplier_metrics_quality', 'fields': ['quality_score', 'on_time_delivery_rate']},
        {'name': 'idx_supplier_metrics_predictive', 'fields': ['reliability_prediction_score', 'partnership_potential_score']}
    ]

# Phase 2: Advanced Brand Intelligence

@db.model
class BrandIntelligence:
    """Comprehensive brand intelligence for AI-driven product recommendations"""
    brand_id: int  # FK to Brand
    
    # Market Position & Strategy
    market_position: str = "unknown"  # Premium, Mid-range, Budget, Luxury, Economy
    brand_category: str = "unknown"  # Manufacturer, Distributor, Private Label, OEM
    target_market: str = "general"  # Professional, Consumer, Industrial, Commercial
    market_focus: List[str] = []  # B2B, B2C, B2G (Business to Government)
    
    # Quality & Performance
    quality_rating: Optional[Decimal] = None  # 1-10 scale
    reliability_score: Optional[Decimal] = None  # 1-10 scale
    innovation_score: Optional[Decimal] = None  # Technology leadership 1-10 scale
    performance_consistency: Optional[Decimal] = None  # Product quality consistency 1-10
    
    # Sustainability & Social Responsibility
    sustainability_rating: str = "unknown"  # A-F rating
    environmental_impact_score: Optional[Decimal] = None  # 1-10 scale (lower = better)
    carbon_footprint_data: Optional[Dict[str, Any]] = None
    social_responsibility_score: Optional[Decimal] = None  # 1-10 scale
    ethical_sourcing: bool = False
    
    # Customer Experience
    customer_satisfaction_score: Optional[Decimal] = None  # 1-10 scale
    brand_loyalty_score: Optional[Decimal] = None  # 1-10 scale
    customer_support_quality: Optional[Decimal] = None  # 1-10 scale
    user_experience_rating: Optional[Decimal] = None  # 1-10 scale
    
    # Warranty & Support
    standard_warranty_months: Optional[int] = None
    extended_warranty_available: bool = False
    warranty_terms: Dict[str, Any] = {}  # Detailed warranty by product type
    support_channels: List[str] = []  # Phone, Email, Chat, Online, On-site
    support_response_time: Optional[str] = None  # 24hr, 48hr, next business day
    
    # Technical & Compatibility
    technology_standards: List[str] = []  # Standards complied with
    compatibility_matrix: Dict[str, List[str]] = {}  # Compatible brands/products by category
    interoperability_score: Optional[Decimal] = None  # 1-10 scale
    upgrade_path_availability: bool = False
    
    # Market Segments & Applications
    target_segments: List[str] = []  # Industrial, Consumer, Professional, Educational
    primary_applications: List[str] = []  # Construction, Manufacturing, Office, Home
    use_case_specialization: List[str] = []  # Heavy Duty, Precision, Standard, Light Use
    
    # Regional & Geographic
    regional_presence: Dict[str, Dict[str, Any]] = {}  # Market share and presence by region
    manufacturing_locations: List[str] = []
    distribution_network: Dict[str, Any] = {}
    local_support_availability: Dict[str, bool] = {}  # Support availability by region
    
    # Competitive Intelligence
    main_competitors: List[str] = []  # Brand names
    competitive_advantages: List[str] = []
    competitive_disadvantages: List[str] = []
    market_share_primary: Optional[Decimal] = None  # In primary category
    market_trend: str = "stable"  # growing, stable, declining
    
    # Pricing Strategy
    pricing_strategy: str = "competitive"  # premium, competitive, value, penetration
    price_positioning: str = "mid-range"  # premium, mid-range, value, budget
    discount_frequency: str = "occasional"  # frequent, occasional, rare, never
    price_stability: str = "stable"  # stable, fluctuating, seasonal
    
    # Innovation & Development
    rd_investment_level: str = "moderate"  # high, moderate, low, minimal
    new_product_frequency: str = "regular"  # frequent, regular, occasional, rare
    technology_adoption_speed: str = "moderate"  # early, moderate, late, laggard
    patent_portfolio_strength: str = "unknown"  # strong, moderate, weak, minimal
    
    # Data Sources & Quality
    data_sources: List[str] = []  # market_research, customer_feedback, industry_reports
    information_accuracy: Optional[Decimal] = None  # 1-10 confidence score
    last_market_research_update: Optional[datetime] = None
    analyst_rating: Optional[str] = None  # Buy, Hold, Sell equivalent for partnerships
    
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True,
        'versioned': True
    }
    
    __indexes__ = [
        {'name': 'idx_brand_intel_brand', 'fields': ['brand_id'], 'unique': True},
        {'name': 'idx_brand_intel_position', 'fields': ['market_position', 'target_market']},
        {'name': 'idx_brand_intel_quality', 'fields': ['quality_rating', 'reliability_score']},
        {'name': 'idx_brand_intel_segments', 'fields': ['target_segments'], 'type': 'gin'},
        {'name': 'idx_brand_intel_applications', 'fields': ['primary_applications'], 'type': 'gin'},
        {'name': 'idx_brand_intel_competitive', 'fields': ['market_share_primary', 'market_trend']},
        {'name': 'idx_brand_intel_pricing', 'fields': ['pricing_strategy', 'price_positioning']}
    ]

@db.model
class BrandProductLineIntelligence:
    """Detailed intelligence about specific product lines within brands"""
    brand_id: int  # FK to Brand
    product_line_name: str
    product_line_category: str
    
    # Product Line Characteristics
    line_positioning: str = "mainstream"  # flagship, mainstream, budget, specialty
    target_use_case: str = "general"  # professional, consumer, industrial, specialized
    complexity_level: str = "moderate"  # simple, moderate, complex, expert
    
    # Performance Metrics
    reliability_track_record: Optional[Decimal] = None  # 1-10 scale
    customer_satisfaction_line: Optional[Decimal] = None  # 1-10 scale
    return_rate_line: Optional[Decimal] = None  # 0-100 percentage
    
    # Market Performance
    sales_volume_trend: str = "stable"  # growing, stable, declining
    market_acceptance: str = "good"  # excellent, good, fair, poor
    competitive_position: str = "competitive"  # leader, competitive, follower, niche
    
    # Technical Specifications
    technology_generation: Optional[str] = None  # Current, Previous, Legacy, Next-gen
    upgrade_cycle_months: Optional[int] = None
    backward_compatibility: bool = True
    forward_compatibility: bool = False
    
    # Support & Services
    specialized_training_required: bool = False
    installation_complexity: str = "moderate"  # simple, moderate, complex, expert
    maintenance_requirements: str = "standard"  # minimal, standard, intensive, specialized
    
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True
    }
    
    __indexes__ = [
        {'name': 'idx_brand_line_brand', 'fields': ['brand_id']},
        {'name': 'idx_brand_line_category', 'fields': ['product_line_category', 'line_positioning']},
        {'name': 'idx_brand_line_performance', 'fields': ['reliability_track_record', 'customer_satisfaction_line']}
    ]

# Export all models for use in other modules
__all__ = [
    'SupplierProfile', 
    'SupplierPerformanceMetrics', 
    'BrandIntelligence', 
    'BrandProductLineIntelligence'
]