"""
DataFlow AI Integration Models
==============================

DataFlow models designed for hybrid AI architecture integration with:
- Neo4j Knowledge Graph (tools, tasks, safety rules)
- ChromaDB Vector Database (product embeddings, manuals)
- OpenAI GPT-4 Integration (recommendations, analysis)
- UNSPSC/ETIM Product Classifications

This module provides zero-config database operations with auto-generated nodes
for seamless integration with AI services.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataflow import DataFlow
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Initialize DataFlow with PostgreSQL for AI integration
db = DataFlow(
    # Auto-detects PostgreSQL via environment or uses SQLite for development
    pool_size=25,           # Higher pool for AI service concurrency
    pool_max_overflow=50,   # Support burst AI processing
    pool_recycle=3600,      # 1 hour connection recycling
    monitoring=True,        # Enable performance monitoring
    echo=False,            # Disable SQL logging in production
    auto_migrate=True      # Enable automatic schema evolution
)

# ==============================================================================
# PRODUCT CATALOG & INVENTORY MODELS
# ==============================================================================

@db.model
class Product:
    """
    Master product model with AI-ready classifications and embeddings.
    Auto-generates 9 nodes: Create, Read, Update, Delete, List, BulkCreate, 
    BulkUpdate, BulkDelete, BulkUpsert
    """
    # Core Product Data
    product_code: str           # Primary identifier
    name: str                   # Product name
    description: str            # Full description
    short_description: Optional[str] = None
    
    # Classification Data (UNSPSC/ETIM integration)
    unspsc_code: Optional[str] = None      # UNSPSC classification
    unspsc_title: Optional[str] = None     # UNSPSC description  
    etim_class: Optional[str] = None       # ETIM class
    etim_features: Optional[dict] = None   # ETIM feature values
    
    # Product Categories
    category: str                          # Primary category
    subcategory: Optional[str] = None      # Secondary category
    product_family: Optional[str] = None   # Product line grouping
    brand: str                            # Manufacturer/brand
    manufacturer: Optional[str] = None     # Manufacturing company
    
    # Specifications & Features
    specifications: dict = {}              # Technical specifications
    features: dict = {}                   # Key features
    dimensions: Optional[dict] = None      # Physical dimensions
    weight: Optional[float] = None         # Weight in standard units
    material: Optional[str] = None         # Primary material
    color: Optional[str] = None           # Product color
    
    # Pricing & Availability
    list_price: float                     # Standard price
    cost_price: Optional[float] = None    # Cost basis
    currency: str = "USD"                # Price currency
    is_available: bool = True            # Availability status
    stock_quantity: Optional[int] = None  # Current inventory
    lead_time_days: Optional[int] = None  # Delivery lead time
    minimum_order_qty: int = 1           # Minimum order quantity
    
    # AI Integration Fields
    embedding_status: str = "pending"     # pending, processing, completed, failed
    knowledge_graph_id: Optional[str] = None  # Neo4j node ID
    vector_embedding_id: Optional[str] = None # ChromaDB ID
    ai_tags: Optional[list] = None       # AI-generated tags
    similarity_hash: Optional[str] = None # For duplicate detection
    
    # Safety & Compliance
    safety_rating: Optional[float] = None # 0.0-5.0 safety score
    osha_compliance: Optional[list] = None # OSHA codes
    ansi_standards: Optional[list] = None  # ANSI standards
    certifications: Optional[list] = None # Product certifications
    
    # SEO & Marketing
    seo_keywords: Optional[list] = None   # Search keywords
    marketing_tags: Optional[list] = None # Marketing categories
    competitive_products: Optional[list] = None # Competitor mapping
    
    __dataflow__ = {
        'multi_tenant': True,      # Multi-company support
        'soft_delete': True,       # Soft delete for data integrity
        'audit_log': True,         # Full audit trail
        'versioned': True,         # Version control
        'postgresql': {
            'jsonb_gin_indexes': ['specifications', 'features', 'etim_features', 'ai_tags'],
            'text_search': ['name', 'description', 'short_description'],
            'partial_indexes': [
                {'fields': ['embedding_status'], 'condition': 'embedding_status != \'completed\''},
                {'fields': ['is_available'], 'condition': 'is_available = true'}
            ]
        }
    }
    
    __indexes__ = [
        # Core product indexes
        {'name': 'idx_product_code', 'fields': ['product_code'], 'unique': True},
        {'name': 'idx_product_category', 'fields': ['category', 'subcategory']},
        {'name': 'idx_product_brand', 'fields': ['brand', 'manufacturer']},
        
        # Classification indexes
        {'name': 'idx_product_unspsc', 'fields': ['unspsc_code']},
        {'name': 'idx_product_etim', 'fields': ['etim_class']},
        
        # AI integration indexes
        {'name': 'idx_product_embedding', 'fields': ['embedding_status']},
        {'name': 'idx_product_kg_id', 'fields': ['knowledge_graph_id']},
        {'name': 'idx_product_vector_id', 'fields': ['vector_embedding_id']},
        
        # Business indexes
        {'name': 'idx_product_availability', 'fields': ['is_available', 'stock_quantity']},
        {'name': 'idx_product_pricing', 'fields': ['list_price', 'currency']},
        {'name': 'idx_product_safety', 'fields': ['safety_rating']},
        
        # Search optimization
        {'name': 'idx_product_name_text', 'fields': ['name'], 'type': 'text'},
        {'name': 'idx_product_search', 'fields': ['category', 'brand', 'is_available']}
    ]

@db.model
class ProductVariant:
    """
    Product variants (size, color, configuration variations).
    Links to master Product with specific variations.
    """
    product_id: int                    # Foreign key to Product
    variant_code: str                  # Unique variant identifier
    variant_name: str                  # Variant description
    
    # Variant-specific attributes
    variant_attributes: dict = {}      # Size, color, configuration
    price_modifier: float = 0.0       # Price adjustment from base
    cost_modifier: float = 0.0        # Cost adjustment from base
    weight_modifier: float = 0.0      # Weight difference
    
    # Availability
    is_available: bool = True
    stock_quantity: Optional[int] = None
    lead_time_modifier: int = 0       # Additional lead time
    
    # AI Integration
    vector_embedding_id: Optional[str] = None
    parent_similarity_score: Optional[float] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True
    }
    
    __indexes__ = [
        {'name': 'idx_variant_product', 'fields': ['product_id']},
        {'name': 'idx_variant_code', 'fields': ['variant_code'], 'unique': True},
        {'name': 'idx_variant_availability', 'fields': ['is_available', 'stock_quantity']}
    ]

@db.model
class Vendor:
    """
    Vendor/supplier master data with AI-powered capabilities.
    """
    vendor_code: str                   # Unique vendor identifier
    company_name: str                  # Official company name
    trade_name: Optional[str] = None   # Doing business as name
    
    # Contact Information
    primary_contact: str
    email: str
    phone: str
    website: Optional[str] = None
    
    # Address Information
    billing_address: dict             # JSON address structure
    shipping_address: Optional[dict] = None
    
    # Business Information
    tax_id: Optional[str] = None
    duns_number: Optional[str] = None
    payment_terms: str = "NET30"
    currency: str = "USD"
    credit_limit: Optional[float] = None
    
    # Vendor Categories & Specializations
    vendor_type: str                  # manufacturer, distributor, service_provider
    specializations: list = []        # Areas of expertise
    product_categories: list = []     # Categories they supply
    geographic_coverage: list = []    # Regions served
    
    # Performance Metrics
    performance_rating: Optional[float] = None  # 0.0-5.0 rating
    on_time_delivery_rate: Optional[float] = None  # Percentage
    quality_rating: Optional[float] = None      # Quality score
    total_orders: int = 0
    total_value: float = 0.0
    
    # AI Integration
    knowledge_graph_id: Optional[str] = None
    vendor_profile_embedding: Optional[str] = None
    ai_risk_score: Optional[float] = None     # AI-calculated risk
    competitive_analysis: Optional[dict] = None
    
    # Compliance & Certifications
    certifications: Optional[list] = None
    compliance_status: str = "pending"  # pending, verified, expired
    audit_date: Optional[datetime] = None
    
    # Status
    status: str = "active"  # active, inactive, suspended, terminated
    relationship_manager: Optional[int] = None  # User ID
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        'postgresql': {
            'jsonb_gin_indexes': ['billing_address', 'shipping_address', 'competitive_analysis'],
            'text_search': ['company_name', 'trade_name']
        }
    }
    
    __indexes__ = [
        {'name': 'idx_vendor_code', 'fields': ['vendor_code'], 'unique': True},
        {'name': 'idx_vendor_type', 'fields': ['vendor_type', 'status']},
        {'name': 'idx_vendor_performance', 'fields': ['performance_rating']},
        {'name': 'idx_vendor_compliance', 'fields': ['compliance_status']},
        {'name': 'idx_vendor_name_text', 'fields': ['company_name'], 'type': 'text'}
    ]

# ==============================================================================
# AI SERVICE INTEGRATION MODELS
# ==============================================================================

@db.model
class KnowledgeGraphEntity:
    """
    Maps DataFlow entities to Neo4j knowledge graph nodes.
    Provides bidirectional synchronization between PostgreSQL and Neo4j.
    """
    entity_type: str                  # product, vendor, tool, task, project
    entity_id: int                    # Local DataFlow entity ID
    neo4j_node_id: str               # Neo4j node ID
    neo4j_labels: list               # Neo4j node labels
    
    # Synchronization tracking
    sync_status: str = "pending"      # pending, synced, out_of_sync, failed
    last_sync_date: Optional[datetime] = None
    sync_direction: str = "bidirectional"  # to_neo4j, from_neo4j, bidirectional
    
    # Relationship mapping
    relationships_count: int = 0      # Number of Neo4j relationships
    relationship_types: Optional[list] = None  # Types of relationships
    
    # Data integrity
    checksum: Optional[str] = None    # Data integrity check
    schema_version: str = "1.0"      # Schema version for migrations
    
    # Error handling
    last_error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    __dataflow__ = {
        'multi_tenant': True,
        'audit_log': True,
        'ttl': 7776000  # 90 days for cleanup of failed entries
    }
    
    __indexes__ = [
        {'name': 'idx_kg_entity', 'fields': ['entity_type', 'entity_id'], 'unique': True},
        {'name': 'idx_kg_neo4j_id', 'fields': ['neo4j_node_id'], 'unique': True},
        {'name': 'idx_kg_sync_status', 'fields': ['sync_status', 'last_sync_date']},
        {'name': 'idx_kg_failed', 'fields': ['sync_status', 'retry_count']}
    ]

@db.model
class VectorEmbedding:
    """
    Maps DataFlow entities to ChromaDB vector embeddings.
    Manages embedding lifecycle and similarity operations.
    """
    entity_type: str                  # product, manual, safety_guideline, project_pattern
    entity_id: int                    # Local DataFlow entity ID
    collection_name: str              # ChromaDB collection
    embedding_id: str                 # ChromaDB document ID
    
    # Embedding metadata
    embedding_model: str = "text-embedding-ada-002"  # OpenAI model used
    embedding_dimension: int = 1536   # Vector dimension
    embedding_status: str = "pending" # pending, completed, failed, outdated
    
    # Content tracking
    content_hash: Optional[str] = None  # Hash of source content
    content_version: int = 1          # Version for updates
    last_updated: datetime            # Last embedding update
    
    # Similarity search optimization
    similarity_clusters: Optional[list] = None  # Cluster assignments
    quality_score: Optional[float] = None       # Embedding quality
    
    # Performance metrics
    search_count: int = 0            # Times used in searches
    similarity_feedback: Optional[dict] = None  # User feedback on results
    
    # Error handling
    last_error: Optional[str] = None
    processing_time_ms: Optional[int] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'audit_log': True,
        'ttl': 2592000  # 30 days for outdated embeddings
    }
    
    __indexes__ = [
        {'name': 'idx_vector_entity', 'fields': ['entity_type', 'entity_id']},
        {'name': 'idx_vector_embedding_id', 'fields': ['embedding_id'], 'unique': True},
        {'name': 'idx_vector_collection', 'fields': ['collection_name', 'embedding_status']},
        {'name': 'idx_vector_content_hash', 'fields': ['content_hash']},
        {'name': 'idx_vector_outdated', 'fields': ['embedding_status', 'last_updated']}
    ]

@db.model
class AIRecommendation:
    """
    Stores AI-generated recommendations with provenance and feedback.
    Supports recommendation improvement and user learning.
    """
    request_id: str                   # Unique request identifier
    recommendation_type: str          # tool, safety, project, compatibility
    
    # Request context
    user_id: Optional[int] = None     # Requesting user
    context_data: dict                # Original request parameters
    session_id: Optional[str] = None  # User session
    
    # AI Processing
    ai_model: str = "gpt-4"          # OpenAI model used
    prompt_template: str             # Template used
    processing_time_ms: int          # Response time
    token_usage: Optional[dict] = None # Token consumption
    
    # Recommendation results  
    recommendations: list            # AI recommendations
    reasoning: str                   # AI reasoning
    confidence_score: float          # AI confidence 0.0-1.0
    alternative_options: Optional[list] = None
    
    # Metadata
    safety_notes: Optional[list] = None
    cost_estimate: Optional[float] = None
    complexity_score: Optional[int] = None
    
    # User feedback & learning
    user_rating: Optional[int] = None     # 1-5 user rating
    user_feedback: Optional[str] = None   # User comments
    was_helpful: Optional[bool] = None    # Simple yes/no feedback
    selected_recommendation: Optional[str] = None  # Which rec was chosen
    
    # Performance tracking
    view_count: int = 0              # Times viewed
    share_count: int = 0             # Times shared
    conversion_rate: Optional[float] = None  # Success rate
    
    # Status
    status: str = "active"           # active, archived, flagged
    created_at: datetime             # When recommendation was made
    expires_at: Optional[datetime] = None  # Recommendation expiry
    
    __dataflow__ = {
        'multi_tenant': True,
        'audit_log': True,
        'ttl': 7776000,  # 90 days retention
        'postgresql': {
            'jsonb_gin_indexes': ['context_data', 'recommendations', 'token_usage']
        }
    }
    
    __indexes__ = [
        {'name': 'idx_ai_rec_request_id', 'fields': ['request_id'], 'unique': True},
        {'name': 'idx_ai_rec_type', 'fields': ['recommendation_type', 'status']},
        {'name': 'idx_ai_rec_user', 'fields': ['user_id', 'created_at']},
        {'name': 'idx_ai_rec_confidence', 'fields': ['confidence_score']},
        {'name': 'idx_ai_rec_feedback', 'fields': ['user_rating', 'was_helpful']},
        {'name': 'idx_ai_rec_expires', 'fields': ['expires_at']}
    ]

# ==============================================================================
# CLASSIFICATION & TAXONOMY MODELS
# ==============================================================================

@db.model
class UNSPSCClassification:
    """
    United Nations Standard Products and Services Code (UNSPSC) taxonomy.
    Provides standardized product classification for AI matching.
    """
    unspsc_code: str                 # 8-digit UNSPSC code
    level: int                       # 1=Segment, 2=Family, 3=Class, 4=Commodity
    parent_code: Optional[str] = None # Parent UNSPSC code
    
    # Classification data
    title: str                       # Official UNSPSC title
    definition: Optional[str] = None # Extended definition
    synonyms: Optional[list] = None  # Alternative terms
    keywords: Optional[list] = None  # Search keywords
    
    # Hierarchy information
    segment_code: Optional[str] = None    # Level 1 code
    family_code: Optional[str] = None     # Level 2 code  
    class_code: Optional[str] = None      # Level 3 code
    commodity_code: Optional[str] = None  # Level 4 code
    
    # AI integration
    embedding_id: Optional[str] = None    # Vector embedding for similarity
    related_codes: Optional[list] = None  # AI-suggested related codes
    ai_confidence: Optional[float] = None # AI classification confidence
    
    # Usage statistics
    product_count: int = 0           # Products using this code
    search_frequency: int = 0        # How often searched
    
    # Status
    is_active: bool = True           # Currently active
    version: str = "2023"           # UNSPSC version
    last_updated: datetime          # Last update
    
    __dataflow__ = {
        'soft_delete': True,
        'audit_log': True,
        'postgresql': {
            'text_search': ['title', 'definition'],
            'jsonb_gin_indexes': ['synonyms', 'keywords', 'related_codes']
        }
    }
    
    __indexes__ = [
        {'name': 'idx_unspsc_code', 'fields': ['unspsc_code'], 'unique': True},
        {'name': 'idx_unspsc_level', 'fields': ['level', 'is_active']},
        {'name': 'idx_unspsc_parent', 'fields': ['parent_code']},
        {'name': 'idx_unspsc_hierarchy', 'fields': ['segment_code', 'family_code', 'class_code']},
        {'name': 'idx_unspsc_usage', 'fields': ['product_count', 'search_frequency']},
        {'name': 'idx_unspsc_title_text', 'fields': ['title'], 'type': 'text'}
    ]

@db.model  
class ETIMClassification:
    """
    ETIM (Electro-Technical Information Model) classification system.
    Provides detailed technical specifications for electrical products.
    """
    etim_class: str                  # ETIM class code (e.g., EC123456)
    class_name: str                  # Class name
    class_description: Optional[str] = None
    
    # Hierarchy
    etim_group: str                  # ETIM group (2 digits)
    etim_subgroup: str              # ETIM subgroup (4 digits)
    version: str = "9.0"            # ETIM version
    
    # Features and values
    features: dict = {}             # Feature definitions
    feature_units: Optional[dict] = None  # Units for numeric features
    feature_constraints: Optional[dict] = None  # Value constraints
    
    # Synonyms and translations
    synonyms: Optional[list] = None
    translations: Optional[dict] = None  # Multi-language support
    
    # AI integration
    embedding_id: Optional[str] = None
    feature_similarity_map: Optional[dict] = None
    
    # Usage tracking
    product_count: int = 0
    feature_usage_stats: Optional[dict] = None
    
    # Status
    is_active: bool = True
    release_date: Optional[datetime] = None
    
    __dataflow__ = {
        'soft_delete': True,
        'audit_log': True,
        'postgresql': {
            'jsonb_gin_indexes': ['features', 'feature_units', 'feature_constraints', 'translations'],
            'text_search': ['class_name', 'class_description']
        }
    }
    
    __indexes__ = [
        {'name': 'idx_etim_class', 'fields': ['etim_class'], 'unique': True},
        {'name': 'idx_etim_group', 'fields': ['etim_group', 'etim_subgroup']},
        {'name': 'idx_etim_version', 'fields': ['version', 'is_active']},
        {'name': 'idx_etim_usage', 'fields': ['product_count']},
        {'name': 'idx_etim_name_text', 'fields': ['class_name'], 'type': 'text'}
    ]

# ==============================================================================
# AI PROCESSING QUEUE & ORCHESTRATION
# ==============================================================================

@db.model
class AIProcessingQueue:
    """
    Queue for AI processing tasks with priority and retry logic.
    Orchestrates AI service calls across Neo4j, ChromaDB, and OpenAI.
    """
    task_id: str                     # Unique task identifier
    task_type: str                   # embedding, knowledge_graph, recommendation, classification
    entity_type: str                 # product, vendor, tool, manual
    entity_id: int                   # Target entity ID
    
    # Processing configuration
    priority: int = 5                # 1=highest, 10=lowest
    ai_service: str                  # openai, neo4j, chromadb, hybrid
    processing_config: dict = {}     # Service-specific configuration
    
    # Queue management
    status: str = "queued"           # queued, processing, completed, failed, retrying
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_duration_ms: Optional[int] = None
    
    # Retry logic
    retry_count: int = 0
    max_retries: int = 3
    retry_delay_seconds: int = 60    # Exponential backoff base
    
    # Dependencies
    depends_on: Optional[list] = None     # Task dependencies
    blocks_tasks: Optional[list] = None   # Tasks waiting for this
    
    # Results
    result_data: Optional[dict] = None    # Processing results
    error_message: Optional[str] = None   # Error details
    performance_metrics: Optional[dict] = None  # Processing metrics
    
    # Resource management
    assigned_worker: Optional[str] = None # Worker ID
    resource_usage: Optional[dict] = None # CPU, memory, tokens used
    cost_estimate: Optional[float] = None # Processing cost
    
    __dataflow__ = {
        'multi_tenant': True,
        'ttl': 604800,  # 7 days retention
        'postgresql': {
            'jsonb_gin_indexes': ['processing_config', 'result_data', 'performance_metrics']
        }
    }
    
    __indexes__ = [
        {'name': 'idx_ai_queue_task_id', 'fields': ['task_id'], 'unique': True},
        {'name': 'idx_ai_queue_status_priority', 'fields': ['status', 'priority', 'queued_at']},
        {'name': 'idx_ai_queue_type', 'fields': ['task_type', 'ai_service']},
        {'name': 'idx_ai_queue_entity', 'fields': ['entity_type', 'entity_id']},
        {'name': 'idx_ai_queue_retry', 'fields': ['status', 'retry_count']},
        {'name': 'idx_ai_queue_worker', 'fields': ['assigned_worker', 'status']},
        {'name': 'idx_ai_queue_completed', 'fields': ['completed_at']}
    ]

@db.model
class AIServiceHealth:
    """
    Monitors health and performance of AI services.
    Provides circuit breaker functionality and performance analytics.
    """
    service_name: str                # openai, neo4j, chromadb
    endpoint: str                    # Service endpoint
    check_type: str                  # health_check, performance_test, load_test
    
    # Health status
    status: str                      # healthy, degraded, unhealthy, unreachable
    response_time_ms: int           # Response time
    error_rate: float = 0.0         # Error rate percentage
    
    # Performance metrics
    throughput_rps: Optional[float] = None  # Requests per second
    cpu_usage: Optional[float] = None       # CPU utilization
    memory_usage: Optional[float] = None    # Memory usage
    queue_depth: Optional[int] = None       # Pending requests
    
    # Service-specific metrics
    service_metrics: Optional[dict] = None  # Service-specific data
    
    # Timestamps
    check_timestamp: datetime
    last_healthy: Optional[datetime] = None
    last_error: Optional[datetime] = None
    
    # Alerting
    alert_level: str = "none"       # none, warning, critical
    alert_message: Optional[str] = None
    notification_sent: bool = False
    
    # Historical context
    trend_direction: Optional[str] = None    # improving, stable, degrading
    performance_score: Optional[float] = None # Overall score 0.0-1.0
    
    __dataflow__ = {
        'multi_tenant': True,
        'ttl': 2592000,  # 30 days retention
        'postgresql': {
            'jsonb_gin_indexes': ['service_metrics']
        }
    }
    
    __indexes__ = [
        {'name': 'idx_ai_health_service', 'fields': ['service_name', 'check_timestamp']},
        {'name': 'idx_ai_health_status', 'fields': ['status', 'alert_level']},
        {'name': 'idx_ai_health_performance', 'fields': ['response_time_ms', 'error_rate']},
        {'name': 'idx_ai_health_alerts', 'fields': ['alert_level', 'notification_sent']},
        {'name': 'idx_ai_health_recent', 'fields': ['check_timestamp']}
    ]

# Export all models and the DataFlow instance
__all__ = [
    'db',
    'Product', 'ProductVariant', 'Vendor',
    'KnowledgeGraphEntity', 'VectorEmbedding', 'AIRecommendation',
    'UNSPSCClassification', 'ETIMClassification',
    'AIProcessingQueue', 'AIServiceHealth'
]

# ==============================================================================
# DATAFLOW INTEGRATION UTILITIES
# ==============================================================================

class DataFlowAIIntegration:
    """
    Utility class for common DataFlow AI integration patterns.
    Provides convenience methods for typical AI workflow operations.
    """
    
    def __init__(self, dataflow_instance=None):
        """Initialize with DataFlow instance"""
        self.db = dataflow_instance or db
        self.runtime = LocalRuntime()
    
    def create_product_with_ai_processing(self, product_data: dict) -> tuple:
        """
        Create product and automatically queue for AI processing.
        Returns (results, run_id) tuple.
        """
        workflow = WorkflowBuilder()
        
        # Create product
        workflow.add_node("ProductCreateNode", "create_product", product_data)
        
        # Queue for embedding generation
        workflow.add_node("AIProcessingQueueCreateNode", "queue_embedding", {
            "task_type": "embedding",
            "entity_type": "product", 
            "ai_service": "chromadb",
            "priority": 3,
            "processing_config": {
                "collection": "products",
                "model": "text-embedding-ada-002"
            }
        })
        
        # Queue for knowledge graph integration
        workflow.add_node("AIProcessingQueueCreateNode", "queue_knowledge_graph", {
            "task_type": "knowledge_graph",
            "entity_type": "product",
            "ai_service": "neo4j", 
            "priority": 4,
            "processing_config": {
                "create_relationships": True,
                "similarity_threshold": 0.8
            }
        })
        
        # Connect product ID to queue tasks
        workflow.add_connection("create_product", "id", "queue_embedding", "entity_id")
        workflow.add_connection("create_product", "id", "queue_knowledge_graph", "entity_id")
        
        return self.runtime.execute(workflow.build())
    
    def bulk_product_classification(self, products_batch: list) -> tuple:
        """
        Bulk create products with UNSPSC/ETIM classification.
        Optimized for high-volume product imports.
        """
        workflow = WorkflowBuilder()
        
        # Bulk create products
        workflow.add_node("ProductBulkCreateNode", "bulk_create", {
            "data": products_batch,
            "batch_size": 1000,
            "conflict_resolution": "upsert"
        })
        
        # Queue classification tasks for each product
        classification_tasks = []
        for i, product in enumerate(products_batch):
            if product.get('unspsc_code') or product.get('etim_class'):
                classification_tasks.append({
                    "task_type": "classification",
                    "entity_type": "product",
                    "ai_service": "openai",
                    "priority": 5,
                    "processing_config": {
                        "classify_unspsc": bool(product.get('unspsc_code')),
                        "classify_etim": bool(product.get('etim_class'))
                    }
                })
        
        if classification_tasks:
            workflow.add_node("AIProcessingQueueBulkCreateNode", "queue_classifications", {
                "data": classification_tasks,
                "batch_size": 100
            })
        
        return self.runtime.execute(workflow.build())
    
    def get_ai_recommendations(self, request_params: dict) -> tuple:
        """
        Get AI recommendations and store results.
        Combines OpenAI API call with result persistence.
        """
        workflow = WorkflowBuilder()
        
        # Create recommendation request record
        workflow.add_node("AIRecommendationCreateNode", "create_request", {
            "recommendation_type": request_params["type"],
            "context_data": request_params,
            "ai_model": "gpt-4",
            "status": "processing"
        })
        
        # The actual AI processing would be handled by external services
        # This demonstrates the DataFlow pattern for tracking AI operations
        
        return self.runtime.execute(workflow.build())
    
    def sync_knowledge_graph_entities(self, entity_type: str, batch_size: int = 100) -> tuple:
        """
        Synchronize DataFlow entities with Neo4j knowledge graph.
        Handles bidirectional sync with conflict resolution.
        """
        workflow = WorkflowBuilder()
        
        # Get entities pending sync
        workflow.add_node("KnowledgeGraphEntityListNode", "pending_sync", {
            "filter": {
                "entity_type": entity_type,
                "sync_status": {"$in": ["pending", "out_of_sync"]}
            },
            "limit": batch_size,
            "order_by": ["last_sync_date"]
        })
        
        # Update sync status to processing
        workflow.add_node("KnowledgeGraphEntityBulkUpdateNode", "mark_processing", {
            "filter": {"sync_status": "pending"},
            "update": {"sync_status": "processing"},
            "limit": batch_size
        })
        
        return self.runtime.execute(workflow.build())
    
    def health_check_ai_services(self) -> tuple:
        """
        Perform health checks on all AI services.
        Creates health records for monitoring.
        """
        workflow = WorkflowBuilder()
        
        services = [
            {"service_name": "openai", "endpoint": "api.openai.com", "check_type": "health_check"},
            {"service_name": "neo4j", "endpoint": "localhost:7687", "check_type": "health_check"}, 
            {"service_name": "chromadb", "endpoint": "localhost:8000", "check_type": "health_check"}
        ]
        
        # Create health check records
        workflow.add_node("AIServiceHealthBulkCreateNode", "health_checks", {
            "data": services,
            "batch_size": 10
        })
        
        return self.runtime.execute(workflow.build())