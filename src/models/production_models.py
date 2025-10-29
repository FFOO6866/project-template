"""
Production DataFlow Models for Horme POV
Unified PostgreSQL schema replacing multiple SQLite databases
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from dataflow import DataFlow

# Initialize DataFlow with PostgreSQL
db = DataFlow()

@db.model
class Category:
    """Product categories with hierarchical support"""
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'multi_tenant': False,
        'soft_delete': False,
        'audit_log': True
    }
    
    __indexes__ = [
        {'name': 'idx_category_slug', 'fields': ['slug'], 'unique': True},
        {'name': 'idx_category_active', 'fields': ['is_active']}
    ]

@db.model  
class Brand:
    """Product brands and manufacturers"""
    name: str
    slug: str
    description: Optional[str] = None
    website_url: Optional[str] = None
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True
    }
    
    __indexes__ = [
        {'name': 'idx_brand_slug', 'fields': ['slug'], 'unique': True},
        {'name': 'idx_brand_active', 'fields': ['is_active']}
    ]

@db.model
class Supplier:
    """Suppliers and data sources"""
    name: str
    website: str
    api_endpoint: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool = True
    scraping_config: Optional[Dict[str, Any]] = None
    last_scraped: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True
    }
    
    __indexes__ = [
        {'name': 'idx_supplier_active', 'fields': ['is_active']},
        {'name': 'idx_supplier_website', 'fields': ['website'], 'unique': True}
    ]

@db.model
class Product:
    """Core product catalog with enrichment tracking"""
    sku: str
    name: str
    slug: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    supplier_id: Optional[int] = None
    status: str = "active"  # active, inactive, discontinued
    is_published: bool = True
    availability: str = "in_stock"  # in_stock, out_of_stock, backorder
    currency: str = "USD"
    base_price: Optional[Decimal] = None
    catalogue_item_id: Optional[int] = None
    source_url: Optional[str] = None
    images_url: Optional[str] = None
    
    # Enrichment fields
    enriched_description: Optional[str] = None
    technical_specs: Optional[Dict[str, Any]] = None
    supplier_info: Optional[Dict[str, Any]] = None
    competitor_data: Optional[Dict[str, Any]] = None
    enrichment_status: str = "pending"  # pending, enriched, failed
    enrichment_source: Optional[str] = None
    last_enriched: Optional[datetime] = None
    
    # Import tracking
    import_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'multi_tenant': False,
        'soft_delete': True,  # Keep deleted products for audit
        'versioned': True,    # Track price/description changes
        'audit_log': True
    }
    
    __indexes__ = [
        {'name': 'idx_product_sku', 'fields': ['sku'], 'unique': True},
        {'name': 'idx_product_slug', 'fields': ['slug'], 'unique': True},
        {'name': 'idx_product_category', 'fields': ['category_id', 'status']},
        {'name': 'idx_product_brand', 'fields': ['brand_id', 'status']},
        {'name': 'idx_product_supplier', 'fields': ['supplier_id', 'status']},
        {'name': 'idx_product_status', 'fields': ['status', 'is_published']},
        {'name': 'idx_product_enrichment', 'fields': ['enrichment_status']},
        {'name': 'idx_product_fulltext', 'fields': ['name', 'description'], 'type': 'gin'}
    ]

@db.model
class ProductPricing:
    """Product pricing history and variations"""
    product_id: int
    price_type: str = "base"  # base, sale, wholesale, retail
    amount: Decimal
    currency: str = "USD"
    effective_from: datetime
    effective_to: Optional[datetime] = None
    supplier_id: Optional[int] = None
    minimum_quantity: int = 1
    created_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True
    }
    
    __indexes__ = [
        {'name': 'idx_pricing_product', 'fields': ['product_id', 'price_type']},
        {'name': 'idx_pricing_effective', 'fields': ['effective_from', 'effective_to']},
        {'name': 'idx_pricing_supplier', 'fields': ['supplier_id', 'product_id']}
    ]

@db.model
class ProductSpecification:
    """Technical specifications and attributes"""
    product_id: int
    spec_name: str
    spec_value: str
    spec_category: Optional[str] = None
    unit: Optional[str] = None
    is_searchable: bool = True
    created_at: datetime = None
    
    __dataflow__ = {
        'audit_log': False  # High volume data
    }
    
    __indexes__ = [
        {'name': 'idx_spec_product', 'fields': ['product_id']},
        {'name': 'idx_spec_name_value', 'fields': ['spec_name', 'spec_value']},
        {'name': 'idx_spec_searchable', 'fields': ['is_searchable', 'spec_name']}
    ]

@db.model
class ProductInventory:
    """Inventory tracking and stock levels"""
    product_id: int
    supplier_id: int
    quantity_available: int = 0
    quantity_reserved: int = 0
    reorder_level: int = 10
    reorder_quantity: int = 100
    last_updated: datetime
    warehouse_location: Optional[str] = None
    
    __dataflow__ = {
        'audit_log': True
    }
    
    __indexes__ = [
        {'name': 'idx_inventory_product', 'fields': ['product_id'], 'unique': True},
        {'name': 'idx_inventory_supplier', 'fields': ['supplier_id']},
        {'name': 'idx_inventory_reorder', 'fields': ['quantity_available', 'reorder_level']}
    ]

@db.model
class WorkRecommendation:
    """AI-generated work recommendations"""
    title: str
    description: str
    category: str
    priority: str = "medium"  # low, medium, high, urgent
    status: str = "open"  # open, in_progress, completed, cancelled
    estimated_hours: Optional[int] = None
    estimated_value: Optional[Decimal] = None
    related_products: Optional[List[int]] = None
    client_requirements: Optional[Dict[str, Any]] = None
    recommendation_source: str  # ai_analysis, manual, rfp_analysis
    confidence_score: Optional[float] = None
    created_at: datetime = None
    updated_at: datetime = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    
    __dataflow__ = {
        'audit_log': True,
        'versioned': True
    }
    
    __indexes__ = [
        {'name': 'idx_workrec_status', 'fields': ['status', 'priority']},
        {'name': 'idx_workrec_category', 'fields': ['category', 'status']},
        {'name': 'idx_workrec_assigned', 'fields': ['assigned_to', 'status']},
        {'name': 'idx_workrec_due', 'fields': ['due_date', 'status']},
        {'name': 'idx_workrec_confidence', 'fields': ['confidence_score']}
    ]

@db.model
class RFPDocument:
    """Request for Proposal documents and analysis"""
    document_name: str
    document_path: str
    file_size: int
    file_type: str
    upload_date: datetime
    parsed_content: Optional[str] = None
    parsed_requirements: Optional[Dict[str, Any]] = None
    analysis_status: str = "pending"  # pending, analyzed, failed
    analysis_results: Optional[Dict[str, Any]] = None
    client_name: Optional[str] = None
    project_value: Optional[Decimal] = None
    deadline: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True,
        'versioned': True
    }
    
    __indexes__ = [
        {'name': 'idx_rfp_status', 'fields': ['analysis_status']},
        {'name': 'idx_rfp_client', 'fields': ['client_name', 'upload_date']},
        {'name': 'idx_rfp_deadline', 'fields': ['deadline']},
        {'name': 'idx_rfp_value', 'fields': ['project_value']}
    ]

@db.model
class Quotation:
    """Generated quotations and proposals"""
    rfp_id: Optional[int] = None
    quotation_number: str
    client_name: str
    client_email: Optional[str] = None
    project_title: str
    total_amount: Decimal
    currency: str = "USD"
    status: str = "draft"  # draft, sent, accepted, rejected, expired
    valid_until: datetime
    line_items: List[Dict[str, Any]]
    terms_conditions: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None
    sent_date: Optional[datetime] = None
    response_date: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True,
        'versioned': True
    }
    
    __indexes__ = [
        {'name': 'idx_quotation_number', 'fields': ['quotation_number'], 'unique': True},
        {'name': 'idx_quotation_status', 'fields': ['status', 'valid_until']},
        {'name': 'idx_quotation_client', 'fields': ['client_name', 'created_at']},
        {'name': 'idx_quotation_rfp', 'fields': ['rfp_id']},
        {'name': 'idx_quotation_amount', 'fields': ['total_amount', 'status']}
    ]

@db.model
class QuotationItem:
    """Individual line items in quotations"""
    quotation_id: int
    product_id: Optional[int] = None
    item_description: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    item_category: Optional[str] = None
    supplier_id: Optional[int] = None
    delivery_days: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True
    }
    
    __indexes__ = [
        {'name': 'idx_quotitem_quotation', 'fields': ['quotation_id']},
        {'name': 'idx_quotitem_product', 'fields': ['product_id']},
        {'name': 'idx_quotitem_supplier', 'fields': ['supplier_id']}
    ]

@db.model
class Customer:
    """Customer and client information"""
    name: str
    company_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    industry: Optional[str] = None
    customer_type: str = "prospect"  # prospect, active, inactive
    credit_limit: Optional[Decimal] = None
    payment_terms: str = "net_30"
    preferred_contact: str = "email"  # email, phone, both
    notes: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    __dataflow__ = {
        'audit_log': True,
        'soft_delete': True
    }
    
    __indexes__ = [
        {'name': 'idx_customer_email', 'fields': ['email'], 'unique': True},
        {'name': 'idx_customer_company', 'fields': ['company_name']},
        {'name': 'idx_customer_type', 'fields': ['customer_type']},
        {'name': 'idx_customer_industry', 'fields': ['industry']}
    ]

@db.model
class ActivityLog:
    """System activity and user actions tracking"""
    entity_type: str  # product, quotation, rfp, customer
    entity_id: int
    action: str  # created, updated, deleted, viewed, sent
    user_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    
    __dataflow__ = {
        'audit_log': False  # This IS the audit log
    }
    
    __indexes__ = [
        {'name': 'idx_activity_entity', 'fields': ['entity_type', 'entity_id']},
        {'name': 'idx_activity_user', 'fields': ['user_id', 'timestamp']},
        {'name': 'idx_activity_timestamp', 'fields': ['timestamp']},
        {'name': 'idx_activity_action', 'fields': ['action', 'entity_type']}
    ]

@db.model
class OSHAStandard:
    """OSHA safety standards (29 CFR)"""
    cfr: str  # 29 CFR number
    title: str
    description: str
    requirements: str
    applies_to: List[str] = []  # Work types/activities
    required_ppe: List[str] = []  # Required PPE items
    mandatory: bool = True
    risk_level: str = "medium"  # low, medium, high, critical
    penalties: Optional[str] = None
    legal_reference_url: str  # osha.gov URL
    created_at: datetime = None
    updated_at: datetime = None

    __dataflow__ = {
        'audit_log': True,
        'versioned': True  # Track changes to standards
    }

    __indexes__ = [
        {'name': 'idx_osha_cfr', 'fields': ['cfr'], 'unique': True},
        {'name': 'idx_osha_risk_level', 'fields': ['risk_level']},
        {'name': 'idx_osha_applies_to', 'fields': ['applies_to'], 'type': 'gin'}
    ]

@db.model
class ANSIStandard:
    """ANSI/ISEA/ASTM safety standards"""
    standard: str  # ANSI standard number
    title: str
    description: str
    standard_type: str  # eye_protection, hearing_protection, etc.
    specifications: Dict[str, Any] = {}  # Technical specifications
    markings: Dict[str, Any] = {}  # Required markings
    test_requirements: Dict[str, Any] = {}  # Test methods
    product_types: List[str] = []  # Applicable product types
    reference_url: Optional[str] = None
    industries: List[str] = []  # Applicable industries
    created_at: datetime = None
    updated_at: datetime = None

    __dataflow__ = {
        'audit_log': True,
        'versioned': True
    }

    __indexes__ = [
        {'name': 'idx_ansi_standard', 'fields': ['standard'], 'unique': True},
        {'name': 'idx_ansi_type', 'fields': ['standard_type']},
        {'name': 'idx_ansi_product_types', 'fields': ['product_types'], 'type': 'gin'}
    ]

@db.model
class ToolRiskClassification:
    """Risk classifications for tools and equipment"""
    tool_name: str
    category: str  # power_tool, hand_tool, painting_tool, etc.
    risk_level: str  # low, medium, high, critical
    hazards: List[str]  # Array of hazards
    osha_standards: List[str] = []  # Applicable OSHA CFR numbers
    mandatory_ppe: List[str]  # Mandatory PPE items
    recommended_ppe: List[str] = []  # Recommended PPE items
    training_required: bool = False
    certification_required: bool = False
    created_at: datetime = None
    updated_at: datetime = None

    __dataflow__ = {
        'audit_log': True
    }

    __indexes__ = [
        {'name': 'idx_tool_name', 'fields': ['tool_name'], 'unique': True},
        {'name': 'idx_tool_category', 'fields': ['category']},
        {'name': 'idx_tool_risk_level', 'fields': ['risk_level']},
        {'name': 'idx_tool_hazards', 'fields': ['hazards'], 'type': 'gin'}
    ]

@db.model
class TaskHazardMapping:
    """Hazard mappings for specific tasks"""
    task_id: str  # Task identifier
    task_name: str
    hazards: List[str]  # Array of hazards
    risk_level: str  # low, medium, high, critical
    osha_standards: List[str] = []  # Applicable OSHA CFR numbers
    mandatory_ppe: List[str]  # Mandatory PPE items
    recommended_ppe: List[str] = []  # Recommended PPE items
    safety_notes: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

    __dataflow__ = {
        'audit_log': True
    }

    __indexes__ = [
        {'name': 'idx_task_id', 'fields': ['task_id'], 'unique': True},
        {'name': 'idx_task_risk_level', 'fields': ['risk_level']},
        {'name': 'idx_task_hazards', 'fields': ['hazards'], 'type': 'gin'}
    ]

@db.model
class ANSIEquipmentSpecification:
    """ANSI equipment specifications and certifications"""
    equipment_type: str  # safety_glasses, earplugs, etc.
    ansi_standard: str  # Reference to ANSI standard
    required_marking: Optional[str] = None
    protection_level: str  # basic, moderate, high, maximum
    specifications: Dict[str, Any] = {}
    suitable_for: List[str] = []  # Suitable applications
    not_suitable_for: List[str] = []  # Unsuitable applications
    test_specifications: Dict[str, Any] = {}
    notes: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

    __dataflow__ = {
        'audit_log': True
    }

    __indexes__ = [
        {'name': 'idx_equipment_type', 'fields': ['equipment_type'], 'unique': True},
        {'name': 'idx_equipment_standard', 'fields': ['ansi_standard']},
        {'name': 'idx_equipment_protection', 'fields': ['protection_level']}
    ]

# Export the DataFlow instance for use in other modules


# =============================================================================
# PRODUCT CLASSIFICATION MODELS (UNSPSC and ETIM)
# =============================================================================
# IMPORTANT: These models represent REAL data from official sources only.
# Data must be loaded using scripts/load_classification_data.py
#
# Data Sources:
#   UNSPSC: Purchase from https://www.unspsc.org/purchase-unspsc (~$500 USD)
#   ETIM: Membership required at https://www.etim-international.com/

@db.model
class UNSPSCCode:
    """UNSPSC (United Nations Standard Products and Services Code) classification.

    IMPORTANT: Data must be purchased from https://www.unspsc.org/
    Cost: Approximately $500 USD for commercial license

    UNSPSC provides a 4-level hierarchy:
    - Level 1: Segment (2 digits)
    - Level 2: Family (4 digits)
    - Level 3: Class (6 digits)
    - Level 4: Commodity (8 digits)
    """
    code: str  # 8-digit UNSPSC code (e.g., '10101501' for Cattle)
    segment: str  # Segment name
    family: str  # Family name
    class_: str  # Class name (class is Python keyword, so class_)
    commodity: str  # Commodity name
    title: str  # Full descriptive title
    definition: Optional[str] = None  # Detailed definition
    level: int  # 1=Segment, 2=Family, 3=Class, 4=Commodity
    created_at: datetime = None
    updated_at: datetime = None

    __dataflow__ = {
        'table_name': 'unspsc_codes',
        'audit_log': False,  # Reference data, no need for audit
        'soft_delete': False
    }

    __indexes__ = [
        {'name': 'idx_unspsc_code', 'fields': ['code'], 'unique': True},
        {'name': 'idx_unspsc_level', 'fields': ['level']},
        {'name': 'idx_unspsc_title', 'fields': ['title'], 'type': 'gin'},
        {'name': 'idx_unspsc_segment', 'fields': ['segment']},
        {'name': 'idx_unspsc_family', 'fields': ['family']}
    ]


@db.model
class ETIMClass:
    """ETIM (Electro-Technical Information Model) classification.

    IMPORTANT: Data requires ETIM membership
    Membership: https://www.etim-international.com/become-a-member/

    ETIM provides multi-lingual product classification for electro-technical products.
    """
    class_code: str  # ETIM class code (e.g., 'EC000001')
    version: str  # ETIM version (e.g., '9.0')
    description_en: str  # English description
    description_de: Optional[str] = None  # German description
    description_fr: Optional[str] = None  # French description
    description_nl: Optional[str] = None  # Dutch description
    parent_class: Optional[str] = None  # Parent class code for hierarchy
    features: Optional[Dict[str, Any]] = None  # Technical features (JSONB)
    created_at: datetime = None
    updated_at: datetime = None

    __dataflow__ = {
        'table_name': 'etim_classes',
        'audit_log': False,  # Reference data
        'soft_delete': False
    }

    __indexes__ = [
        {'name': 'idx_etim_class_code', 'fields': ['class_code'], 'unique': True},
        {'name': 'idx_etim_version', 'fields': ['version']},
        {'name': 'idx_etim_parent', 'fields': ['parent_class']},
        {'name': 'idx_etim_description_en', 'fields': ['description_en'], 'type': 'gin'},
        {'name': 'idx_etim_features', 'fields': ['features'], 'type': 'gin'}
    ]


@db.model
class ProductClassification:
    """Links products to UNSPSC and ETIM classifications.

    Stores classification assignments with confidence scores and metadata.
    Each product can have multiple classifications over time as AI improves.
    """
    product_id: int  # Reference to Product model
    unspsc_code: Optional[str] = None  # UNSPSC code (must exist in unspsc_codes table)
    etim_class: Optional[str] = None  # ETIM class code (must exist in etim_classes table)
    confidence: Decimal  # Confidence score (0.0-1.0)
    classification_method: str  # 'manual', 'ai', 'rules', 'import'
    classified_at: datetime  # When classification was made
    classified_by: Optional[str] = None  # User ID or system component name
    notes: Optional[str] = None  # Additional classification notes

    __dataflow__ = {
        'table_name': 'product_classifications',
        'audit_log': True,  # Track all classification changes
        'soft_delete': False
    }

    __indexes__ = [
        {'name': 'idx_product_classifications_product', 'fields': ['product_id']},
        {'name': 'idx_product_classifications_unspsc', 'fields': ['unspsc_code']},
        {'name': 'idx_product_classifications_etim', 'fields': ['etim_class']},
        {'name': 'idx_product_classifications_method', 'fields': ['classification_method']},
        {'name': 'idx_product_classifications_confidence', 'fields': ['confidence']}
    ]

    __constraints__ = [
        # Ensure at least one classification is provided
        {'type': 'check', 'expr': 'unspsc_code IS NOT NULL OR etim_class IS NOT NULL'},
        # Ensure confidence is in valid range
        {'type': 'check', 'expr': 'confidence >= 0 AND confidence <= 1'}
    ]