"""
Comprehensive PostgreSQL database schema for Horme product knowledge base using Kailash DataFlow.

This module defines the complete data model for managing product information, including:
- Products with rich metadata and specifications
- Categories and brand hierarchies
- Images and media assets
- Supplier relationships
- Audit trails and source tracking
- Support for enriched data from web scraping

Features:
- Auto-generated CRUD nodes for each model (9 nodes per model)
- Enterprise-grade multi-tenancy support
- Built-in audit logging and soft deletes
- Optimized indexing for search and SKU lookups
- PostgreSQL-specific optimizations (JSONB, GIN indexes)
- Full-text search capabilities
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from dataflow import DataFlow

# Initialize DataFlow with PostgreSQL-specific optimizations
db = DataFlow(
    # Uses environment variable DATABASE_URL if not specified
    pool_size=20,              # Connection pool for high performance
    pool_max_overflow=30,      # Extra connections during peaks
    pool_recycle=3600,         # Recycle connections every hour
    monitoring=True,           # Enable performance monitoring
    echo=False,               # Disable SQL logging in production
    auto_migrate=True         # Enable automatic schema migrations
)

@db.model
class Category:
    """
    Product categories with hierarchical structure.
    
    Automatically generates 9 node types:
    - CategoryCreateNode, CategoryReadNode, CategoryUpdateNode, CategoryDeleteNode
    - CategoryListNode (with MongoDB-style filtering)
    - CategoryBulkCreateNode, CategoryBulkUpdateNode, CategoryBulkDeleteNode, CategoryBulkUpsertNode
    """
    name: str                          # Category name (e.g., "Laptops")
    slug: str                          # URL-friendly identifier (e.g., "laptops")
    description: Optional[str] = None  # Category description
    parent_id: Optional[int] = None    # Parent category for hierarchy
    level: int = 0                     # Depth in hierarchy (0 = root)
    path: Optional[str] = None         # Full path (e.g., "Electronics/Computers/Laptops")
    is_active: bool = True             # Category status
    sort_order: int = 0                # Display order within parent
    
    # Metadata for web scraping enrichment
    metadata: Optional[dict] = None    # Additional category data (JSONB)
    
    # Enterprise features
    __dataflow__ = {
        'multi_tenant': True,          # Adds tenant_id for SaaS applications
        'soft_delete': True,           # Adds deleted_at field
        'audit_log': True,             # Tracks all changes
        'versioned': True,             # Optimistic locking with version field
        'postgresql': {
            'jsonb_gin_indexes': ['metadata'],  # GIN index on JSONB metadata
            'text_search': ['name', 'description'],  # Full-text search
            'partial_indexes': [
                {'fields': ['parent_id'], 'condition': 'parent_id IS NOT NULL'},
                {'fields': ['slug'], 'condition': 'is_active = true'}
            ]
        }
    }
    
    # Performance indexes
    __indexes__ = [
        {'name': 'idx_category_slug_unique', 'fields': ['tenant_id', 'slug'], 'unique': True},
        {'name': 'idx_category_parent_level', 'fields': ['parent_id', 'level']},
        {'name': 'idx_category_active_sort', 'fields': ['is_active', 'sort_order']},
        {'name': 'idx_category_path', 'fields': ['path']}
    ]

@db.model
class Brand:
    """
    Product brands and manufacturers.
    
    Supports brand hierarchies (parent companies) and rich metadata.
    """
    name: str                          # Brand name (e.g., "Apple")
    slug: str                          # URL-friendly identifier
    description: Optional[str] = None  # Brand description
    logo_url: Optional[str] = None     # Brand logo image URL
    website_url: Optional[str] = None  # Official website
    country: Optional[str] = None      # Country of origin
    founded_year: Optional[int] = None # Year founded
    parent_brand_id: Optional[int] = None  # Parent company (e.g., Meta -> Facebook)
    is_active: bool = True             # Brand status
    
    # Web scraping metadata
    scraping_metadata: Optional[dict] = None  # Source URLs, last scraped, etc.
    
    # Enterprise features
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        'postgresql': {
            'jsonb_gin_indexes': ['scraping_metadata'],
            'text_search': ['name', 'description']
        }
    }
    
    __indexes__ = [
        {'name': 'idx_brand_slug_unique', 'fields': ['tenant_id', 'slug'], 'unique': True},
        {'name': 'idx_brand_name_search', 'fields': ['name']},
        {'name': 'idx_brand_parent', 'fields': ['parent_brand_id']},
        {'name': 'idx_brand_country', 'fields': ['country']}
    ]

@db.model
class Supplier:
    """
    Product suppliers and vendors.
    
    Manages supplier relationships and contact information.
    """
    name: str                          # Supplier name
    slug: str                          # URL-friendly identifier
    company_type: str = "distributor"  # distributor, manufacturer, retailer
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    address: Optional[str] = None      # Physical address
    country: Optional[str] = None
    
    # Business details
    business_license: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None  # e.g., "Net 30"
    
    # Relationship status
    is_active: bool = True
    is_preferred: bool = False         # Preferred supplier flag
    credit_rating: Optional[str] = None  # A, B, C, etc.
    
    # Metadata
    notes: Optional[str] = None
    supplier_metadata: Optional[dict] = None
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        'postgresql': {
            'jsonb_gin_indexes': ['supplier_metadata'],
            'text_search': ['name', 'notes']
        }
    }
    
    __indexes__ = [
        {'name': 'idx_supplier_slug_unique', 'fields': ['tenant_id', 'slug'], 'unique': True},
        {'name': 'idx_supplier_type_active', 'fields': ['company_type', 'is_active']},
        {'name': 'idx_supplier_preferred', 'fields': ['is_preferred']},
        {'name': 'idx_supplier_country', 'fields': ['country']}
    ]

@db.model
class Product:
    """
    Core product information with comprehensive metadata.
    
    Central model for product knowledge base with support for:
    - Multiple SKUs and identifiers
    - Rich specifications and attributes
    - Pricing and availability
    - Web scraping enrichment
    """
    # Core identifiers
    sku: str                           # Primary SKU (Stock Keeping Unit)
    name: str                          # Product name
    slug: str                          # URL-friendly identifier
    model_number: Optional[str] = None # Manufacturer model number
    upc: Optional[str] = None          # Universal Product Code
    ean: Optional[str] = None          # European Article Number
    isbn: Optional[str] = None         # For books
    
    # Basic information
    description: Optional[str] = None   # Short description
    long_description: Optional[str] = None  # Detailed description
    category_id: Optional[int] = None   # FK to Category
    brand_id: Optional[int] = None      # FK to Brand
    
    # Product status
    status: str = "active"             # active, inactive, discontinued
    is_published: bool = True          # Visibility status
    availability: str = "in_stock"     # in_stock, out_of_stock, preorder, discontinued
    
    # Pricing information
    price: Optional[float] = None      # Current price
    msrp: Optional[float] = None       # Manufacturer Suggested Retail Price
    cost: Optional[float] = None       # Cost basis
    currency: str = "USD"              # Price currency
    
    # Physical attributes
    weight: Optional[float] = None     # Weight in kg
    length: Optional[float] = None     # Length in cm
    width: Optional[float] = None      # Width in cm  
    height: Optional[float] = None     # Height in cm
    color: Optional[str] = None        # Primary color
    material: Optional[str] = None     # Primary material
    
    # Rich specifications (JSONB for flexibility)
    specifications: Optional[dict] = None  # Technical specifications
    features: Optional[List[str]] = None   # Key features list
    attributes: Optional[dict] = None      # Additional attributes
    
    # SEO and marketing
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: Optional[List[str]] = None   # Search keywords
    
    # Inventory tracking
    stock_quantity: Optional[int] = None
    min_stock_level: Optional[int] = None
    max_stock_level: Optional[int] = None
    
    # Web scraping enrichment data
    source_urls: Optional[List[str]] = None      # URLs where product was found
    scraping_metadata: Optional[dict] = None     # Scraping timestamps, confidence scores
    enriched_data: Optional[dict] = None         # AI-enhanced product data
    last_scraped_at: Optional[datetime] = None   # Last web scraping timestamp
    
    # Quality and ratings
    rating_average: Optional[float] = None       # Average rating (1-5)
    rating_count: Optional[int] = None          # Number of ratings
    review_count: Optional[int] = None          # Number of reviews
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True,
        'postgresql': {
            'jsonb_gin_indexes': ['specifications', 'attributes', 'scraping_metadata', 'enriched_data'],
            'text_search': ['name', 'description', 'long_description', 'model_number'],
            'partial_indexes': [
                {'fields': ['sku'], 'condition': 'status = \'active\''},
                {'fields': ['category_id'], 'condition': 'is_published = true'},
                {'fields': ['brand_id'], 'condition': 'is_published = true'}
            ]
        }
    }
    
    __indexes__ = [
        # Primary business indexes
        {'name': 'idx_product_sku_unique', 'fields': ['tenant_id', 'sku'], 'unique': True},
        {'name': 'idx_product_slug_unique', 'fields': ['tenant_id', 'slug'], 'unique': True},
        {'name': 'idx_product_model_brand', 'fields': ['model_number', 'brand_id']},
        
        # Search and filtering indexes
        {'name': 'idx_product_category_status', 'fields': ['category_id', 'status', 'is_published']},
        {'name': 'idx_product_brand_status', 'fields': ['brand_id', 'status', 'is_published']},
        {'name': 'idx_product_price_range', 'fields': ['price', 'currency']},
        {'name': 'idx_product_availability', 'fields': ['availability', 'is_published']},
        
        # Product codes for lookup
        {'name': 'idx_product_upc', 'fields': ['upc']},
        {'name': 'idx_product_ean', 'fields': ['ean']},
        {'name': 'idx_product_isbn', 'fields': ['isbn']},
        
        # Web scraping indexes
        {'name': 'idx_product_last_scraped', 'fields': ['last_scraped_at']},
        
        # Inventory and ratings
        {'name': 'idx_product_stock', 'fields': ['stock_quantity', 'availability']},
        {'name': 'idx_product_rating', 'fields': ['rating_average', 'rating_count']}
    ]

@db.model
class ProductImage:
    """
    Product images and media assets.
    
    Supports multiple images per product with metadata and ordering.
    """
    product_id: int                    # FK to Product
    url: str                          # Image URL or file path
    alt_text: Optional[str] = None    # Alt text for accessibility
    title: Optional[str] = None       # Image title
    
    # Image properties
    image_type: str = "photo"         # photo, diagram, screenshot, etc.
    position: int = 0                 # Display order (0 = primary)
    width: Optional[int] = None       # Image width in pixels
    height: Optional[int] = None      # Image height in pixels
    file_size: Optional[int] = None   # File size in bytes
    mime_type: Optional[str] = None   # MIME type (image/jpeg, etc.)
    
    # Source tracking
    source_url: Optional[str] = None  # Original source URL (for scraped images)
    is_primary: bool = False          # Primary product image flag
    is_active: bool = True            # Image status
    
    # AI-generated metadata
    ai_description: Optional[str] = None      # AI-generated image description
    ai_tags: Optional[List[str]] = None       # AI-extracted tags
    ai_confidence: Optional[float] = None     # AI confidence score
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'postgresql': {
            'jsonb_gin_indexes': ['ai_tags'],
            'text_search': ['alt_text', 'title', 'ai_description']
        }
    }
    
    __indexes__ = [
        {'name': 'idx_product_image_product', 'fields': ['product_id', 'is_active']},
        {'name': 'idx_product_image_position', 'fields': ['product_id', 'position']},
        {'name': 'idx_product_image_primary', 'fields': ['product_id', 'is_primary']},
        {'name': 'idx_product_image_type', 'fields': ['image_type', 'is_active']}
    ]

@db.model
class ProductSpecification:
    """
    Structured product specifications and technical details.
    
    Flexible key-value storage for product specifications with type safety.
    """
    product_id: int                   # FK to Product
    spec_group: str                   # Specification group (e.g., "Technical", "Physical")
    spec_name: str                    # Specification name (e.g., "Processor")
    spec_value: str                   # Specification value (e.g., "Intel i7-12700H")
    spec_unit: Optional[str] = None   # Unit of measurement (e.g., "GHz", "inches")
    
    # Data typing
    data_type: str = "text"           # text, number, boolean, date, list
    numeric_value: Optional[float] = None      # For numeric comparisons
    boolean_value: Optional[bool] = None       # For yes/no specifications
    date_value: Optional[datetime] = None      # For date specifications
    
    # Display and organization
    display_order: int = 0            # Order within spec_group
    is_key_spec: bool = False         # Important specification flag
    is_searchable: bool = True        # Include in search indexes
    is_comparable: bool = True        # Use in product comparisons
    
    # Source tracking
    source: str = "manual"            # manual, scraped, api, imported
    confidence: Optional[float] = None # Confidence in specification accuracy
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'postgresql': {
            'text_search': ['spec_name', 'spec_value']
        }
    }
    
    __indexes__ = [
        {'name': 'idx_product_spec_product', 'fields': ['product_id', 'spec_group']},
        {'name': 'idx_product_spec_name_value', 'fields': ['spec_name', 'spec_value']},
        {'name': 'idx_product_spec_searchable', 'fields': ['is_searchable', 'spec_name']},
        {'name': 'idx_product_spec_key', 'fields': ['product_id', 'is_key_spec']},
        {'name': 'idx_product_spec_numeric', 'fields': ['spec_name', 'numeric_value']},
        {'name': 'idx_product_spec_order', 'fields': ['product_id', 'spec_group', 'display_order']}
    ]

@db.model
class ProductSupplier:
    """
    Product-supplier relationships with pricing and availability.
    
    Many-to-many relationship between products and suppliers.
    """
    product_id: int                   # FK to Product
    supplier_id: int                  # FK to Supplier
    
    # Supplier-specific product info
    supplier_sku: Optional[str] = None        # Supplier's SKU for this product
    supplier_name: Optional[str] = None       # Supplier's name for this product
    supplier_description: Optional[str] = None
    
    # Pricing and terms
    supplier_price: Optional[float] = None    # Supplier's price
    currency: str = "USD"
    minimum_order_qty: Optional[int] = None   # Minimum order quantity
    lead_time_days: Optional[int] = None      # Lead time in days
    
    # Availability
    is_available: bool = True
    stock_status: str = "available"           # available, limited, out_of_stock
    last_updated: Optional[datetime] = None   # Last price/availability update
    
    # Relationship status
    is_preferred: bool = False                # Preferred supplier for this product
    is_active: bool = True
    
    # Performance metrics
    reliability_score: Optional[float] = None # 0-100 reliability score
    quality_score: Optional[float] = None     # 0-100 quality score
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'versioned': True
    }
    
    __indexes__ = [
        {'name': 'idx_product_supplier_unique', 'fields': ['product_id', 'supplier_id'], 'unique': True},
        {'name': 'idx_product_supplier_sku', 'fields': ['supplier_id', 'supplier_sku']},
        {'name': 'idx_product_supplier_price', 'fields': ['product_id', 'supplier_price']},
        {'name': 'idx_product_supplier_preferred', 'fields': ['product_id', 'is_preferred']},
        {'name': 'idx_product_supplier_available', 'fields': ['supplier_id', 'is_available', 'stock_status']}
    ]

@db.model
class ScrapingJob:
    """
    Web scraping job tracking and metadata.
    
    Tracks web scraping operations for data enrichment.
    """
    job_name: str                     # Human-readable job name
    job_type: str                     # product_discovery, price_update, spec_enrichment
    target_url: str                   # URL being scraped
    target_domain: str                # Domain being scraped
    
    # Job status
    status: str = "pending"           # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results tracking
    products_found: Optional[int] = None      # Number of products discovered
    products_updated: Optional[int] = None    # Number of products updated
    errors_count: Optional[int] = None        # Number of errors encountered
    
    # Configuration
    scraping_config: Optional[dict] = None    # Scraping parameters (JSONB)
    user_agent: Optional[str] = None          # User agent used
    rate_limit: Optional[float] = None        # Requests per second limit
    
    # Results and errors
    results_summary: Optional[dict] = None    # Summary of results (JSONB)
    error_log: Optional[List[str]] = None     # Error messages
    
    # Scheduling
    is_recurring: bool = False
    cron_schedule: Optional[str] = None       # Cron expression for recurring jobs
    next_run_at: Optional[datetime] = None    # Next scheduled run
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'audit_log': True,
        'postgresql': {
            'jsonb_gin_indexes': ['scraping_config', 'results_summary'],
            'text_search': ['job_name', 'target_domain']
        }
    }
    
    __indexes__ = [
        {'name': 'idx_scraping_job_status', 'fields': ['status', 'started_at']},
        {'name': 'idx_scraping_job_domain', 'fields': ['target_domain', 'job_type']},
        {'name': 'idx_scraping_job_schedule', 'fields': ['is_recurring', 'next_run_at']},
        {'name': 'idx_scraping_job_completed', 'fields': ['completed_at', 'status']}
    ]

@db.model
class ProductAnalytics:
    """
    Product analytics and performance metrics.
    
    Aggregated data for business intelligence and reporting.
    """
    product_id: int                   # FK to Product
    date: datetime                    # Analytics date (daily aggregation)
    
    # View metrics
    page_views: int = 0               # Product page views
    unique_visitors: int = 0          # Unique visitors
    bounce_rate: Optional[float] = None       # Bounce rate percentage
    avg_time_on_page: Optional[float] = None  # Average time in seconds
    
    # Engagement metrics
    add_to_cart: int = 0              # Add to cart events
    add_to_wishlist: int = 0          # Add to wishlist events
    share_count: int = 0              # Social shares
    
    # Search metrics
    search_impressions: int = 0       # Times shown in search results
    search_clicks: int = 0            # Clicks from search results
    search_ctr: Optional[float] = None        # Click-through rate
    
    # Performance scores
    relevance_score: Optional[float] = None   # Search relevance score
    popularity_score: Optional[float] = None  # Overall popularity score
    trending_score: Optional[float] = None    # Trending indicator
    
    # Data aggregation metadata
    data_sources: Optional[List[str]] = None  # Sources of analytics data
    last_updated: Optional[datetime] = None   # Last update timestamp
    
    __dataflow__ = {
        'multi_tenant': True,
        'soft_delete': True,
        'postgresql': {
            'jsonb_gin_indexes': ['data_sources']
        }
    }
    
    __indexes__ = [
        {'name': 'idx_product_analytics_product_date', 'fields': ['product_id', 'date'], 'unique': True},
        {'name': 'idx_product_analytics_date', 'fields': ['date']},
        {'name': 'idx_product_analytics_views', 'fields': ['page_views', 'date']},
        {'name': 'idx_product_analytics_popularity', 'fields': ['popularity_score', 'date']},
        {'name': 'idx_product_analytics_trending', 'fields': ['trending_score', 'date']}
    ]

# Export all models for easy importing
__all__ = [
    'db',
    'Category',
    'Brand', 
    'Supplier',
    'Product',
    'ProductImage',
    'ProductSpecification',
    'ProductSupplier',
    'ScrapingJob',
    'ProductAnalytics'
]

# Model relationships summary for reference:
"""
Relationship Map:
- Product -> Category (many-to-one)
- Product -> Brand (many-to-one)
- Product -> ProductImage (one-to-many)
- Product -> ProductSpecification (one-to-many)
- Product -> ProductSupplier (many-to-many via ProductSupplier)
- Supplier -> ProductSupplier (one-to-many)
- Product -> ProductAnalytics (one-to-many)
- Category -> Category (self-referencing parent-child)
- Brand -> Brand (self-referencing parent-child)

Each model automatically generates 9 node types:
1. {Model}CreateNode - Single record creation
2. {Model}ReadNode - Single record retrieval
3. {Model}UpdateNode - Single record update
4. {Model}DeleteNode - Single record deletion
5. {Model}ListNode - Query with MongoDB-style filters
6. {Model}BulkCreateNode - Bulk record creation
7. {Model}BulkUpdateNode - Bulk record updates
8. {Model}BulkDeleteNode - Bulk record deletion
9. {Model}BulkUpsertNode - Bulk insert or update operations

Total: 9 models × 9 nodes = 81 auto-generated database operation nodes
"""