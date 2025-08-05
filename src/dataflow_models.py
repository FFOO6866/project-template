"""
DataFlow Models for AI-Powered Sales Assistant System
=====================================================

This module defines comprehensive DataFlow models for:
- Customer and company management
- Quote generation with line items
- Document storage and metadata
- User management with roles
- ERP integration data structures
- Multi-tenant support
- Audit trails and history tracking
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataflow import DataFlow
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

import os

# Initialize DataFlow with environment-based configuration
# DataFlow alpha only supports PostgreSQL
db_url = os.getenv(
    "DATABASE_URL", 
    "postgresql://horme_user:horme_password@localhost:5432/horme_classification_db"  # Default to PostgreSQL (DataFlow alpha requirement)
)

# Initialize DataFlow with enterprise features
db = DataFlow(
    database_url=db_url,
    pool_size=10 if "sqlite" in db_url else 20,
    pool_max_overflow=20 if "sqlite" in db_url else 30,
    pool_recycle=3600,
    monitoring=True,
    echo=False,  # Set to True for development
    auto_migrate=True
)

# ==============================================================================
# COMPANY & TENANT MANAGEMENT
# ==============================================================================

@db.model
class Company:
    """Company/Tenant model for multi-tenant support"""
    name: str
    domain: str
    industry: str
    address: str
    phone: str
    email: str
    logo_url: Optional[str] = None
    settings: Optional[dict] = None  # Company-specific settings
    erp_config: Optional[dict] = None  # ERP integration configuration
    active: bool = True
    
    __dataflow__ = {
        'soft_delete': True,
        'audit_log': True,
        'versioned': True
    }
    
    __indexes__ = [
        {'name': 'idx_company_domain', 'fields': ['domain'], 'unique': True},
        {'name': 'idx_company_active', 'fields': ['active']},
        {'name': 'idx_company_industry', 'fields': ['industry']}
    ]

# ==============================================================================
# USER MANAGEMENT WITH ROLES
# ==============================================================================

@db.model
class User:
    """User model with role-based access control"""
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    role: str  # admin, sales_manager, sales_rep, viewer
    department: str
    company_id: int
    is_active: bool = True
    last_login: Optional[datetime] = None
    preferences: Optional[dict] = None
    
    __dataflow__ = {
        'multi_tenant': True,  # Uses company_id for tenant isolation
        'soft_delete': True,
        'audit_log': True,
        'versioned': True
    }
    
    __indexes__ = [
        {'name': 'idx_user_email', 'fields': ['email'], 'unique': True},
        {'name': 'idx_user_company_role', 'fields': ['company_id', 'role']},
        {'name': 'idx_user_active', 'fields': ['is_active']},
        {'name': 'idx_user_department', 'fields': ['department']}
    ]

@db.model
class UserSession:
    """User session tracking for security and analytics"""
    user_id: int
    session_token: str
    ip_address: str
    user_agent: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True
    
    __dataflow__ = {
        'multi_tenant': True,
        'ttl': 86400  # 24 hour TTL for automatic cleanup
    }
    
    __indexes__ = [
        {'name': 'idx_session_token', 'fields': ['session_token'], 'unique': True},
        {'name': 'idx_session_user', 'fields': ['user_id', 'is_active']},
        {'name': 'idx_session_expires', 'fields': ['expires_at']}
    ]

# ==============================================================================
# CUSTOMER MANAGEMENT
# ==============================================================================

@db.model
class Customer:
    """Customer master data with comprehensive information"""
    name: str
    type: str  # individual, business, enterprise
    industry: Optional[str] = None
    company_size: Optional[str] = None  # small, medium, large, enterprise
    
    # Contact Information
    primary_contact: str
    email: str
    phone: str
    website: Optional[str] = None
    
    # Address Information
    billing_address: dict  # JSON structure with address components
    shipping_address: Optional[dict] = None
    
    # Business Information
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    credit_limit: Optional[float] = None
    currency: str = "USD"
    
    # CRM Fields
    lead_source: Optional[str] = None
    assigned_sales_rep: Optional[int] = None  # User ID
    status: str = "active"  # active, inactive, prospect, qualified
    priority: str = "medium"  # low, medium, high, critical
    
    # Analytics
    lifetime_value: Optional[float] = None
    last_order_date: Optional[datetime] = None
    total_orders: int = 0
    
    # Custom Fields
    custom_fields: Optional[dict] = None
    notes: Optional[str] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True
    }
    
    __indexes__ = [
        {'name': 'idx_customer_email', 'fields': ['email']},
        {'name': 'idx_customer_industry', 'fields': ['industry']},
        {'name': 'idx_customer_status', 'fields': ['status']},
        {'name': 'idx_customer_sales_rep', 'fields': ['assigned_sales_rep']},
        {'name': 'idx_customer_priority', 'fields': ['priority']},
        {'name': 'idx_customer_name_text', 'fields': ['name'], 'type': 'text'}
    ]

# ==============================================================================
# DOCUMENT MANAGEMENT
# ==============================================================================

@db.model
class Document:
    """Document storage with metadata and AI processing status"""
    name: str
    type: str  # rfp, quote, order, contract, specification
    category: str  # inbound, outbound, internal
    file_path: str  # Storage path or URL
    file_size: int
    mime_type: str
    
    # Document Relationships
    customer_id: Optional[int] = None
    quote_id: Optional[int] = None
    parent_document_id: Optional[int] = None
    
    # Processing Status
    ai_status: str = "pending"  # pending, processing, completed, failed
    ai_extracted_data: Optional[dict] = None
    ai_confidence_score: Optional[float] = None
    
    # Document Metadata
    upload_date: datetime
    uploaded_by: int  # User ID
    version: int = 1
    is_latest_version: bool = True
    
    # Content Analysis
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    key_terms: Optional[list] = None
    summary: Optional[str] = None
    
    # Security and Access
    security_level: str = "internal"  # public, internal, confidential, restricted
    access_permissions: Optional[dict] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        'encryption': {
            'fields': ['ai_extracted_data'],
            'key_rotation': True
        }
    }
    
    __indexes__ = [
        {'name': 'idx_document_type_category', 'fields': ['type', 'category']},
        {'name': 'idx_document_customer', 'fields': ['customer_id']},
        {'name': 'idx_document_quote', 'fields': ['quote_id']},
        {'name': 'idx_document_ai_status', 'fields': ['ai_status']},
        {'name': 'idx_document_upload_date', 'fields': ['upload_date']},
        {'name': 'idx_document_name_text', 'fields': ['name'], 'type': 'text'},
        {'name': 'idx_document_latest_version', 'fields': ['is_latest_version']}
    ]

@db.model
class DocumentProcessingQueue:
    """Queue for AI document processing tasks"""
    document_id: int
    processing_type: str  # extract, analyze, summarize, classify
    priority: int = 5  # 1-10, lower is higher priority
    status: str = "queued"  # queued, processing, completed, failed, retrying
    
    # Processing Configuration
    ai_model: str
    processing_config: Optional[dict] = None
    
    # Timing and Retry Logic
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Results
    result_data: Optional[dict] = None
    error_message: Optional[str] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'ttl': 604800  # 7 days TTL for cleanup
    }
    
    __indexes__ = [
        {'name': 'idx_queue_status_priority', 'fields': ['status', 'priority']},
        {'name': 'idx_queue_document', 'fields': ['document_id']},
        {'name': 'idx_queue_queued_at', 'fields': ['queued_at']}
    ]

# ==============================================================================
# QUOTE GENERATION SYSTEM
# ==============================================================================

@db.model
class Quote:
    """Quote master record with comprehensive quote information"""
    quote_number: str  # Auto-generated unique identifier
    customer_id: int
    
    # Quote Details
    title: str
    description: Optional[str] = None
    status: str = "draft"  # draft, sent, accepted, rejected, expired, revised
    
    # Financial Information
    subtotal: float = 0.0
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    total_amount: float = 0.0
    currency: str = "USD"
    
    # Dates and Validity
    created_date: datetime
    sent_date: Optional[datetime] = None
    expiry_date: datetime
    response_date: Optional[datetime] = None
    
    # Sales Information
    created_by: int  # User ID
    assigned_to: Optional[int] = None  # User ID
    probability: Optional[float] = None  # Win probability percentage
    
    # Quote Configuration
    terms_and_conditions: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    special_instructions: Optional[str] = None
    
    # Revision Tracking
    version: int = 1
    parent_quote_id: Optional[int] = None
    revision_reason: Optional[str] = None
    
    # Integration
    erp_quote_id: Optional[str] = None
    sync_status: str = "pending"  # pending, synced, failed
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True
    }
    
    __indexes__ = [
        {'name': 'idx_quote_number', 'fields': ['quote_number'], 'unique': True},
        {'name': 'idx_quote_customer', 'fields': ['customer_id']},
        {'name': 'idx_quote_status', 'fields': ['status']},
        {'name': 'idx_quote_created_by', 'fields': ['created_by']},
        {'name': 'idx_quote_expiry_date', 'fields': ['expiry_date']},
        {'name': 'idx_quote_created_date', 'fields': ['created_date']},
        {'name': 'idx_quote_erp_sync', 'fields': ['sync_status']}
    ]

@db.model
class QuoteLineItem:
    """Individual line items within a quote"""
    quote_id: int
    line_number: int  # Position within the quote
    
    # Product Information
    product_code: Optional[str] = None
    product_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    
    # Pricing and Quantities
    quantity: float
    unit_of_measure: str = "each"
    unit_price: float
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    line_total: float
    
    # Product Details
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    specifications: Optional[dict] = None
    
    # Delivery and Lead Time
    lead_time_days: Optional[int] = None
    availability_status: Optional[str] = None
    
    # ERP Integration
    erp_product_id: Optional[str] = None
    cost_basis: Optional[float] = None  # For margin calculation
    margin_percent: Optional[float] = None
    
    # Configuration
    is_optional: bool = False
    is_alternative: bool = False
    parent_line_id: Optional[int] = None  # For alternative items
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True
    }
    
    __indexes__ = [
        {'name': 'idx_line_item_quote', 'fields': ['quote_id', 'line_number']},
        {'name': 'idx_line_item_product_code', 'fields': ['product_code']},
        {'name': 'idx_line_item_category', 'fields': ['category']},
        {'name': 'idx_line_item_manufacturer', 'fields': ['manufacturer']}
    ]

@db.model
class QuoteTemplate:
    """Reusable quote templates for common product configurations"""
    name: str
    description: Optional[str] = None
    category: str
    industry: Optional[str] = None
    
    # Template Configuration
    template_data: dict  # JSON structure with line items and settings
    default_terms: Optional[str] = None
    default_validity_days: int = 30
    
    # Usage and Analytics
    usage_count: int = 0
    created_by: int
    last_used_date: Optional[datetime] = None
    
    # Access Control
    is_public: bool = False
    allowed_users: Optional[list] = None
    allowed_roles: Optional[list] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True
    }
    
    __indexes__ = [
        {'name': 'idx_template_category', 'fields': ['category']},
        {'name': 'idx_template_industry', 'fields': ['industry']},
        {'name': 'idx_template_public', 'fields': ['is_public']},
        {'name': 'idx_template_usage', 'fields': ['usage_count']}
    ]

# ==============================================================================
# ERP INTEGRATION MODELS
# ==============================================================================

@db.model
class ERPProduct:
    """Product master data synchronized from ERP systems"""
    erp_product_id: str
    product_code: str
    name: str
    description: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    
    # Pricing Information
    list_price: float
    cost_price: Optional[float] = None
    currency: str = "USD"
    price_updated_at: datetime
    
    # Availability
    stock_quantity: Optional[float] = None
    available_quantity: Optional[float] = None
    lead_time_days: Optional[int] = None
    stock_status: str = "available"  # available, limited, out_of_stock, discontinued
    
    # Product Details
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    specifications: Optional[dict] = None
    weight: Optional[float] = None
    dimensions: Optional[dict] = None
    
    # ERP Sync Information
    erp_system: str  # SAP, Oracle, NetSuite, etc.
    last_sync_date: datetime
    sync_status: str = "active"  # active, inactive, error
    
    # Product Classification
    product_family: Optional[str] = None
    product_line: Optional[str] = None
    is_configured: bool = False  # Requires configuration
    is_service: bool = False
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True
    }
    
    __indexes__ = [
        {'name': 'idx_erp_product_id', 'fields': ['erp_product_id'], 'unique': True},
        {'name': 'idx_erp_product_code', 'fields': ['product_code']},
        {'name': 'idx_erp_category', 'fields': ['category', 'subcategory']},
        {'name': 'idx_erp_manufacturer', 'fields': ['manufacturer']},
        {'name': 'idx_erp_stock_status', 'fields': ['stock_status']},
        {'name': 'idx_erp_sync_date', 'fields': ['last_sync_date']},
        {'name': 'idx_erp_name_text', 'fields': ['name'], 'type': 'text'}
    ]

@db.model
class ERPSyncLog:
    """Log of ERP synchronization activities"""
    sync_type: str  # products, customers, orders, pricing
    sync_direction: str  # inbound, outbound, bidirectional
    entity_type: str  # product, customer, quote, order
    entity_id: Optional[str] = None
    
    # Sync Details
    erp_system: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, partial
    
    # Results
    records_processed: int = 0
    records_successful: int = 0
    records_failed: int = 0
    error_details: Optional[dict] = None
    
    # Configuration
    sync_config: Optional[dict] = None
    batch_size: Optional[int] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'ttl': 2592000  # 30 days TTL
    }
    
    __indexes__ = [
        {'name': 'idx_sync_log_type_date', 'fields': ['sync_type', 'started_at']},
        {'name': 'idx_sync_log_status', 'fields': ['status']},
        {'name': 'idx_sync_log_erp_system', 'fields': ['erp_system']},
        {'name': 'idx_sync_log_entity', 'fields': ['entity_type', 'entity_id']}
    ]

# ==============================================================================
# AUDIT TRAIL AND HISTORY TRACKING
# ==============================================================================

@db.model
class ActivityLog:
    """Comprehensive activity logging for audit trails"""
    entity_type: str  # quote, customer, document, user
    entity_id: str
    action: str  # create, update, delete, view, send, approve
    
    # User Information
    user_id: int
    user_name: str
    user_role: str
    
    # Change Details
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    change_summary: Optional[str] = None
    
    # Context Information
    ip_address: str
    user_agent: str
    session_id: Optional[str] = None
    
    # Timing
    timestamp: datetime
    
    # Additional Metadata
    metadata: Optional[dict] = None
    risk_level: str = "low"  # low, medium, high, critical
    
    __dataflow__ = {
        'multi_tenant': True,
        'ttl': 7776000  # 90 days TTL for compliance
    }
    
    __indexes__ = [
        {'name': 'idx_activity_entity', 'fields': ['entity_type', 'entity_id']},
        {'name': 'idx_activity_user', 'fields': ['user_id', 'timestamp']},
        {'name': 'idx_activity_action', 'fields': ['action']},
        {'name': 'idx_activity_timestamp', 'fields': ['timestamp']},
        {'name': 'idx_activity_risk', 'fields': ['risk_level']}
    ]

@db.model
class BusinessMetrics:
    """Business intelligence and KPI tracking"""
    metric_name: str
    metric_category: str  # sales, customer, product, efficiency
    metric_value: float
    metric_unit: str  # currency, percentage, count, time
    
    # Time Dimensions
    period_type: str  # daily, weekly, monthly, quarterly, yearly
    period_start: datetime
    period_end: datetime
    
    # Dimensions
    user_id: Optional[int] = None
    customer_id: Optional[int] = None
    product_category: Optional[str] = None
    region: Optional[str] = None
    
    # Metadata
    calculation_method: Optional[str] = None
    data_sources: Optional[list] = None
    confidence_level: Optional[float] = None
    
    # Comparison Data
    previous_period_value: Optional[float] = None
    target_value: Optional[float] = None
    variance_percent: Optional[float] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'ttl': 31536000  # 1 year TTL
    }
    
    __indexes__ = [
        {'name': 'idx_metrics_name_period', 'fields': ['metric_name', 'period_start']},
        {'name': 'idx_metrics_category', 'fields': ['metric_category']},
        {'name': 'idx_metrics_user', 'fields': ['user_id', 'period_start']},
        {'name': 'idx_metrics_customer', 'fields': ['customer_id', 'period_start']}
    ]

# ==============================================================================
# CONFIGURATION AND SETTINGS
# ==============================================================================

@db.model
class SystemConfiguration:
    """System-wide configuration settings"""
    config_key: str
    config_value: str
    config_type: str  # string, integer, float, boolean, json
    category: str  # system, email, ai, erp, security
    
    # Metadata
    description: Optional[str] = None
    is_sensitive: bool = False
    is_user_configurable: bool = True
    requires_restart: bool = False
    
    # Validation
    validation_rules: Optional[dict] = None
    default_value: Optional[str] = None
    
    # Change Tracking
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'audit_log': True,
        'encryption': {
            'fields': ['config_value'],
            'condition': 'is_sensitive = true'
        }
    }
    
    __indexes__ = [
        {'name': 'idx_config_key', 'fields': ['config_key'], 'unique': True},
        {'name': 'idx_config_category', 'fields': ['category']},
        {'name': 'idx_config_user_configurable', 'fields': ['is_user_configurable']}
    ]

# ==============================================================================
# WORKFLOW STATE MANAGEMENT
# ==============================================================================

@db.model
class WorkflowState:
    """Track workflow execution states for complex business processes"""
    workflow_id: str
    workflow_type: str  # quote_generation, document_processing, erp_sync
    entity_id: str  # Related entity ID (quote_id, document_id, etc.)
    
    # State Information
    current_state: str
    previous_state: Optional[str] = None
    next_possible_states: Optional[list] = None
    
    # Execution Context
    context_data: Optional[dict] = None
    error_state: Optional[dict] = None
    retry_count: int = 0
    
    # Timing
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    # Assignment
    assigned_user: Optional[int] = None
    assigned_role: Optional[str] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'ttl': 2592000  # 30 days TTL
    }
    
    __indexes__ = [
        {'name': 'idx_workflow_id', 'fields': ['workflow_id']},
        {'name': 'idx_workflow_type_state', 'fields': ['workflow_type', 'current_state']},
        {'name': 'idx_workflow_entity', 'fields': ['entity_id']},
        {'name': 'idx_workflow_assigned', 'fields': ['assigned_user']}
    ]

# Export the DataFlow instance for use in other modules
__all__ = [
    'db',
    'Company', 'User', 'UserSession',
    'Customer', 'Document', 'DocumentProcessingQueue',
    'Quote', 'QuoteLineItem', 'QuoteTemplate',
    'ERPProduct', 'ERPSyncLog',
    'ActivityLog', 'BusinessMetrics',
    'SystemConfiguration', 'WorkflowState'
]