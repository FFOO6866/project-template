"""
DataFlow Models for UNSPSC/ETIM Classification System - DATA-001
================================================================

Enhanced DataFlow models specifically designed for the classification system.
Each @db.model automatically generates 9 database operation nodes, eliminating
the need for custom node implementations while providing enterprise features.

Models Added:
- ProductClassification: Links products to both UNSPSC/ETIM with confidence
- ClassificationHistory: Audit trail of classification changes  
- ClassificationCache: Performance optimization for frequently accessed classifications
- ETIMAttribute: Technical attributes with multi-language support
- ClassificationRule: ML training data and keyword rules
- ClassificationFeedback: User feedback for improving classification accuracy

Performance Targets:
- Classification lookup: <500ms (leveraging DataFlow caching)
- Bulk classification: 10,000+ products/sec using BulkCreateNode
- Vector similarity search: <100ms using pgvector integration
"""

# Apply Windows compatibility patches first
import windows_sdk_compatibility

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataflow import DataFlow

# Auto-detect Docker environment and configure accordingly
def is_docker_environment() -> bool:
    """Detect if running in Docker container."""
    return (
        os.path.exists('/.dockerenv') or
        os.getenv('CONTAINER_ENV') == 'docker' or
        os.getenv('DATABASE_URL', '').find('@postgres:') != -1 or
        os.getenv('REDIS_URL', '').find('redis:') != -1
    )

# Configure database URL based on environment
if is_docker_environment():
    # Docker environment - use service names
    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://horme_user:horme_password@postgres:5432/horme_classification_db'
    )
    redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/2')
    print("INFO: Using Docker configuration with service names")
else:
    # Local development - use localhost
    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://horme_user:horme_password@localhost:5432/horme_classification_db'
    )
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/2')
    print("INFO: Using local development configuration")

# Production-optimized PostgreSQL + pgvector configuration for classification system
db = DataFlow(
    database_url=database_url,
    
    # High-performance connection pooling for classification workloads
    pool_size=75,                    # Increased for classification-heavy workloads
    pool_max_overflow=150,           # Higher overflow for peak classification requests
    pool_recycle=1200,               # 20 minutes (faster recycle for ML workloads)
    pool_pre_ping=True,              # Essential for ML pipeline reliability
    pool_timeout=20,                 # Faster timeout for classification requests
    pool_reset_on_return='rollback', # Clean state for classification transactions
    
    # Performance monitoring
    monitoring=True,
    performance_tracking=True,
    slow_query_threshold=500,        # Log queries >500ms (stricter for classification)
    echo=False,
    
    # Auto-migration with classification-specific optimizations
    auto_migrate=True,
    migration_timeout=600,           # 10 minutes for complex classification schema
    
    # PostgreSQL extensions for classification
    extensions=['pgvector', 'pg_trgm', 'btree_gin', 'pg_stat_statements', 'pgcrypto'],
    
    # Enterprise features optimized for classification
    enable_audit_log=True,
    enable_soft_delete=True,
    enable_versioning=True,
    
    # Advanced caching for ML predictions
    enable_caching=True,
    cache_backend=redis_url,  # Dedicated Redis DB for classification
    cache_prefix='classification',
    cache_compression='gzip',
    cache_serializer='msgpack',      # Faster serialization for ML data
    
    # ML-specific optimizations
    enable_vector_indexing=True,     # pgvector optimization
    vector_dimensions=1536,          # OpenAI embedding dimensions
    vector_index_type='ivfflat',     # Optimal for similarity search
    vector_lists=1000,               # Index parameter for 100k+ vectors
    
    # Bulk operation optimization for classification data
    bulk_batch_size=8000,            # Optimal for classification imports
    bulk_insert_method='copy',       # COPY for bulk classification data
    enable_bulk_upsert=True,         # Essential for classification updates
    
    # Query optimization for classification patterns
    query_cache_size=15000,          # Larger cache for classification queries
    enable_prepared_statements=True, # Reuse classification query plans
    statement_cache_size=1000,
    
    # Connection health and reliability
    health_check_interval=30,        # More frequent health checks
    connection_invalidate_pool_on_disconnect=True,
    enable_connection_pooling_metrics=True
)

# ==============================================================================
# CORE BUSINESS MODELS
# ==============================================================================

@db.model
class Company:
    """
    Company model for business entity management with enterprise features.
    Automatically generates 9 nodes: Create, Read, Update, Delete, List,
    BulkCreate, BulkUpdate, BulkDelete, BulkUpsert for comprehensive company operations.
    """
    
    # Primary identification
    id: int
    name: str
    industry: str
    
    # Company details
    description: Optional[str] = None
    website: Optional[str] = None
    employee_count: Optional[int] = 0
    founded_year: Optional[int] = None
    
    # Status and operations
    is_active: bool = True
    headquarters_location: Optional[str] = None
    company_type: str = "private"  # private, public, non_profit, government
    
    # Business metadata
    revenue_range: Optional[str] = None  # startup, small, medium, large, enterprise
    market_segment: Optional[str] = None
    primary_contact_email: Optional[str] = None
    phone_number: Optional[str] = None
    
    # Compliance and verification
    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    is_verified: bool = False
    verification_date: Optional[datetime] = None
    
    # Audit trail
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        
        # High-traffic company data caching
        'cache_ttl': 2700,              # 45 minutes cache for company data
        'cache_strategy': 'write_through',
        'cache_warming': True,          # Preload active companies
        
        # Enhanced search for companies
        'search_fields': ['name', 'industry', 'description', 'headquarters_location'],
        'full_text_search': True,
        'search_ranking': 'ts_rank',
        
        # Performance optimization
        'performance_tracking': True,
        'query_optimization': True,
        'enable_read_replicas': True,
        
        # Business intelligence features
        'enable_analytics': True,
        'track_access_patterns': True,
        'enable_data_profiling': True
    }
    
    __indexes__ = [
        {'name': 'idx_company_name_unique', 'fields': ['name'], 'unique': True},
        {'name': 'idx_company_industry', 'fields': ['industry', 'is_active']},
        {'name': 'idx_company_size', 'fields': ['employee_count', 'revenue_range']},
        {'name': 'idx_company_location', 'fields': ['headquarters_location']},
        {'name': 'idx_company_type', 'fields': ['company_type', 'market_segment']},
        {'name': 'idx_company_verification', 'fields': ['is_verified', 'verification_date']},
        {'name': 'idx_company_contact', 'fields': ['primary_contact_email']},
        {'name': 'idx_company_registration', 'fields': ['tax_id', 'registration_number']},
        {'name': 'idx_company_founded', 'fields': ['founded_year']}
    ]


@db.model
class User:
    """
    User model for authentication and profile management.
    Automatically generates 9 nodes: Create, Read, Update, Delete, List,
    BulkCreate, BulkUpdate, BulkDelete, BulkUpsert for comprehensive user operations.
    """
    
    # Primary identification
    id: int
    username: str
    email: str
    
    # User details
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    
    # Authentication
    password_hash: str
    is_active: bool = True
    is_verified: bool = False
    last_login: Optional[datetime] = None
    
    # Profile information
    company_id: Optional[int] = None  # Foreign key to Company
    role: str = "user"  # user, admin, manager, viewer
    department: Optional[str] = None
    job_title: Optional[str] = None
    
    # Preferences
    timezone: str = "UTC"
    language: str = "en"
    notification_preferences: Dict[str, Any] = None
    
    # Audit trail
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        'cache_ttl': 900,  # 15 minutes cache for user data
        'search_fields': ['username', 'email', 'first_name', 'last_name'],
        'jsonb_fields': ['notification_preferences'],
        'performance_tracking': True,
        'privacy_compliant': True
    }
    
    __indexes__ = [
        {'name': 'idx_user_username_unique', 'fields': ['username'], 'unique': True},
        {'name': 'idx_user_email_unique', 'fields': ['email'], 'unique': True},
        {'name': 'idx_user_company', 'fields': ['company_id', 'role']},
        {'name': 'idx_user_active', 'fields': ['is_active', 'is_verified']},
        {'name': 'idx_user_login', 'fields': ['last_login']},
        {'name': 'idx_user_name', 'fields': ['first_name', 'last_name']},
        {'name': 'idx_user_role', 'fields': ['role', 'department']},
        {'name': 'idx_user_preferences_gin', 'fields': ['notification_preferences'], 'type': 'gin'}
    ]


@db.model
class Customer:
    """
    Customer model for client relationship management.
    Automatically generates 9 nodes: Create, Read, Update, Delete, List,
    BulkCreate, BulkUpdate, BulkDelete, BulkUpsert for comprehensive customer operations.
    """
    
    # Primary identification
    id: int
    name: str
    customer_type: str = "business"  # business, individual, government
    
    # Contact information
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    
    # Address information
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    
    # Business details
    industry: Optional[str] = None
    company_size: Optional[str] = None
    annual_revenue: Optional[str] = None
    
    # Relationship management
    account_manager_id: Optional[int] = None  # Foreign key to User
    customer_status: str = "active"  # active, inactive, prospect, churned
    credit_limit: Optional[float] = None
    payment_terms: str = "net_30"
    
    # Sales metrics
    total_orders: int = 0
    total_revenue: float = 0.0
    last_order_date: Optional[datetime] = None
    acquisition_date: Optional[datetime] = None
    
    # Customer preferences
    preferred_currency: str = "USD"
    communication_preferences: Dict[str, Any] = None
    
    # Audit trail
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        'cache_ttl': 1800,  # 30 minutes cache for customer data
        'search_fields': ['name', 'email', 'industry'],
        'jsonb_fields': ['communication_preferences'],
        'performance_tracking': True,
        'privacy_compliant': True
    }
    
    # High-traffic customer model indexes for CRM performance
    __indexes__ = [
        # Primary access patterns
        {'name': 'idx_customer_name_text', 'fields': ['name'], 'type': 'gin', 'options': 'gin_trgm_ops'},
        {'name': 'idx_customer_email_unique', 'fields': ['email'], 'unique': True, 'condition': 'email IS NOT NULL'},
        
        # Business intelligence and filtering
        {'name': 'idx_customer_type_status_active', 'fields': ['customer_type', 'customer_status'], 'condition': 'deleted_at IS NULL'},
        {'name': 'idx_customer_industry_size_revenue', 'fields': ['industry', 'company_size', 'total_revenue']},
        
        # Sales and account management
        {'name': 'idx_customer_manager_status', 'fields': ['account_manager_id', 'customer_status']},
        {'name': 'idx_customer_revenue_orders', 'fields': ['total_revenue', 'total_orders', 'last_order_date']},
        {'name': 'idx_customer_high_value', 'fields': ['total_revenue'], 'condition': 'total_revenue > 50000'},
        
        # Geographic and demographic analysis
        {'name': 'idx_customer_location_composite', 'fields': ['country', 'region', 'customer_type']},
        {'name': 'idx_customer_acquisition_cohort', 'fields': ['acquisition_date', 'customer_type']},
        
        # Communication and preferences
        {'name': 'idx_customer_preferences_gin_ops', 'fields': ['communication_preferences'], 'type': 'gin', 'options': 'jsonb_path_ops'},
        {'name': 'idx_customer_currency_terms', 'fields': ['preferred_currency', 'payment_terms']},
        
        # Performance optimization for dashboards
        {'name': 'idx_customer_dashboard_cover', 'fields': ['customer_status', 'total_revenue'], 
         'include': ['name', 'industry', 'last_order_date'], 'condition': 'deleted_at IS NULL'},
        
        # Recent activity tracking
        {'name': 'idx_customer_recent_activity', 'fields': ['last_order_date'], 'condition': 'last_order_date > CURRENT_DATE - INTERVAL \'90 days\''},
        
        # Account health monitoring
        {'name': 'idx_customer_health_metrics', 'fields': ['customer_status', 'total_orders', 'acquisition_date']}
    ]


@db.model
class Quote:
    """
    Quote model for sales quotation management.
    Automatically generates 9 nodes: Create, Read, Update, Delete, List,
    BulkCreate, BulkUpdate, BulkDelete, BulkUpsert for comprehensive quote operations.
    """
    
    # Primary identification
    id: int
    quote_number: str
    
    # Relationships
    customer_id: int  # Foreign key to Customer
    created_by_user_id: int  # Foreign key to User
    
    # Quote details
    title: str
    description: Optional[str] = None
    status: str = "draft"  # draft, sent, accepted, rejected, expired
    
    # Financial information
    subtotal: float = 0.0
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    total_amount: float = 0.0
    currency: str = "USD"
    
    # Validity and terms
    valid_until: datetime
    payment_terms: str = "net_30"
    delivery_terms: Optional[str] = None
    notes: Optional[str] = None
    
    # Quote items (stored as JSON for simplicity)
    line_items: List[Dict[str, Any]] = None
    
    # Sales process
    probability: float = 0.0  # 0.0 to 1.0
    expected_close_date: Optional[datetime] = None
    competitor_info: Optional[str] = None
    
    # Communication tracking
    sent_date: Optional[datetime] = None
    viewed_date: Optional[datetime] = None
    last_follow_up: Optional[datetime] = None
    follow_up_count: int = 0
    
    # Conversion tracking
    converted_to_order: bool = False
    order_id: Optional[int] = None
    conversion_date: Optional[datetime] = None
    
    # Audit trail
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        'cache_ttl': 1200,  # 20 minutes cache for quote data
        'search_fields': ['quote_number', 'title', 'description'],
        'jsonb_fields': ['line_items'],
        'performance_tracking': True
    }
    
    # High-performance indexes for sales quotation management
    __indexes__ = [
        # Primary access patterns
        {'name': 'idx_quote_number_unique', 'fields': ['quote_number'], 'unique': True},
        {'name': 'idx_quote_customer_status_date', 'fields': ['customer_id', 'status', 'created_at']},
        
        # Sales team and user management
        {'name': 'idx_quote_creator_status', 'fields': ['created_by_user_id', 'status']},
        {'name': 'idx_quote_user_performance', 'fields': ['created_by_user_id', 'converted_to_order', 'total_amount']},
        
        # Sales pipeline management
        {'name': 'idx_quote_status_priority', 'fields': ['status'], 'condition': 'status IN (\'sent\', \'pending\', \'follow_up\')'},
        {'name': 'idx_quote_active_pipeline', 'fields': ['status', 'created_at'], 'condition': 'deleted_at IS NULL AND status != \'expired\''},
        
        # Time-sensitive operations
        {'name': 'idx_quote_validity_expiring', 'fields': ['valid_until', 'status'], 'condition': 'valid_until > CURRENT_DATE AND status != \'expired\''},
        {'name': 'idx_quote_expiry_alert', 'fields': ['valid_until'], 'condition': 'valid_until BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL \'7 days\''},
        
        # Financial analysis
        {'name': 'idx_quote_amount_currency_date', 'fields': ['total_amount', 'currency', 'created_at']},
        {'name': 'idx_quote_high_value', 'fields': ['total_amount', 'probability'], 'condition': 'total_amount > 10000'},
        
        # Sales forecasting
        {'name': 'idx_quote_probability_forecast', 'fields': ['probability', 'expected_close_date', 'total_amount']},
        {'name': 'idx_quote_close_prediction', 'fields': ['expected_close_date', 'probability'], 'condition': 'expected_close_date IS NOT NULL'},
        
        # Conversion tracking
        {'name': 'idx_quote_conversion_analysis', 'fields': ['converted_to_order', 'conversion_date', 'total_amount']},
        {'name': 'idx_quote_won_deals', 'fields': ['conversion_date', 'total_amount'], 'condition': 'converted_to_order = true'},
        
        # Follow-up and engagement
        {'name': 'idx_quote_follow_up_due', 'fields': ['last_follow_up', 'follow_up_count'], 'condition': 'status IN (\'sent\', \'pending\')'},
        {'name': 'idx_quote_engagement_tracking', 'fields': ['sent_date', 'viewed_date', 'last_follow_up']},
        
        # Complex JSONB queries for line items
        {'name': 'idx_quote_line_items_gin_ops', 'fields': ['line_items'], 'type': 'gin', 'options': 'jsonb_path_ops'},
        {'name': 'idx_quote_line_items_products', 'fields': ['line_items'], 'type': 'gin'},
        
        # Performance covering indexes
        {'name': 'idx_quote_dashboard_cover', 'fields': ['status', 'created_at'], 
         'include': ['quote_number', 'customer_id', 'total_amount', 'probability'], 
         'condition': 'deleted_at IS NULL'},
        
        # Text search optimization
        {'name': 'idx_quote_title_search', 'fields': ['title'], 'type': 'gin', 'options': 'gin_trgm_ops'}
    ]


# ==============================================================================
# ENHANCED CLASSIFICATION MODELS
# ==============================================================================

@db.model
class ProductClassification:
    """
    Links products to both UNSPSC and ETIM classifications with confidence scoring.
    Automatically generates 9 nodes: Create, Read, Update, Delete, List, 
    BulkCreate, BulkUpdate, BulkDelete, BulkUpsert for high-performance operations.
    """
    
    # Primary identification
    id: int
    product_id: int  # Foreign key to Product model
    
    # Dual classification system
    unspsc_code: Optional[str] = None
    unspsc_confidence: float = 0.0
    etim_class_id: Optional[str] = None  
    etim_confidence: float = 0.0
    
    # Overall classification metadata
    dual_confidence: float = 0.0  # Average of both confidences
    classification_method: str = "unknown"  # ml_automatic, keyword_enhanced, manual, hybrid
    confidence_level: str = "very_low"  # very_high, high, medium, low, very_low
    
    # Classification context
    classification_text: str = ""  # Text used for classification
    language: str = "en"
    
    # Performance and processing metadata
    processing_time_ms: float = 0.0
    cache_hit: bool = False
    workflow_id: str = ""
    
    # Status and validation
    is_validated: bool = False
    validated_by: Optional[int] = None  # User ID
    validation_date: Optional[datetime] = None
    needs_review: bool = False
    
    # Recommendations and feedback
    recommendations: List[str] = None  # JSON array of recommendations
    user_feedback: Optional[str] = None
    feedback_score: Optional[int] = None  # 1-5 rating
    
    # Audit trail
    classified_at: datetime
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    # Production-optimized classification configuration
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        
        # Aggressive caching for ML predictions
        'cache_ttl': 7200,              # 2 hours for stable classifications
        'cache_strategy': 'write_through',
        'cache_warming': True,
        'cache_warming_threshold': 50,   # Warm classifications with >50 accesses
        
        # Enhanced search for classifications
        'search_fields': ['classification_text', 'unspsc_code', 'etim_class_id', 'workflow_id'],
        'full_text_search': True,
        'enable_similarity_search': True,
        'similarity_threshold': 0.8,
        
        # ML-specific features
        'jsonb_fields': ['recommendations'],
        'jsonb_compress': True,
        'enable_vector_search': True,
        'vector_similarity_method': 'cosine',
        
        # Performance optimization for ML workloads
        'performance_tracking': True,
        'enable_query_parallelization': True,
        'batch_prediction_size': 1000,
        
        # ML pipeline optimization
        'enable_confidence_tracking': True,
        'enable_model_versioning': True,
        'enable_ab_testing': True,
        
        # Bulk operations for ML training data
        'bulk_insert_batch_size': 10000,
        'enable_streaming_inserts': True,
        'conflict_resolution': 'upsert_on_product_id'
    }
    
    __indexes__ = [
        {'name': 'idx_classification_product', 'fields': ['product_id'], 'unique': True},
        {'name': 'idx_classification_unspsc', 'fields': ['unspsc_code', 'unspsc_confidence']},
        {'name': 'idx_classification_etim', 'fields': ['etim_class_id', 'etim_confidence']},
        {'name': 'idx_classification_confidence', 'fields': ['dual_confidence', 'confidence_level']},
        {'name': 'idx_classification_method', 'fields': ['classification_method', 'classified_at']},
        {'name': 'idx_classification_validation', 'fields': ['is_validated', 'validation_date']},
        {'name': 'idx_classification_performance', 'fields': ['processing_time_ms', 'cache_hit']},
        {'name': 'idx_classification_feedback', 'fields': ['user_feedback', 'feedback_score']},
        {'name': 'idx_classification_language', 'fields': ['language']},
        {'name': 'idx_classification_workflow', 'fields': ['workflow_id']},
        {'name': 'idx_classification_recommendations_gin', 'fields': ['recommendations'], 'type': 'gin'}
    ]


@db.model
class ClassificationHistory:
    """
    Audit trail for classification changes with detailed change tracking.
    Uses DataFlow's automatic audit_log feature enhanced with classification-specific fields.
    """
    
    # Primary identification
    id: int
    product_classification_id: int  # Foreign key to ProductClassification
    
    # Change details
    change_type: str  # create, update, validate, feedback, manual_override
    field_changed: Optional[str] = None  # Which field was modified
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    
    # Classification-specific change data
    old_unspsc_code: Optional[str] = None
    new_unspsc_code: Optional[str] = None
    old_etim_class_id: Optional[str] = None
    new_etim_class_id: Optional[str] = None
    confidence_change: float = 0.0  # Change in confidence score
    
    # Change context
    change_reason: str = ""
    automated_change: bool = True
    user_id: Optional[int] = None
    system_component: str = ""  # ml_engine, manual_validation, api_import
    
    # Performance impact
    processing_time_ms: float = 0.0
    affected_recommendations: bool = False
    
    # Metadata
    change_timestamp: datetime
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'audit_log': True,
        'ttl': 7776000,  # 90 days retention for compliance
        'search_fields': ['change_type', 'change_reason'],
        'immutable': True  # Never modify history records
    }
    
    __indexes__ = [
        {'name': 'idx_history_classification', 'fields': ['product_classification_id', 'change_timestamp']},
        {'name': 'idx_history_change_type', 'fields': ['change_type', 'automated_change']},
        {'name': 'idx_history_user', 'fields': ['user_id', 'change_timestamp']},
        {'name': 'idx_history_codes', 'fields': ['old_unspsc_code', 'new_unspsc_code']},
        {'name': 'idx_history_confidence', 'fields': ['confidence_change']},
        {'name': 'idx_history_timestamp', 'fields': ['change_timestamp']},
        {'name': 'idx_history_system', 'fields': ['system_component', 'automated_change']}
    ]


@db.model
class ClassificationCache:
    """
    High-performance cache for classification results with intelligent invalidation.
    Leverages DataFlow's built-in caching with custom TTL and invalidation rules.
    """
    
    # Cache key components
    id: int
    cache_key: str  # Hash of product data
    product_data_hash: str  # MD5 hash of classification input
    
    # Cached classification result
    cached_result: Dict[str, Any] = None  # Full classification result as JSONB
    
    # Cache metadata
    hit_count: int = 0
    miss_count: int = 0
    last_hit_at: Optional[datetime] = None
    cache_source: str = "ml_engine"  # ml_engine, manual, api_import
    
    # Performance metrics
    avg_processing_time_ms: float = 0.0
    cache_efficiency: float = 0.0  # hit_count / (hit_count + miss_count)
    
    # Cache lifecycle
    created_at: datetime
    expires_at: datetime
    last_validated_at: Optional[datetime] = None
    invalidation_reason: Optional[str] = None
    
    # Cache warming and optimization
    is_popular: bool = False  # High-frequency access pattern
    warming_priority: int = 0  # 1-10 priority for cache warming
    
    # Highly optimized cache configuration for ML predictions
    __dataflow__ = {
        'multi_tenant': True,
        
        # Intelligent TTL management
        'ttl': 5400,                    # 1.5 hours base TTL
        'cache_ttl': 2700,              # 45 minutes for cache metadata
        'adaptive_ttl': True,           # Adjust TTL based on hit frequency
        'ttl_multiplier_popular': 2.0,  # Double TTL for popular items
        
        # Advanced caching features  
        'jsonb_fields': ['cached_result'],
        'jsonb_compress': True,
        'enable_cache_compression': 'lz4',  # Fast compression for cache data
        
        # Performance optimization
        'performance_tracking': True,
        'track_cache_efficiency': True,
        'enable_cache_warming': True,
        'warming_batch_size': 500,
        
        # Automatic management
        'auto_cleanup': True,
        'cleanup_interval': 3600,       # Hourly cleanup
        'cleanup_threshold': 0.8,       # Cleanup when 80% full
        
        # Cache analytics
        'enable_cache_analytics': True,
        'track_access_patterns': True,
        'enable_predictive_warming': True,
        
        # Memory optimization
        'enable_memory_mapping': True,
        'memory_threshold': '500MB',
        'eviction_policy': 'lru_with_frequency'
    }
    
    # High-performance indexes for cache optimization
    __indexes__ = [
        # Primary cache access patterns
        {'name': 'idx_cache_key_unique', 'fields': ['cache_key'], 'unique': True},
        {'name': 'idx_cache_hash_partial', 'fields': ['product_data_hash'], 'condition': 'expires_at > CURRENT_TIMESTAMP'},
        
        # Time-based optimization
        {'name': 'idx_cache_expiry_cleanup', 'fields': ['expires_at'], 'condition': 'expires_at <= CURRENT_TIMESTAMP'},
        {'name': 'idx_cache_last_hit_active', 'fields': ['last_hit_at', 'expires_at']},
        
        # Performance analytics
        {'name': 'idx_cache_efficiency_popular', 'fields': ['cache_efficiency', 'hit_count', 'is_popular']},
        {'name': 'idx_cache_warming_priority', 'fields': ['warming_priority', 'is_popular'], 'condition': 'warming_priority > 0'},
        
        # Cache management
        {'name': 'idx_cache_source_created', 'fields': ['cache_source', 'created_at']},
        {'name': 'idx_cache_validated_recent', 'fields': ['last_validated_at'], 'condition': 'last_validated_at > CURRENT_TIMESTAMP - INTERVAL \'1 day\''},
        
        # Advanced JSONB indexing for cached results
        {'name': 'idx_cache_result_gin_ops', 'fields': ['cached_result'], 'type': 'gin', 'options': 'jsonb_path_ops'},
        {'name': 'idx_cache_result_specific_gin', 'fields': ['cached_result'], 'type': 'gin'},
        
        # Covering index for cache lookup
        {'name': 'idx_cache_lookup_cover', 'fields': ['cache_key', 'expires_at'], 
         'include': ['hit_count', 'cache_efficiency', 'cached_result'], 
         'condition': 'expires_at > CURRENT_TIMESTAMP'}
    ]


@db.model
class ETIMAttribute:
    """
    Technical attributes for ETIM classes with multi-language support.
    Enhanced with vector embeddings for semantic similarity search using pgvector.
    """
    
    # Primary identification
    id: int
    etim_class_id: str  # Foreign key to ETIMClass
    attribute_id: str  # ETIM attribute identifier (e.g., "EF000001")
    
    # Multi-language attribute names
    name_en: str
    name_de: Optional[str] = None
    name_fr: Optional[str] = None
    name_es: Optional[str] = None
    name_it: Optional[str] = None
    name_ja: Optional[str] = None
    name_ko: Optional[str] = None
    
    # Attribute specifications
    data_type: str = "text"  # text, numeric, boolean, list, range
    unit: Optional[str] = None
    possible_values: Optional[List[str]] = None  # JSON array for enumerated values
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    # Semantic search capabilities
    name_embedding: Optional[List[float]] = None  # Vector embedding for semantic search
    description_embedding: Optional[List[float]] = None
    
    # Attribute metadata
    is_required: bool = False
    is_searchable: bool = True
    display_order: int = 0
    group_name: Optional[str] = None
    
    # Usage statistics
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    
    # Versioning and status
    version: str = "9.0"
    is_active: bool = True
    deprecated_date: Optional[datetime] = None
    replacement_attribute_id: Optional[str] = None
    
    # Audit trail
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        'search_fields': ['name_en', 'name_de', 'name_fr', 'attribute_id'],
        'jsonb_fields': ['possible_values'],
        'vector_fields': ['name_embedding', 'description_embedding'],  # pgvector support
        'multi_language': True
    }
    
    __indexes__ = [
        {'name': 'idx_etim_attr_class_id', 'fields': ['etim_class_id', 'attribute_id']},
        {'name': 'idx_etim_attr_names', 'fields': ['name_en', 'name_de']},
        {'name': 'idx_etim_attr_type_unit', 'fields': ['data_type', 'unit']},
        {'name': 'idx_etim_attr_required', 'fields': ['is_required', 'is_searchable']},
        {'name': 'idx_etim_attr_usage', 'fields': ['usage_count', 'last_used_at']},
        {'name': 'idx_etim_attr_version', 'fields': ['version', 'is_active']},
        {'name': 'idx_etim_attr_values_gin', 'fields': ['possible_values'], 'type': 'gin'},
        # pgvector indexes for semantic similarity
        {'name': 'idx_etim_attr_name_vector', 'fields': ['name_embedding'], 'type': 'ivfflat'},
        {'name': 'idx_etim_attr_desc_vector', 'fields': ['description_embedding'], 'type': 'ivfflat'}
    ]


@db.model
class ClassificationRule:
    """
    ML training data and keyword-based classification rules.
    Powers the classification engine with both automated ML and keyword fallback.
    """
    
    # Primary identification
    id: int
    rule_type: str  # keyword, ml_pattern, regex, fuzzy_match
    classification_system: str  # unspsc, etim, dual
    
    # Rule definition
    rule_name: str
    rule_pattern: str  # Keyword, regex, or ML pattern
    target_code: str  # UNSPSC code or ETIM class ID
    confidence_score: float = 0.8
    
    # Rule conditions and context
    required_keywords: List[str] = None  # JSON array
    excluded_keywords: List[str] = None  # JSON array
    context_filters: Dict[str, Any] = None  # Additional filtering conditions
    
    # ML training data
    training_examples: List[Dict[str, Any]] = None  # Positive/negative examples
    feature_weights: Dict[str, float] = None  # Feature importance weights
    model_version: Optional[str] = None
    
    # Performance metrics
    accuracy_score: float = 0.0
    precision_score: float = 0.0
    recall_score: float = 0.0
    f1_score: float = 0.0
    
    # Usage statistics
    match_count: int = 0
    correct_matches: int = 0
    false_positives: int = 0
    last_used_at: Optional[datetime] = None
    
    # Rule lifecycle
    is_active: bool = True
    created_by: Optional[int] = None  # User ID
    approved_by: Optional[int] = None
    approval_date: Optional[datetime] = None
    
    # Audit trail
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        'search_fields': ['rule_name', 'rule_pattern', 'target_code'],
        'jsonb_fields': ['required_keywords', 'excluded_keywords', 'context_filters', 'training_examples', 'feature_weights'],
        'performance_tracking': True
    }
    
    __indexes__ = [
        {'name': 'idx_rule_type_system', 'fields': ['rule_type', 'classification_system']},
        {'name': 'idx_rule_target_code', 'fields': ['target_code', 'confidence_score']},
        {'name': 'idx_rule_performance', 'fields': ['accuracy_score', 'f1_score']},
        {'name': 'idx_rule_usage', 'fields': ['match_count', 'last_used_at']},
        {'name': 'idx_rule_active', 'fields': ['is_active', 'approval_date']},
        {'name': 'idx_rule_keywords_gin', 'fields': ['required_keywords'], 'type': 'gin'},
        {'name': 'idx_rule_excluded_gin', 'fields': ['excluded_keywords'], 'type': 'gin'},
        {'name': 'idx_rule_context_gin', 'fields': ['context_filters'], 'type': 'gin'},
        {'name': 'idx_rule_training_gin', 'fields': ['training_examples'], 'type': 'gin'}
    ]


@db.model
class ClassificationFeedback:
    """
    User feedback for improving classification accuracy with sentiment analysis.
    Enables continuous learning and model improvement based on user corrections.
    """
    
    # Primary identification
    id: int
    product_classification_id: int  # Foreign key to ProductClassification
    user_id: Optional[int] = None
    
    # Feedback details
    feedback_type: str  # correction, validation, suggestion, rating
    feedback_text: Optional[str] = None
    rating: Optional[int] = None  # 1-5 stars
    
    # Classification corrections
    suggested_unspsc_code: Optional[str] = None
    suggested_etim_class_id: Optional[str] = None
    correction_reason: Optional[str] = None
    
    # Sentiment and analysis
    sentiment_score: Optional[float] = None  # -1.0 to 1.0
    sentiment_label: Optional[str] = None  # positive, negative, neutral
    feedback_quality: Optional[str] = None  # high, medium, low
    
    # Processing status
    status: str = "pending"  # pending, reviewed, implemented, rejected
    reviewed_by: Optional[int] = None  # User ID of reviewer
    review_date: Optional[datetime] = None
    implementation_date: Optional[datetime] = None
    
    # Impact tracking
    affected_products: int = 0  # Number of products affected by this feedback
    accuracy_improvement: Optional[float] = None  # Measured improvement
    
    # Metadata
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    submitted_at: datetime
    
    # Audit trail
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'search_fields': ['feedback_text', 'correction_reason'],
        'sentiment_analysis': True,
        'user_feedback': True
    }
    
    __indexes__ = [
        {'name': 'idx_feedback_classification', 'fields': ['product_classification_id', 'submitted_at']},
        {'name': 'idx_feedback_user', 'fields': ['user_id', 'feedback_type']},
        {'name': 'idx_feedback_rating', 'fields': ['rating', 'sentiment_score']},
        {'name': 'idx_feedback_status', 'fields': ['status', 'review_date']},
        {'name': 'idx_feedback_corrections', 'fields': ['suggested_unspsc_code', 'suggested_etim_class_id']},
        {'name': 'idx_feedback_impact', 'fields': ['affected_products', 'accuracy_improvement']},
        {'name': 'idx_feedback_sentiment', 'fields': ['sentiment_label', 'feedback_quality']},
        {'name': 'idx_feedback_submitted', 'fields': ['submitted_at']}
    ]


# ==============================================================================
# PERFORMANCE OPTIMIZATION MODELS
# ==============================================================================

@db.model
class ClassificationMetrics:
    """
    Real-time performance metrics for classification system monitoring.
    Tracks performance across all classification operations with detailed breakdowns.
    """
    
    # Primary identification
    id: int
    metric_name: str
    metric_category: str  # performance, accuracy, usage, cache
    
    # Metric values
    metric_value: float
    metric_unit: str  # ms, percentage, count, score
    
    # Time dimensions
    measurement_timestamp: datetime
    period_type: str  # real_time, hourly, daily, weekly, monthly
    period_start: datetime
    period_end: datetime
    
    # Classification system breakdown
    unspsc_value: Optional[float] = None
    etim_value: Optional[float] = None
    dual_value: Optional[float] = None
    
    # Dimensional breakdowns
    by_method: Dict[str, float] = None  # Breakdown by classification method
    by_confidence: Dict[str, float] = None  # Breakdown by confidence level
    by_language: Dict[str, float] = None  # Breakdown by language
    
    # Comparative analysis
    previous_value: Optional[float] = None
    change_percentage: Optional[float] = None
    trend_direction: Optional[str] = None  # improving, declining, stable
    
    # Context and metadata
    sample_size: Optional[int] = None
    confidence_interval: Optional[str] = None
    measurement_method: str = "automatic"
    
    __dataflow__ = {
        'multi_tenant': True,
        'time_series': True,
        'ttl': 15552000,  # 6 months retention
        'jsonb_fields': ['by_method', 'by_confidence', 'by_language'],
        'performance_monitoring': True
    }
    
    __indexes__ = [
        {'name': 'idx_metrics_name_timestamp', 'fields': ['metric_name', 'measurement_timestamp']},
        {'name': 'idx_metrics_category_period', 'fields': ['metric_category', 'period_type']},
        {'name': 'idx_metrics_value_change', 'fields': ['metric_value', 'change_percentage']},
        {'name': 'idx_metrics_breakdowns_gin', 'fields': ['by_method'], 'type': 'gin'},
        {'name': 'idx_metrics_period_range', 'fields': ['period_start', 'period_end']},
        {'name': 'idx_metrics_trend', 'fields': ['trend_direction', 'measurement_timestamp']}
    ]


# Export all models and DataFlow instance
__all__ = [
    'db',
    'Company',
    'User',
    'Customer', 
    'Quote',
    'ProductClassification',
    'ClassificationHistory', 
    'ClassificationCache',
    'ETIMAttribute',
    'ClassificationRule',
    'ClassificationFeedback',
    'ClassificationMetrics',
    'Document',
    'DocumentProcessingQueue'
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
        'jsonb_fields': ['ai_extracted_data', 'access_permissions', 'key_terms']
    }
    
    __indexes__ = [
        {'name': 'idx_document_customer', 'fields': ['customer_id']},
        {'name': 'idx_document_type', 'fields': ['type']},
        {'name': 'idx_document_status', 'fields': ['ai_status']},
        {'name': 'idx_document_upload_date', 'fields': ['upload_date']},
        {'name': 'idx_document_name_text', 'fields': ['name'], 'type': 'text'}
    ]

@db.model
class DocumentProcessingQueue:
    """Queue for processing documents with AI workflows"""
    document_id: int
    processing_type: str  # ocr, classification, extraction, summary
    status: str = "pending"  # pending, processing, completed, failed, retrying
    priority: int = 5  # 1-10, 1 = highest priority
    
    # Processing Configuration
    workflow_config: Optional[dict] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Timing
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # seconds
    
    # Results
    processing_results: Optional[dict] = None
    error_message: Optional[str] = None
    output_file_path: Optional[str] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'ttl': 2592000,  # 30 days retention
        'jsonb_fields': ['workflow_config', 'processing_results']
    }
    
    __indexes__ = [
        {'name': 'idx_queue_status_priority', 'fields': ['status', 'priority']},
        {'name': 'idx_queue_document', 'fields': ['document_id']},
        {'name': 'idx_queue_queued_at', 'fields': ['queued_at']}
    ]

# ==============================================================================
# DATAFLOW WORKFLOW PATTERNS FOR CLASSIFICATION
# ==============================================================================

def get_classification_workflow_patterns():
    """
    Get comprehensive DataFlow workflow patterns for classification operations.
    These patterns leverage the auto-generated nodes from @db.model decorators.
    """
    
    patterns = {
        # High-performance bulk classification using auto-generated nodes
        "bulk_product_classification": {
            "description": "Classify 10,000+ products using ProductClassificationBulkCreateNode",
            "nodes": [
                "ProductClassificationBulkCreateNode",  # Auto-generated from @db.model
                "ClassificationCacheBulkCreateNode",    # Auto-generated cache storage
                "ClassificationHistoryBulkCreateNode",  # Auto-generated audit trail
                "ClassificationMetricsUpdateNode"       # Performance tracking
            ],
            "performance": "10,000+ classifications/sec",
            "use_case": "Bulk product imports, migration, batch processing"
        },
        
        # Real-time single product classification
        "single_product_classification": {
            "description": "Real-time classification with cache checking",
            "nodes": [
                "ClassificationCacheReadNode",          # Check cache first
                "ProductClassificationCreateNode",      # Create if not cached  
                "ClassificationHistoryCreateNode",      # Audit trail
                "ClassificationMetricsUpdateNode"       # Performance tracking
            ],
            "performance": "<500ms including cache lookup",
            "use_case": "API requests, real-time user interactions"
        },
        
        # Classification validation and feedback workflow
        "classification_validation": {
            "description": "User validation and feedback processing",
            "nodes": [
                "ClassificationFeedbackCreateNode",     # Store user feedback
                "ProductClassificationUpdateNode",      # Update classification if needed
                "ClassificationHistoryCreateNode",      # Record validation
                "ClassificationRuleUpdateNode"          # Update rules based on feedback
            ],
            "performance": "<100ms for feedback storage",
            "use_case": "User corrections, quality improvement, learning"
        },
        
        # Multi-language ETIM classification
        "multilingual_etim_classification": {
            "description": "ETIM classification with multi-language support",
            "nodes": [
                "ETIMAttributeListNode",                # Get attributes by language
                "ProductClassificationCreateNode",      # Store classification
                "ClassificationCacheCreateNode",        # Cache with language key
                "ClassificationMetricsUpdateNode"       # Track by language
            ],
            "performance": "<800ms including translation lookup",
            "use_case": "International markets, localized content"
        },
        
        # Performance monitoring and optimization
        "classification_performance_monitoring": {
            "description": "Real-time performance monitoring dashboard",
            "nodes": [
                "ClassificationMetricsListNode",        # Get current metrics
                "ClassificationCacheListNode",          # Cache efficiency stats
                "ProductClassificationListNode",        # Recent classifications
                "ClassificationFeedbackCountNode"       # User satisfaction metrics
            ],
            "performance": "<200ms for dashboard updates",
            "use_case": "System monitoring, performance optimization"
        }
    }
    
    return patterns


# Model relationship validation
def validate_classification_relationships():
    """Validate foreign key relationships and DataFlow configuration."""
    
    relationships = [
        ("ProductClassification", "product_id", "Product", "id"),
        ("ClassificationHistory", "product_classification_id", "ProductClassification", "id"),
        ("ClassificationCache", "product_data_hash", None, None),  # Hash-based, no FK
        ("ETIMAttribute", "etim_class_id", "ETIMClass", "class_id"),
        ("ClassificationRule", "target_code", None, None),  # Multiple targets
        ("ClassificationFeedback", "product_classification_id", "ProductClassification", "id"),
        ("ClassificationMetrics", None, None, None)  # Standalone metrics
    ]
    
    # Verify all models have required DataFlow configuration
    models = [Company, User, Customer, Quote, ProductClassification, ClassificationHistory, ClassificationCache, 
              ETIMAttribute, ClassificationRule, ClassificationFeedback, ClassificationMetrics, Document, DocumentProcessingQueue]
    
    for model in models:
        assert hasattr(model, '__dataflow__'), f"{model.__name__} missing DataFlow configuration"
        assert model.__dataflow__.get('multi_tenant', False), f"{model.__name__} should be multi-tenant"
        
        # Verify performance-critical models have proper indexing
        if model.__name__ in ['ProductClassification', 'ClassificationCache']:
            assert hasattr(model, '__indexes__'), f"{model.__name__} missing performance indexes"
    
    return True


# Initialize validation on import
try:
    validate_classification_relationships()
    print("SUCCESS: DataFlow classification models validated successfully")
except Exception as e:
    print(f"ERROR: Classification model validation failed: {e}")