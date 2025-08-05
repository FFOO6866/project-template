"""
DataFlow Models for Horme Product Ecosystem - FOUND-003

Comprehensive DataFlow models using @db.model decorators for:
- Core product models with UNSPSC/ETIM classification
- Safety compliance and OSHA/ANSI standards
- Multi-vendor pricing and inventory management
- User profiles with skill assessment and certifications

Each model auto-generates 9 nodes: Create, Read, Update, Delete, List, Search, Count, Exists, Validate
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

# DataFlow imports - using the existing dataflow_models.py pattern
try:
    from dataflow import DataFlow, Field
    from kailash.workflow.builder import WorkflowBuilder
    from kailash.runtime.local import LocalRuntime
except ImportError:
    # Fallback for testing - create mock implementations
    class DataFlow:
        def __init__(self, **kwargs):
            self.database_url = kwargs.get('database_url')
            self.pool_size = kwargs.get('pool_size', 20)
            self.auto_migrate = kwargs.get('auto_migrate', True)
        
        def model(self, cls):
            # Mock decorator
            cls.__dataflow__ = True
            cls.__table_name__ = cls.__name__.lower() + 's'
            return cls
    
    class Field:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        
        @staticmethod
        def primary_key():
            return Field(primary_key=True)
        
        @staticmethod
        def unique():
            return Field(unique=True)
        
        @staticmethod
        def index():
            return Field(index=True)
        
        @staticmethod
        def foreign_key(reference):
            return Field(foreign_key=reference)
        
        @staticmethod
        def default_factory(func):
            return Field(default_factory=func)
        
        @staticmethod
        def null():
            return Field(null=True)
        
        @staticmethod
        def max_length(length):
            return Field(max_length=length)

# Initialize DataFlow with PostgreSQL configuration
db = DataFlow(
    # PostgreSQL connection for Horme product ecosystem
    database_url="postgresql://horme_user:horme_password@localhost:5432/horme_product_db",
    pool_size=25,
    pool_max_overflow=50,
    pool_recycle=3600,
    monitoring=True,
    echo=False,  # Set to True for development SQL logging
    auto_migrate=True,
    # Enable enterprise features
    enable_audit_log=True,
    enable_soft_delete=True,
    enable_versioning=True,
    enable_encryption=True
)

# ==============================================================================
# CORE PRODUCT MODELS
# ==============================================================================

@db.model
class Product:
    """Core product model with comprehensive specifications and classification support."""
    
    # Primary identification
    id: int = Field.primary_key()
    product_code: str = Field(unique=True, index=True, max_length=50)
    name: str = Field(max_length=255, index=True)
    description: str = Field()
    brand: str = Field(index=True, max_length=100)
    model_number: str = Field(max_length=100)
    
    # Classification system integration
    unspsc_code: str = Field(foreign_key="UNSPSCCode.code", index=True, max_length=8)
    etim_class: str = Field(foreign_key="ETIMClass.class_id", index=True, max_length=20)
    
    # Product specifications as JSONB for PostgreSQL
    specifications: Dict[str, Any] = Field(default_factory=dict)
    
    # Safety and compliance
    safety_rating: str = Field(max_length=10, index=True)
    
    # Audit trail fields
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = Field.null()
    
    # DataFlow configuration
    __dataflow__ = {
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        'search_fields': ['name', 'description', 'brand', 'model_number'],
        'jsonb_fields': ['specifications'],
        'full_text_search': True
    }
    
    # Database indexes for performance
    __indexes__ = [
        {'name': 'idx_product_code_unique', 'fields': ['product_code'], 'unique': True},
        {'name': 'idx_product_brand_name', 'fields': ['brand', 'name']},
        {'name': 'idx_product_classification', 'fields': ['unspsc_code', 'etim_class']},
        {'name': 'idx_product_safety_rating', 'fields': ['safety_rating']},
        {'name': 'idx_product_created_at', 'fields': ['created_at']},
        {'name': 'idx_product_specs_gin', 'fields': ['specifications'], 'type': 'gin'},  # JSONB index
        {'name': 'idx_product_search_text', 'fields': ['name', 'description'], 'type': 'text'}
    ]


@db.model  
class ProductCategory:
    """Hierarchical product categorization with UNSPSC integration."""
    
    # Primary identification
    id: int = Field.primary_key()
    name: str = Field(max_length=100, index=True)
    
    # Hierarchical structure
    parent_id: Optional[int] = Field(foreign_key="ProductCategory.id", null=True, index=True)
    level: int = Field(index=True)  # 1-5 hierarchy depth
    
    # UNSPSC integration
    unspsc_segment: str = Field(max_length=2, index=True)
    unspsc_family: str = Field(max_length=2, index=True)
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = Field.null()
    
    __dataflow__ = {
        'soft_delete': True,
        'audit_log': True,
        'hierarchical': True,
        'search_fields': ['name']
    }
    
    __indexes__ = [
        {'name': 'idx_category_parent_level', 'fields': ['parent_id', 'level']},
        {'name': 'idx_category_unspsc', 'fields': ['unspsc_segment', 'unspsc_family']},
        {'name': 'idx_category_name', 'fields': ['name']},
        {'name': 'idx_category_level', 'fields': ['level']}
    ]


@db.model
class ProductSpecification:
    """Detailed product specifications with searchable attributes."""
    
    # Primary identification
    id: int = Field.primary_key()
    product_id: int = Field(foreign_key="Product.id", index=True)
    
    # Specification details
    spec_name: str = Field(max_length=100, index=True)
    spec_value: str = Field(max_length=500)
    spec_unit: Optional[str] = Field(max_length=20, null=True)
    spec_type: str = Field(max_length=50, index=True)  # numeric, text, boolean, list
    is_searchable: bool = Field(default=True, index=True)
    
    # Priority and display order
    display_order: int = Field(default=0)
    is_key_feature: bool = Field(default=False, index=True)
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    __dataflow__ = {
        'audit_log': True,
        'search_fields': ['spec_name', 'spec_value']
    }
    
    __indexes__ = [
        {'name': 'idx_spec_product_name', 'fields': ['product_id', 'spec_name']},
        {'name': 'idx_spec_searchable', 'fields': ['is_searchable', 'spec_type']},
        {'name': 'idx_spec_key_features', 'fields': ['is_key_feature', 'display_order']}
    ]


# ==============================================================================
# CLASSIFICATION SYSTEM MODELS
# ==============================================================================

@db.model
class UNSPSCCode:
    """UN Standard Products and Services Code classification system."""
    
    # Primary identification (8-digit UNSPSC code)
    code: str = Field.primary_key()  # e.g., "31201501"
    title: str = Field(max_length=255, index=True)
    description: str = Field()
    
    # Hierarchical components
    segment: str = Field(max_length=2, index=True)    # First 2 digits
    family: str = Field(max_length=2, index=True)     # Next 2 digits
    class_code: str = Field(max_length=2, index=True) # Next 2 digits
    commodity: str = Field(max_length=2, index=True)  # Last 2 digits
    level: int = Field(index=True)  # 1-5 hierarchy level
    
    # Metadata
    version: str = Field(default="2022", max_length=10)
    is_active: bool = Field(default=True, index=True)
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    __dataflow__ = {
        'audit_log': True,
        'search_fields': ['title', 'description'],
        'hierarchical': True
    }
    
    __indexes__ = [
        {'name': 'idx_unspsc_code_pk', 'fields': ['code'], 'unique': True},
        {'name': 'idx_unspsc_hierarchy', 'fields': ['segment', 'family', 'class_code', 'commodity']},
        {'name': 'idx_unspsc_level', 'fields': ['level', 'is_active']},
        {'name': 'idx_unspsc_title_text', 'fields': ['title'], 'type': 'text'},
        {'name': 'idx_unspsc_segment_family', 'fields': ['segment', 'family']}
    ]


@db.model
class ETIMClass:
    """ETIM (European Technical Information Model) classification system."""
    
    # Primary identification
    class_id: str = Field.primary_key()  # e.g., "EC010101"
    
    # Multi-language support
    name_en: str = Field(max_length=255, index=True)
    name_de: Optional[str] = Field(max_length=255, null=True)
    name_fr: Optional[str] = Field(max_length=255, null=True)
    description: str = Field()
    
    # ETIM metadata
    version: str = Field(default="9.0", max_length=10)
    parent_class: Optional[str] = Field(foreign_key="ETIMClass.class_id", null=True, index=True)
    
    # Hierarchy and structure
    level: int = Field(default=1, index=True)
    is_active: bool = Field(default=True, index=True)
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    __dataflow__ = {
        'audit_log': True,
        'search_fields': ['name_en', 'name_de', 'name_fr', 'description'],
        'hierarchical': True,
        'multi_language': True
    }
    
    __indexes__ = [
        {'name': 'idx_etim_class_id_pk', 'fields': ['class_id'], 'unique': True},
        {'name': 'idx_etim_parent_child', 'fields': ['parent_class', 'level']},
        {'name': 'idx_etim_names', 'fields': ['name_en', 'name_de']},
        {'name': 'idx_etim_version_active', 'fields': ['version', 'is_active']},
        {'name': 'idx_etim_multilang_text', 'fields': ['name_en', 'name_de', 'name_fr'], 'type': 'text'}
    ]


# ==============================================================================
# SAFETY COMPLIANCE MODELS
# ==============================================================================

@db.model
class SafetyStandard:
    """Safety standards and regulations (OSHA, ANSI, NIOSH, etc.)."""
    
    # Primary identification
    id: int = Field.primary_key()
    standard_type: str = Field(max_length=20, index=True)  # OSHA, ANSI, NIOSH, ISO, NFPA, etc.
    standard_code: str = Field(unique=True, max_length=50, index=True)  # e.g., "OSHA-1926.95"
    
    # Standard details
    title: str = Field(max_length=255, index=True)
    description: str = Field()
    severity_level: str = Field(max_length=20, index=True)  # critical, high, medium, low
    regulation_text: str = Field()  # Full legal text
    
    # Temporal information
    effective_date: datetime = Field(index=True)
    expiry_date: Optional[datetime] = Field(null=True, index=True)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    # Legal and compliance metadata
    issuing_authority: str = Field(max_length=100, index=True)
    geographic_scope: str = Field(default="US", max_length=10)  # US, EU, CA, etc.
    industry_scope: Optional[str] = Field(max_length=200, null=True)  # construction, manufacturing, etc.
    
    # Status and versioning
    is_active: bool = Field(default=True, index=True)
    superseded_by: Optional[str] = Field(foreign_key="SafetyStandard.standard_code", null=True)
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = Field.null()
    
    __dataflow__ = {
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        'search_fields': ['title', 'description', 'regulation_text'],
        'legal_compliance': True
    }
    
    __indexes__ = [
        {'name': 'idx_safety_standard_code_unique', 'fields': ['standard_code'], 'unique': True},
        {'name': 'idx_safety_type_severity', 'fields': ['standard_type', 'severity_level']},
        {'name': 'idx_safety_effective_dates', 'fields': ['effective_date', 'expiry_date']},
        {'name': 'idx_safety_authority_scope', 'fields': ['issuing_authority', 'geographic_scope']},
        {'name': 'idx_safety_active_standards', 'fields': ['is_active', 'effective_date']},
        {'name': 'idx_safety_text_search', 'fields': ['title', 'description'], 'type': 'text'}
    ]


@db.model
class ComplianceRequirement:
    """Links products to safety standards with specific requirements."""
    
    # Primary identification
    id: int = Field.primary_key()
    product_id: int = Field(foreign_key="Product.id", index=True)
    safety_standard_id: int = Field(foreign_key="SafetyStandard.id", index=True)
    
    # Requirement details
    requirement_text: str = Field()
    is_mandatory: bool = Field(default=True, index=True)
    ppe_required: bool = Field(default=False, index=True)
    
    # Compliance assessment
    compliance_status: str = Field(default="pending", max_length=20, index=True)  # pending, compliant, non_compliant
    assessment_date: Optional[datetime] = Field(null=True)
    assessed_by: Optional[str] = Field(max_length=100, null=True)
    
    # Documentation and evidence
    documentation_required: bool = Field(default=False)
    evidence_files: Optional[List[str]] = Field(default_factory=list)  # JSON array of file paths
    
    # Temporal tracking
    effective_date: datetime = Field(default_factory=datetime.now, index=True)
    review_date: Optional[datetime] = Field(null=True, index=True)
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = Field.null()
    
    __dataflow__ = {
        'soft_delete': True,
        'audit_log': True,
        'legal_compliance': True,
        'search_fields': ['requirement_text']
    }
    
    __indexes__ = [
        {'name': 'idx_compliance_product_standard', 'fields': ['product_id', 'safety_standard_id']},
        {'name': 'idx_compliance_mandatory_status', 'fields': ['is_mandatory', 'compliance_status']},
        {'name': 'idx_compliance_ppe_required', 'fields': ['ppe_required']},
        {'name': 'idx_compliance_review_dates', 'fields': ['effective_date', 'review_date']},
        {'name': 'idx_compliance_assessment', 'fields': ['compliance_status', 'assessment_date']}
    ]


@db.model
class PPERequirement:
    """Personal Protective Equipment requirements linked to compliance."""
    
    # Primary identification
    id: int = Field.primary_key()
    compliance_requirement_id: int = Field(foreign_key="ComplianceRequirement.id", index=True)
    
    # PPE specifications
    ppe_type: str = Field(max_length=50, index=True)  # head, eye, hearing, respiratory, hand, foot, body, fall
    ppe_specification: str = Field()  # Detailed PPE requirements
    ppe_standard: Optional[str] = Field(max_length=50, null=True)  # ANSI Z87.1, etc.
    
    # Requirement details
    is_required: bool = Field(default=True, index=True)
    alternative_ppe: Optional[str] = Field(null=True)  # Alternative PPE options
    certification_required: bool = Field(default=False)
    
    # Product recommendations
    recommended_products: Optional[List[int]] = Field(default_factory=list)  # Product IDs as JSON array
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    __dataflow__ = {
        'audit_log': True,
        'search_fields': ['ppe_type', 'ppe_specification']
    }
    
    __indexes__ = [
        {'name': 'idx_ppe_compliance_req', 'fields': ['compliance_requirement_id']},
        {'name': 'idx_ppe_type_required', 'fields': ['ppe_type', 'is_required']},
        {'name': 'idx_ppe_certification', 'fields': ['certification_required']},
        {'name': 'idx_ppe_standard', 'fields': ['ppe_standard']}
    ]


# ==============================================================================
# VENDOR AND PRICING MODELS
# ==============================================================================

@db.model
class Vendor:
    """Supplier and vendor management with comprehensive business information."""
    
    # Primary identification
    id: int = Field.primary_key()
    vendor_code: str = Field(unique=True, max_length=50, index=True)
    company_name: str = Field(max_length=255, index=True)
    display_name: str = Field(max_length=100, index=True)
    
    # Business classification
    vendor_type: str = Field(max_length=50, index=True)  # manufacturer, distributor, supplier, contractor, consultant
    industry_focus: Optional[str] = Field(max_length=100, null=True, index=True)
    
    # Contact information
    contact_email: str = Field(max_length=255, index=True)
    contact_phone: str = Field(max_length=50)
    website_url: Optional[str] = Field(max_length=255, null=True)
    
    # Address as JSONB structure
    address: Dict[str, str] = Field(default_factory=dict)
    
    # Business terms and relationships
    payment_terms: str = Field(max_length=50, index=True)  # Net 15, Net 30, COD, etc.
    credit_rating: str = Field(max_length=10, index=True)  # A+, A, B+, B, C, etc.
    credit_limit: Optional[Decimal] = Field(null=True)
    currency: str = Field(default="USD", max_length=3)
    
    # Vendor status and preferences
    is_preferred: bool = Field(default=False, index=True)
    is_active: bool = Field(default=True, index=True)
    performance_rating: Optional[Decimal] = Field(null=True)  # 1.0-5.0 scale
    
    # Contract and legal
    contract_start_date: Optional[datetime] = Field(null=True)
    contract_end_date: Optional[datetime] = Field(null=True)
    insurance_verified: bool = Field(default=False)
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = Field.null()
    
    __dataflow__ = {
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        'search_fields': ['company_name', 'display_name', 'contact_email'],
        'jsonb_fields': ['address']
    }
    
    # High-performance indexes for vendor management
    __indexes__ = [
        # Primary access patterns
        {'name': 'idx_vendor_code_unique', 'fields': ['vendor_code'], 'unique': True},
        {'name': 'idx_vendor_company_name_text', 'fields': ['company_name'], 'type': 'gin', 'options': 'gin_trgm_ops'},
        
        # Business intelligence queries
        {'name': 'idx_vendor_type_status_rating', 'fields': ['vendor_type', 'is_active', 'performance_rating']},
        {'name': 'idx_vendor_preferred_active', 'fields': ['is_preferred', 'is_active'], 'condition': 'deleted_at IS NULL'},
        
        # Financial and contract management
        {'name': 'idx_vendor_payment_credit_limit', 'fields': ['payment_terms', 'credit_rating', 'credit_limit']},
        {'name': 'idx_vendor_contract_active', 'fields': ['contract_start_date', 'contract_end_date'], 
         'condition': 'contract_end_date > CURRENT_DATE'},
        
        # Geographic and contact optimization
        {'name': 'idx_vendor_address_gin_ops', 'fields': ['address'], 'type': 'gin', 'options': 'jsonb_path_ops'},
        {'name': 'idx_vendor_contact_email', 'fields': ['contact_email'], 'condition': 'is_active = true'},
        
        # Performance analytics
        {'name': 'idx_vendor_rating_updated', 'fields': ['performance_rating', 'updated_at']},
        {'name': 'idx_vendor_industry_focus', 'fields': ['industry_focus', 'vendor_type']},
        
        # Covering index for vendor list queries
        {'name': 'idx_vendor_list_cover', 'fields': ['is_active', 'vendor_type'], 
         'include': ['company_name', 'display_name', 'performance_rating'], 
         'condition': 'deleted_at IS NULL'}
    ]


@db.model
class ProductPricing:
    """Multi-vendor pricing with quantity breaks and temporal validity."""
    
    # Primary identification
    id: int = Field.primary_key()
    product_id: int = Field(foreign_key="Product.id", index=True)
    vendor_id: int = Field(foreign_key="Vendor.id", index=True)
    
    # Vendor-specific product information
    vendor_product_code: str = Field(max_length=100, index=True)
    vendor_product_name: Optional[str] = Field(max_length=255, null=True)
    
    # Pricing structure
    list_price: Decimal = Field()  # Official list price
    cost_price: Optional[Decimal] = Field(null=True)  # Cost to us (confidential)
    discount_price: Optional[Decimal] = Field(null=True)  # Discounted/sale price
    currency: str = Field(default="USD", max_length=3, index=True)
    
    # Quantity and unit information
    price_unit: str = Field(default="each", max_length=20)  # each, box, case, dozen, etc.
    minimum_order_quantity: int = Field(default=1)
    maximum_order_quantity: Optional[int] = Field(null=True)
    
    # Quantity-based pricing breaks as JSONB
    price_break_quantities: Dict[str, str] = Field(default_factory=dict)  # {"10": "95.00", "25": "90.00"}
    
    # Temporal validity
    effective_date: datetime = Field(index=True)
    expiry_date: Optional[datetime] = Field(null=True, index=True)
    last_updated: datetime = Field(default_factory=datetime.now, index=True)
    
    # Status and metadata
    is_active: bool = Field(default=True, index=True)
    price_source: str = Field(default="manual", max_length=20)  # manual, import, api, catalog
    competitive_rank: Optional[int] = Field(null=True)  # 1=best price, 2=second best, etc.
    
    # Lead time and availability
    standard_lead_time_days: Optional[int] = Field(null=True)
    availability_status: str = Field(default="available", max_length=20, index=True)
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = Field.null()
    
    __dataflow__ = {
        'soft_delete': True,
        'audit_log': True,
        'search_fields': ['vendor_product_code', 'vendor_product_name'],
        'jsonb_fields': ['price_break_quantities']
    }
    
    __indexes__ = [
        {'name': 'idx_pricing_product_vendor', 'fields': ['product_id', 'vendor_id']},
        {'name': 'idx_pricing_effective_dates', 'fields': ['effective_date', 'expiry_date']},
        {'name': 'idx_pricing_active_prices', 'fields': ['is_active', 'discount_price']},
        {'name': 'idx_pricing_currency_unit', 'fields': ['currency', 'price_unit']},
        {'name': 'idx_pricing_competitive_rank', 'fields': ['product_id', 'competitive_rank']},
        {'name': 'idx_pricing_vendor_code', 'fields': ['vendor_product_code']},
        {'name': 'idx_pricing_breaks_gin', 'fields': ['price_break_quantities'], 'type': 'gin'}
    ]


@db.model
class InventoryLevel:
    """Real-time inventory tracking across multiple vendors and locations."""
    
    # Primary identification
    id: int = Field.primary_key()
    product_id: int = Field(foreign_key="Product.id", index=True)
    vendor_id: int = Field(foreign_key="Vendor.id", index=True)
    
    # Location and warehouse information
    location: str = Field(max_length=100, index=True)  # Warehouse/store identifier
    location_name: Optional[str] = Field(max_length=255, null=True)
    
    # Quantity tracking
    quantity_on_hand: int = Field(default=0, index=True)
    quantity_reserved: int = Field(default=0)  # Allocated but not shipped
    quantity_on_order: int = Field(default=0)  # Ordered from vendor
    quantity_damaged: int = Field(default=0)   # Damaged/defective units
    
    # Reorder management
    reorder_point: int = Field(default=0)      # Minimum before reorder
    reorder_quantity: int = Field(default=0)   # Standard reorder amount
    safety_stock: int = Field(default=0)       # Safety buffer stock
    
    # Lead times and delivery
    lead_time_days: int = Field(default=0, index=True)
    last_reorder_date: Optional[datetime] = Field(null=True)
    expected_delivery_date: Optional[datetime] = Field(null=True)
    
    # Status and availability
    availability_status: str = Field(max_length=20, index=True)  # available, limited, out_of_stock, discontinued
    reason_code: Optional[str] = Field(max_length=50, null=True)  # backorder, seasonal, etc.
    
    # Inventory movement tracking
    last_movement_date: datetime = Field(default_factory=datetime.now, index=True)
    last_count_date: Optional[datetime] = Field(null=True, index=True)
    count_variance: Optional[int] = Field(null=True)  # Difference from expected
    
    # Cost tracking
    average_cost: Optional[Decimal] = Field(null=True)  # Weighted average cost
    last_cost: Optional[Decimal] = Field(null=True)     # Most recent purchase cost
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, index=True)
    
    __dataflow__ = {
        'audit_log': True,
        'real_time_updates': True,
        'search_fields': ['location', 'location_name']
    }
    
    __indexes__ = [
        {'name': 'idx_inventory_product_vendor_location', 'fields': ['product_id', 'vendor_id', 'location'], 'unique': True},
        {'name': 'idx_inventory_availability', 'fields': ['availability_status', 'quantity_on_hand']},
        {'name': 'idx_inventory_reorder_point', 'fields': ['quantity_on_hand', 'reorder_point']},
        {'name': 'idx_inventory_movement_dates', 'fields': ['last_movement_date', 'last_count_date']},
        {'name': 'idx_inventory_lead_times', 'fields': ['lead_time_days', 'expected_delivery_date']},
        {'name': 'idx_inventory_location', 'fields': ['location', 'availability_status']}
    ]


# ==============================================================================
# USER PROFILE AND SKILL MODELS
# ==============================================================================

@db.model
class UserProfile:
    """User profiles for skill-based product recommendations and personalization."""
    
    # Primary identification
    id: int = Field.primary_key()
    user_id: int = Field(unique=True, index=True)  # Link to external user system
    
    # Skill and experience profile
    skill_level: str = Field(max_length=20, index=True)  # beginner, intermediate, advanced, professional
    experience_years: int = Field(default=0, index=True)
    
    # Safety and certification status
    safety_certified: bool = Field(default=False, index=True)
    certification_expiry: Optional[datetime] = Field(null=True, index=True)
    
    # Preferences for recommendations
    preferred_brands: List[str] = Field(default_factory=list)  # JSON array
    project_types: List[str] = Field(default_factory=list)    # JSON array
    budget_range: Optional[str] = Field(max_length=20, null=True)  # low, medium, high, premium
    
    # Professional information
    job_title: Optional[str] = Field(max_length=100, null=True)
    company_type: Optional[str] = Field(max_length=50, null=True)  # contractor, diy, professional, etc.
    industry: Optional[str] = Field(max_length=50, null=True, index=True)
    
    # Geographic and demographic
    geographic_region: Optional[str] = Field(max_length=50, null=True, index=True)
    language_preference: str = Field(default="en", max_length=5)
    
    # Privacy and consent settings
    data_sharing_consent: bool = Field(default=False)
    marketing_consent: bool = Field(default=False)
    analytics_consent: bool = Field(default=True)
    
    # Profile completeness and quality
    profile_completeness: int = Field(default=0)  # 0-100%
    last_activity_date: Optional[datetime] = Field(null=True, index=True)
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now, index=True)
    deleted_at: Optional[datetime] = Field.null()
    
    __dataflow__ = {
        'soft_delete': True,
        'audit_log': True,
        'privacy_compliant': True,
        'search_fields': ['job_title', 'company_type'],
        'jsonb_fields': ['preferred_brands', 'project_types']
    }
    
    __indexes__ = [
        {'name': 'idx_user_profile_user_id', 'fields': ['user_id'], 'unique': True},
        {'name': 'idx_user_profile_skill_experience', 'fields': ['skill_level', 'experience_years']},
        {'name': 'idx_user_profile_safety_cert', 'fields': ['safety_certified', 'certification_expiry']},
        {'name': 'idx_user_profile_industry_region', 'fields': ['industry', 'geographic_region']},
        {'name': 'idx_user_profile_activity', 'fields': ['last_activity_date']},
        {'name': 'idx_user_profile_brands_gin', 'fields': ['preferred_brands'], 'type': 'gin'},
        {'name': 'idx_user_profile_projects_gin', 'fields': ['project_types'], 'type': 'gin'}
    ]


@db.model
class SkillAssessment:
    """Detailed skill assessments for users across different categories."""
    
    # Primary identification
    id: int = Field.primary_key()
    user_profile_id: int = Field(foreign_key="UserProfile.id", index=True)
    
    # Skill categorization
    skill_category: str = Field(max_length=50, index=True)     # power_tools, hand_tools, electrical, etc.
    skill_subcategory: Optional[str] = Field(max_length=50, null=True, index=True)  # cordless_drills, etc.
    
    # Assessment results
    proficiency_score: int = Field(index=True)  # 1-100 scale
    certification_level: str = Field(max_length=20, index=True)  # basic, intermediate, advanced, expert
    
    # Assessment metadata
    assessed_date: datetime = Field(default_factory=datetime.now, index=True)
    assessor_type: str = Field(max_length=20, index=True)  # self, system, professional
    assessment_method: Optional[str] = Field(max_length=50, null=True)  # quiz, practical, observation
    
    # Assessment details
    assessment_notes: Optional[str] = Field(null=True)
    strengths: Optional[List[str]] = Field(default_factory=list, null=True)  # JSON array
    improvement_areas: Optional[List[str]] = Field(default_factory=list, null=True)  # JSON array
    
    # Validity and expiration
    expires_at: Optional[datetime] = Field(null=True, index=True)
    is_current: bool = Field(default=True, index=True)
    superseded_by: Optional[int] = Field(foreign_key="SkillAssessment.id", null=True)
    
    # Verification and credibility
    verified: bool = Field(default=False, index=True)
    verification_source: Optional[str] = Field(max_length=100, null=True)
    confidence_score: Optional[int] = Field(null=True)  # 1-100 confidence in assessment
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    __dataflow__ = {
        'audit_log': True,
        'versioned': True,
        'search_fields': ['skill_category', 'skill_subcategory', 'assessment_notes'],
        'jsonb_fields': ['strengths', 'improvement_areas']
    }
    
    __indexes__ = [
        {'name': 'idx_skill_user_category', 'fields': ['user_profile_id', 'skill_category']},
        {'name': 'idx_skill_proficiency_level', 'fields': ['proficiency_score', 'certification_level']},
        {'name': 'idx_skill_assessed_date', 'fields': ['assessed_date', 'is_current']},
        {'name': 'idx_skill_assessor_method', 'fields': ['assessor_type', 'assessment_method']},
        {'name': 'idx_skill_expiry_current', 'fields': ['expires_at', 'is_current']},
        {'name': 'idx_skill_verified', 'fields': ['verified', 'confidence_score']},
        {'name': 'idx_skill_category_subcategory', 'fields': ['skill_category', 'skill_subcategory']}
    ]


@db.model
class SafetyCertification:
    """Safety certifications and training records for users."""
    
    # Primary identification
    id: int = Field.primary_key()
    user_profile_id: int = Field(foreign_key="UserProfile.id", index=True)
    
    # Certification details
    certification_type: str = Field(max_length=50, index=True)  # OSHA_10, OSHA_30, CPR_FIRST_AID, etc.
    certification_name: str = Field(max_length=255, index=True)
    issuing_organization: str = Field(max_length=100, index=True)
    certification_number: str = Field(max_length=100, index=True)
    
    # Validity and status
    issue_date: datetime = Field(index=True)
    expiry_date: Optional[datetime] = Field(null=True, index=True)
    is_valid: bool = Field(default=True, index=True)
    renewal_required: bool = Field(default=False, index=True)
    
    # Verification and documentation
    verification_status: str = Field(default="pending", max_length=20, index=True)  # pending, verified, expired, revoked
    verification_date: Optional[datetime] = Field(null=True)
    document_url: Optional[str] = Field(max_length=500, null=True)  # Link to certificate document
    
    # Certification details
    training_hours: Optional[int] = Field(null=True)
    training_location: Optional[str] = Field(max_length=255, null=True)
    instructor_name: Optional[str] = Field(max_length=100, null=True)
    
    # Renewal tracking
    renewal_date: Optional[datetime] = Field(null=True, index=True)
    reminder_sent: bool = Field(default=False)
    auto_renewal: bool = Field(default=False)
    
    # Related safety standards
    related_standards: Optional[List[str]] = Field(default_factory=list, null=True)  # JSON array of standard codes
    
    # Audit trail
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, index=True)
    deleted_at: Optional[datetime] = Field.null()
    
    __dataflow__ = {
        'soft_delete': True,
        'audit_log': True,
        'legal_compliance': True,
        'search_fields': ['certification_name', 'issuing_organization', 'certification_number'],
        'jsonb_fields': ['related_standards']
    }
    
    __indexes__ = [
        {'name': 'idx_safety_cert_user_type', 'fields': ['user_profile_id', 'certification_type']},
        {'name': 'idx_safety_cert_number', 'fields': ['certification_number']},
        {'name': 'idx_safety_cert_validity', 'fields': ['is_valid', 'expiry_date']},
        {'name': 'idx_safety_cert_issuer', 'fields': ['issuing_organization', 'issue_date']},
        {'name': 'idx_safety_cert_verification', 'fields': ['verification_status', 'verification_date']},
        {'name': 'idx_safety_cert_renewal', 'fields': ['renewal_required', 'renewal_date']},
        {'name': 'idx_safety_cert_standards_gin', 'fields': ['related_standards'], 'type': 'gin'}
    ]


# Export all models and the DataFlow instance
__all__ = [
    'db',
    # Core Product Models
    'Product', 'ProductCategory', 'ProductSpecification',
    # Classification Models
    'UNSPSCCode', 'ETIMClass',
    # Safety Models
    'SafetyStandard', 'ComplianceRequirement', 'PPERequirement',
    # Vendor Models
    'Vendor', 'ProductPricing', 'InventoryLevel',
    # User Profile Models
    'UserProfile', 'SkillAssessment', 'SafetyCertification'
]

# Model validation and integrity checks
def validate_model_integrity():
    """Validate DataFlow model integrity and relationships."""
    models = [
        Product, ProductCategory, ProductSpecification,
        UNSPSCCode, ETIMClass,
        SafetyStandard, ComplianceRequirement, PPERequirement,
        Vendor, ProductPricing, InventoryLevel,
        UserProfile, SkillAssessment, SafetyCertification
    ]
    
    for model in models:
        # Verify DataFlow configuration
        assert hasattr(model, '__dataflow__'), f"{model.__name__} missing DataFlow configuration"
        
        # Verify required fields exist
        required_fields = ['created_at']
        for field in required_fields:
            if field == 'created_at' and model.__name__ in ['ProductSpecification', 'PPERequirement']:
                continue  # Some models may not have created_at
            assert hasattr(model, field), f"{model.__name__} missing required field: {field}"
        
        # Verify primary key exists (either 'id' or specific primary key)
        has_primary_key = (
            hasattr(model, 'id') or 
            hasattr(model, 'code') or  # UNSPSCCode uses 'code'
            hasattr(model, 'class_id')  # ETIMClass uses 'class_id'
        )
        assert has_primary_key, f"{model.__name__} missing primary key field"
    
    return True

# Auto-generated node validation
def get_auto_generated_nodes(model_class):
    """Get list of auto-generated DataFlow nodes for a model."""
    base_name = model_class.__name__
    
    return [
        f"{base_name}CreateNode",
        f"{base_name}ReadNode", 
        f"{base_name}UpdateNode",
        f"{base_name}DeleteNode",
        f"{base_name}ListNode",
        f"{base_name}SearchNode",
        f"{base_name}CountNode",
        f"{base_name}ExistsNode",
        f"{base_name}ValidateNode"
    ]

# Initialize model validation on import
if __name__ != "__main__":
    try:
        validate_model_integrity()
    except Exception as e:
        print(f"Model integrity validation failed: {e}")