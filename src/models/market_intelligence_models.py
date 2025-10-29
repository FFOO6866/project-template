"""
Market Intelligence Integration Models
Real-time market dynamics and intelligence for AI processing
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from dataflow import DataFlow

# Use the same DataFlow instance from production models
from .production_models import db

# Phase 4: Market Intelligence Integration

@db.model
class MarketIntelligence:
    """Real-time market intelligence for products and suppliers"""
    product_id: int  # FK to Product
    supplier_id: int  # FK to Supplier
    
    # Current Market Status
    current_pricing: Decimal
    pricing_currency: str = "USD"
    pricing_last_updated: datetime
    availability_status: str = "unknown"  # in_stock, limited, backorder, discontinued
    stock_level_indicator: str = "unknown"  # high, medium, low, critical, out
    
    # Pricing Intelligence
    pricing_history: List[Dict[str, Any]] = []  # Historical price points with dates
    price_trend: str = "stable"  # increasing, stable, decreasing, volatile
    price_volatility_score: Optional[Decimal] = None  # 0-10 scale (higher = more volatile)
    price_seasonality: List[Dict[str, Any]] = []  # Seasonal pricing patterns
    
    # Supply Chain Intelligence
    lead_time_days: int = 0
    lead_time_reliability: str = "unknown"  # reliable, variable, unreliable
    lead_time_history: List[Dict[str, Any]] = []  # Historical lead times
    supply_chain_risk: str = "low"  # low, moderate, high, critical
    alternative_suppliers_available: int = 0
    
    # Demand Intelligence
    demand_patterns: Dict[str, Any] = {}  # Seasonal trends, growth patterns
    demand_trend: str = "stable"  # growing, stable, declining, volatile
    demand_seasonality: List[Dict[str, Any]] = []  # Seasonal demand variations
    backorder_frequency: Optional[Decimal] = None  # 0-100 percentage
    
    # Market Performance
    market_share: Optional[Decimal] = None  # 0-100 percentage in relevant category
    market_position: str = "unknown"  # leader, competitive, follower, niche
    competitive_intensity: str = "moderate"  # low, moderate, high, intense
    
    # Customer Intelligence
    customer_satisfaction: Decimal = Decimal('0.0')  # 1-10 scale
    customer_loyalty_score: Optional[Decimal] = None  # 1-10 scale
    net_promoter_score: Optional[Decimal] = None  # -100 to +100
    customer_retention_rate: Optional[Decimal] = None  # 0-100 percentage
    
    # Quality & Performance Metrics
    return_rate: Optional[Decimal] = None  # 0-100 percentage
    defect_rate: Optional[Decimal] = None  # 0-100 percentage
    warranty_claim_rate: Optional[Decimal] = None  # 0-100 percentage
    support_ticket_frequency: Optional[Decimal] = None  # Tickets per 100 units sold
    
    # Innovation & Development
    product_lifecycle_stage: str = "mature"  # introduction, growth, mature, decline
    time_to_obsolescence: Optional[int] = None  # Estimated months until obsolete
    innovation_investment: str = "moderate"  # high, moderate, low, none
    feature_update_frequency: str = "regular"  # frequent, regular, rare, none
    
    # Geographic Intelligence
    regional_availability: Dict[str, bool] = {}  # Availability by region
    regional_pricing: Dict[str, Decimal] = {}  # Pricing by region
    shipping_costs: Dict[str, Decimal] = {}  # Shipping costs to different regions
    import_duties: Dict[str, Decimal] = {}  # Import duties by region
    
    # Economic Factors
    economic_sensitivity: str = "moderate"  # low, moderate, high
    inflation_impact: str = "moderate"  # low, moderate, high
    currency_exposure: List[str] = []  # Currencies that affect pricing
    commodity_dependencies: List[str] = []  # Raw materials that affect cost
    
    # Competitive Intelligence
    competitive_pricing: Dict[str, Decimal] = {}  # Competitor pricing (competitor_name: price)
    competitive_advantages: List[str] = []  # Advantages over competitors
    competitive_threats: List[str] = []  # Threats from competitors
    market_disruption_risk: str = "low"  # low, moderate, high
    
    # Regulatory & Compliance
    regulatory_changes: List[Dict[str, Any]] = []  # Upcoming regulatory changes
    compliance_cost_impact: Optional[Decimal] = None  # Cost impact of compliance
    certification_status: Dict[str, str] = {}  # Certification statuses
    regulatory_risk: str = "low"  # low, moderate, high
    
    # Sustainability Intelligence
    environmental_score: Optional[Decimal] = None  # 1-10 scale
    carbon_footprint: Optional[Dict[str, Any]] = None  # Carbon footprint data
    sustainability_certifications: List[str] = []  # Environmental certifications
    circular_economy_score: Optional[Decimal] = None  # Recycling/reuse potential
    
    # Technology Intelligence
    technology_maturity: str = "mature"  # emerging, developing, mature, legacy
    automation_potential: str = "moderate"  # low, moderate, high
    digital_integration: str = "partial"  # none, partial, full, advanced
    iot_compatibility: bool = False
    
    # Financial Intelligence
    cost_structure: Dict[str, Decimal] = {}  # Breakdown of cost components
    margin_pressure: str = "stable"  # decreasing, stable, increasing
    investment_requirements: Optional[Decimal] = None  # Capex needed for this product
    roi_timeframe: Optional[int] = None  # Months to break even
    
    # Risk Assessment
    overall_risk_score: Optional[Decimal] = None  # 1-10 scale (higher = more risky)
    risk_factors: List[str] = []  # Identified risk factors
    mitigation_strategies: List[str] = []  # Risk mitigation approaches
    risk_trend: str = "stable"  # increasing, stable, decreasing
    
    # Predictive Intelligence (AI-generated)
    price_forecast_30d: Optional[Decimal] = None
    price_forecast_90d: Optional[Decimal] = None
    demand_forecast_30d: Optional[str] = None  # increasing, stable, decreasing
    demand_forecast_90d: Optional[str] = None
    availability_forecast: str = "stable"  # improving, stable, deteriorating
    
    # Data Sources & Quality
    data_sources: List[str] = []  # api, scraping, manual, third_party, industry_report
    data_freshness_hours: Optional[int] = None  # Hours since last update
    data_reliability_score: Optional[Decimal] = None  # 1-10 scale
    last_validation: Optional[datetime] = None
    
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True,
        'versioned': True  # Track market changes over time
    }
    
    __indexes__ = [
        {'name': 'idx_market_intel_product_supplier', 'fields': ['product_id', 'supplier_id'], 'unique': True},
        {'name': 'idx_market_intel_pricing', 'fields': ['current_pricing', 'pricing_last_updated']},
        {'name': 'idx_market_intel_availability', 'fields': ['availability_status', 'stock_level_indicator']},
        {'name': 'idx_market_intel_lead_time', 'fields': ['lead_time_days', 'lead_time_reliability']},
        {'name': 'idx_market_intel_trends', 'fields': ['price_trend', 'demand_trend']},
        {'name': 'idx_market_intel_performance', 'fields': ['customer_satisfaction', 'return_rate']},
        {'name': 'idx_market_intel_risk', 'fields': ['overall_risk_score', 'supply_chain_risk']},
        {'name': 'idx_market_intel_forecast', 'fields': ['price_forecast_30d', 'demand_forecast_30d']},
        {'name': 'idx_market_intel_data_quality', 'fields': ['data_reliability_score', 'data_freshness_hours']}
    ]

@db.model
class CompetitorIntelligence:
    """Intelligence about competitor products and strategies"""
    competitor_name: str
    competitor_type: str = "direct"  # direct, indirect, substitute, emerging
    
    # Competitor Profile
    company_size: str = "unknown"  # startup, sme, enterprise, multinational
    market_focus: List[str] = []  # Geographic or segment focus
    business_model: str = "traditional"  # traditional, innovative, disruptive
    
    # Product Portfolio
    competing_products: List[Dict[str, Any]] = []  # Their products that compete with ours
    product_portfolio_breadth: str = "moderate"  # narrow, moderate, broad, comprehensive
    innovation_frequency: str = "regular"  # rare, occasional, regular, frequent
    
    # Market Position
    market_share: Optional[Decimal] = None  # 0-100 percentage
    market_trend: str = "stable"  # growing, stable, declining
    geographic_presence: List[str] = []  # Regions where they operate
    customer_base: List[str] = []  # Types of customers they serve
    
    # Competitive Strategy
    pricing_strategy: str = "competitive"  # premium, competitive, value, penetration
    differentiation_strategy: str = "features"  # price, features, service, brand
    go_to_market_strategy: str = "traditional"  # direct, channel, online, hybrid
    
    # Strengths & Weaknesses
    competitive_strengths: List[str] = []  # What they do well
    competitive_weaknesses: List[str] = []  # Where they struggle
    unique_advantages: List[str] = []  # What makes them special
    
    # Financial Intelligence
    financial_health: str = "stable"  # strong, stable, weak, troubled
    investment_activity: str = "moderate"  # high, moderate, low, none
    funding_sources: List[str] = []  # private, public, venture, debt
    
    # Threat Assessment
    competitive_threat_level: str = "moderate"  # low, moderate, high, critical
    threat_trend: str = "stable"  # increasing, stable, decreasing
    disruptive_potential: str = "low"  # low, moderate, high
    
    # Intelligence Sources
    intelligence_sources: List[str] = []  # public_filings, market_research, customer_feedback
    intelligence_quality: Optional[Decimal] = None  # 1-10 scale
    last_intelligence_update: Optional[datetime] = None
    
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True,
        'versioned': True
    }
    
    __indexes__ = [
        {'name': 'idx_competitor_name', 'fields': ['competitor_name'], 'unique': True},
        {'name': 'idx_competitor_type_threat', 'fields': ['competitor_type', 'competitive_threat_level']},
        {'name': 'idx_competitor_market', 'fields': ['market_share', 'market_trend']},
        {'name': 'idx_competitor_strategy', 'fields': ['pricing_strategy', 'differentiation_strategy']},
        {'name': 'idx_competitor_presence', 'fields': ['geographic_presence'], 'type': 'gin'}
    ]

@db.model
class MarketTrend:
    """Market trends and industry intelligence"""
    trend_id: str  # Unique identifier for the trend
    trend_name: str
    trend_category: str  # technology, market, regulatory, economic, social
    
    # Trend Details
    description: str
    detailed_analysis: Optional[str] = None
    affected_industries: List[str] = []  # Industries impacted by this trend
    affected_product_categories: List[str] = []  # Product categories impacted
    
    # Trend Dynamics
    trend_stage: str = "emerging"  # emerging, developing, mature, declining
    trend_magnitude: str = "moderate"  # minor, moderate, major, transformational
    trend_duration: str = "medium_term"  # short_term, medium_term, long_term, permanent
    trend_geographic_scope: str = "global"  # local, regional, national, global
    
    # Impact Assessment
    market_impact: str = "moderate"  # minimal, moderate, significant, transformational
    impact_timeline: str = "2-5_years"  # immediate, 1-2_years, 2-5_years, 5+_years
    affected_stakeholders: List[str] = []  # suppliers, manufacturers, customers, regulators
    
    # Business Implications
    opportunity_areas: List[str] = []  # New opportunities created
    threat_areas: List[str] = []  # Threats or risks created
    investment_implications: List[str] = []  # Investment needs or opportunities
    strategic_implications: List[str] = []  # Strategic considerations
    
    # Products & Suppliers Affected
    affected_products: List[int] = []  # Product IDs likely to be affected
    affected_suppliers: List[int] = []  # Supplier IDs likely to be affected
    impact_type: str = "mixed"  # positive, negative, mixed, neutral
    
    # Confidence & Sources
    confidence_level: Decimal  # 1-10 scale in the trend analysis
    evidence_quality: str = "moderate"  # weak, moderate, strong, compelling
    information_sources: List[str] = []  # industry_reports, expert_opinions, market_data
    
    # Monitoring
    monitoring_indicators: List[str] = []  # Key indicators to track this trend
    last_assessment_update: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True,
        'versioned': True  # Track trend evolution
    }
    
    __indexes__ = [
        {'name': 'idx_trend_id', 'fields': ['trend_id'], 'unique': True},
        {'name': 'idx_trend_category_stage', 'fields': ['trend_category', 'trend_stage']},
        {'name': 'idx_trend_impact', 'fields': ['market_impact', 'impact_timeline']},
        {'name': 'idx_trend_affected_products', 'fields': ['affected_products'], 'type': 'gin'},
        {'name': 'idx_trend_affected_suppliers', 'fields': ['affected_suppliers'], 'type': 'gin'},
        {'name': 'idx_trend_confidence', 'fields': ['confidence_level', 'evidence_quality']}
    ]

@db.model
class PricingIntelligence:
    """Advanced pricing intelligence and optimization data"""
    product_id: int  # FK to Product
    supplier_id: int  # FK to Supplier
    
    # Pricing Structure
    base_price: Decimal
    currency: str = "USD"
    pricing_model: str = "fixed"  # fixed, tiered, volume, dynamic, negotiated
    price_validity_days: Optional[int] = None
    
    # Volume Pricing
    volume_tiers: List[Dict[str, Any]] = []  # Quantity breaks with pricing
    bulk_discount_available: bool = False
    maximum_discount_percentage: Optional[Decimal] = None
    minimum_order_quantity: int = 1
    maximum_order_quantity: Optional[int] = None
    
    # Dynamic Pricing Factors
    demand_sensitivity: Optional[Decimal] = None  # -10 to +10 scale
    supply_sensitivity: Optional[Decimal] = None  # -10 to +10 scale
    seasonal_adjustments: List[Dict[str, Any]] = []  # Seasonal pricing variations
    competitive_pricing_pressure: str = "moderate"  # low, moderate, high, intense
    
    # Cost Intelligence
    estimated_cost_structure: Dict[str, Decimal] = {}  # materials, labor, overhead, margin
    cost_trend: str = "stable"  # decreasing, stable, increasing, volatile
    margin_estimate: Optional[Decimal] = None  # Estimated gross margin percentage
    
    # Market Context
    price_position_vs_market: str = "competitive"  # premium, competitive, value, budget
    price_elasticity: Optional[Decimal] = None  # Demand response to price changes
    substitution_risk: str = "low"  # low, moderate, high (risk of being substituted due to price)
    
    # Negotiation Intelligence
    negotiation_flexibility: str = "moderate"  # none, limited, moderate, high
    typical_negotiated_discount: Optional[Decimal] = None  # 0-100 percentage
    negotiation_factors: List[str] = []  # volume, relationship, timing, competition
    
    # Temporal Intelligence
    price_history_volatility: Optional[Decimal] = None  # Standard deviation of price changes
    price_cycle_patterns: List[Dict[str, Any]] = []  # Recurring price patterns
    promotional_frequency: str = "occasional"  # never, rare, occasional, frequent
    
    # Optimization Recommendations
    optimal_price_point: Optional[Decimal] = None  # AI-recommended optimal price
    price_optimization_confidence: Optional[Decimal] = None  # 1-10 confidence scale
    pricing_recommendations: List[str] = []  # Specific pricing recommendations
    
    # Data Sources
    pricing_data_sources: List[str] = []  # supplier_api, web_scraping, manual_entry
    data_collection_frequency: str = "daily"  # hourly, daily, weekly, monthly
    last_price_update: datetime
    price_data_reliability: Optional[Decimal] = None  # 1-10 scale
    
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True,
        'versioned': True  # Track pricing evolution
    }
    
    __indexes__ = [
        {'name': 'idx_pricing_intel_product_supplier', 'fields': ['product_id', 'supplier_id'], 'unique': True},
        {'name': 'idx_pricing_intel_base_price', 'fields': ['base_price', 'currency']},
        {'name': 'idx_pricing_intel_model', 'fields': ['pricing_model']},
        {'name': 'idx_pricing_intel_position', 'fields': ['price_position_vs_market']},
        {'name': 'idx_pricing_intel_optimization', 'fields': ['optimal_price_point', 'price_optimization_confidence']},
        {'name': 'idx_pricing_intel_update', 'fields': ['last_price_update', 'price_data_reliability']}
    ]

# Export all models for use in other modules
__all__ = [
    'MarketIntelligence', 
    'CompetitorIntelligence', 
    'MarketTrend', 
    'PricingIntelligence'
]