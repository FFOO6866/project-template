"""
PostgreSQL Database Implementation using DataFlow
Replaces SQLite with production-ready PostgreSQL
"""

import os
import logging
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
import json
from datetime import datetime

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
from src.models.production_models import db

logger = logging.getLogger(__name__)

class PostgreSQLDatabase:
    """PostgreSQL database operations using DataFlow"""
    
    def __init__(self, database_url: str = None):
        """
        Initialize with database URL from environment.

        PRODUCTION REQUIREMENT:
        - DATABASE_URL must be set in environment (NO defaults)
        - Use Docker service name 'postgres' in production
        - Example: postgresql://user:pass@postgres:5432/dbname

        Raises:
            ValueError: If DATABASE_URL is not configured in production
        """
        # Get environment to determine if this is production
        environment = os.getenv('ENVIRONMENT', 'development').lower()

        # Get database URL from environment or parameter
        self.database_url = database_url or os.getenv('DATABASE_URL')

        # CRITICAL: Fail fast if DATABASE_URL not configured
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL environment variable is required. "
                "Set DATABASE_URL=postgresql://user:password@postgres:5432/dbname"
            )

        # CRITICAL: Block localhost in production
        if environment == 'production' and 'localhost' in self.database_url.lower():
            raise ValueError(
                "DATABASE_URL cannot contain 'localhost' in production environment. "
                "Use Docker service name 'postgres' instead: "
                "postgresql://user:password@postgres:5432/dbname"
            )
        
        self.runtime = LocalRuntime()
        self.connection_pool = None
        self.schema_initialized = False
        self._initialize_connection_pool()
        self._initialize_schema()
    
    def _initialize_connection_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=5,
                maxconn=20,
                dsn=self.database_url,
                application_name="horme_pov"
            )
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def _initialize_schema(self):
        """Initialize PostgreSQL schema using DataFlow auto-migration"""
        if self.schema_initialized:
            return
        
        try:
            # Initialize DataFlow with PostgreSQL
            logger.info("Initializing DataFlow schema in PostgreSQL...")
            
            # Set database URL for DataFlow
            os.environ['DATABASE_URL'] = self.database_url
            
            # Initialize schema using auto-migration
            db.initialize()
            
            logger.info("✅ PostgreSQL schema initialized with DataFlow auto-migration")
            self.schema_initialized = True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize PostgreSQL schema: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                logger.info(f"Connected to PostgreSQL: {version}")
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise RuntimeError(f"Database connection test failed: {str(e)}") from e
    
    def import_products_from_excel(self, excel_path: str) -> bool:
        """Import products using DataFlow bulk operations"""
        try:
            import pandas as pd
            
            logger.info(f"Loading products from {excel_path}")
            df = pd.read_excel(excel_path)
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Rename columns to match DataFlow model
            column_mapping = {
                'Product SKU': 'sku',
                'Description': 'name',
                'Category': 'category_name',
                'Brand': 'brand_name',
                'CatalogueItemID': 'catalogue_item_id'
            }
            df = df.rename(columns=column_mapping)
            
            # Clean data
            for col in ['sku', 'name', 'category_name', 'brand_name']:
                df[col] = df[col].astype(str).str.strip()
            
            df['catalogue_item_id'] = df['catalogue_item_id'].where(pd.notnull(df['catalogue_item_id']), None)
            
            # Create unique categories first
            unique_categories = df['category_name'].unique()
            category_records = [
                {
                    'name': category,
                    'slug': category.lower().replace(' - ', '-').replace(' ', '-'),
                    'is_active': True,
                    'created_at': datetime.now()
                }
                for category in unique_categories
            ]
            
            # Create unique brands
            unique_brands = df['brand_name'].unique()
            brand_records = [
                {
                    'name': brand,
                    'slug': brand.lower().replace(' ', '-'),
                    'is_active': True,
                    'created_at': datetime.now()
                }
                for brand in unique_brands
            ]
            
            # Use DataFlow to create categories
            if category_records:
                workflow = WorkflowBuilder()
                workflow.add_node("CategoryBulkCreateNode", "create_categories", {
                    "data": category_records,
                    "batch_size": 100,
                    "conflict_resolution": "skip"
                })
                self.runtime.execute(workflow.build())
                logger.info(f"Created {len(category_records)} categories")
            
            # Use DataFlow to create brands
            if brand_records:
                workflow = WorkflowBuilder()
                workflow.add_node("BrandBulkCreateNode", "create_brands", {
                    "data": brand_records,
                    "batch_size": 100,
                    "conflict_resolution": "skip"
                })
                self.runtime.execute(workflow.build())
                logger.info(f"Created {len(brand_records)} brands")
            
            # Now get the category and brand IDs from database
            category_map = self._get_category_map()
            brand_map = self._get_brand_map()
            
            # Create product records
            product_records = []
            batch_size = 500
            
            for _, row in df.iterrows():
                record = {
                    'sku': row['sku'],
                    'name': row['name'],
                    'slug': row['sku'].lower().replace(' ', '-'),
                    'description': row['name'],  # Use name as description initially
                    'category_id': category_map.get(row['category_name']),
                    'brand_id': brand_map.get(row['brand_name']),
                    'catalogue_item_id': row['catalogue_item_id'],
                    'status': 'active',
                    'is_published': True,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                product_records.append(record)
                
                # Process in batches
                if len(product_records) >= batch_size:
                    self._create_products_batch(product_records)
                    product_records = []
            
            # Process remaining products
            if product_records:
                self._create_products_batch(product_records)
            
            return True
            
        except ImportError:
            logger.error("pandas is required for Excel import. Install with: pip install pandas openpyxl")
            return False
        except Exception as e:
            logger.error(f"Failed to import from Excel: {e}")
            raise RuntimeError(f"Excel import failed: {str(e)}") from e
    
    def _get_category_map(self) -> Dict[str, int]:
        """Get category name to ID mapping"""
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("CategoryListNode", "get_categories", {})
            results, run_id = self.runtime.execute(workflow.build())
            
            categories = results.get("get_categories", [])
            return {cat['name']: cat['id'] for cat in categories}
        except Exception as e:
            logger.error(f"Failed to get category map: {e}")
            raise RuntimeError(f"Failed to retrieve category mapping: {str(e)}") from e
    
    def _get_brand_map(self) -> Dict[str, int]:
        """Get brand name to ID mapping"""
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("BrandListNode", "get_brands", {})
            results, run_id = self.runtime.execute(workflow.build())
            
            brands = results.get("get_brands", [])
            return {brand['name']: brand['id'] for brand in brands}
        except Exception as e:
            logger.error(f"Failed to get brand map: {e}")
            raise RuntimeError(f"Failed to retrieve brand mapping: {str(e)}") from e
    
    def _create_products_batch(self, product_records: List[Dict]) -> bool:
        """Create products in batch using DataFlow"""
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("ProductBulkCreateNode", "create_products", {
                "data": product_records,
                "batch_size": len(product_records),
                "conflict_resolution": "skip"
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            logger.info(f"Created batch of {len(product_records)} products")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create products batch: {e}")
            raise RuntimeError(f"Batch product creation failed: {str(e)}") from e
    
    def search_products(self, query: str, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Search products using DataFlow"""
        try:
            search_filter = {}
            
            if query:
                # Use DataFlow MongoDB-style query
                search_filter = {
                    "$or": [
                        {"name": {"$regex": query, "$options": "i"}},
                        {"description": {"$regex": query, "$options": "i"}},
                        {"sku": {"$regex": query, "$options": "i"}}
                    ]
                }
            
            if filters:
                if 'category' in filters:
                    search_filter["category_id"] = filters['category']
                if 'brand' in filters:
                    search_filter["brand_id"] = filters['brand']
                if 'status' in filters:
                    search_filter["status"] = filters['status']
            
            workflow = WorkflowBuilder()
            workflow.add_node("ProductListNode", "search_products", {
                "filter": search_filter,
                "limit": limit,
                "order_by": ["name"]
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            return results.get("search_products", [])
            
        except Exception as e:
            logger.error(f"Product search failed: {e}")
            raise
    
    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        """Get single product by SKU using DataFlow"""
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("ProductListNode", "get_by_sku", {
                "filter": {"sku": sku},
                "limit": 1
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            products = results.get("get_by_sku", [])
            
            return products[0] if products else None
            
        except Exception as e:
            logger.error(f"Failed to get product by SKU {sku}: {e}")
            raise RuntimeError(f"Failed to retrieve product {sku}: {str(e)}") from e
    
    def get_products_by_work_type(self, work_type: str, limit: int = 50) -> List[Dict]:
        """Get products recommended for specific work type"""
        # Work type to category mapping
        work_mappings = {
            'cleaning': ['05 - Cleaning Products'],
            'safety': ['21 - Safety Products'], 
            'tools': ['18 - Tools'],
            'cement work': ['18 - Tools'],
            'construction': ['18 - Tools', '21 - Safety Products'],
            'maintenance': ['05 - Cleaning Products', '18 - Tools']
        }
        
        categories = work_mappings.get(work_type.lower(), [])
        if not categories:
            return self.search_products(work_type, limit=limit)
        
        try:
            # First get category IDs
            category_map = self._get_category_map()
            category_ids = [category_map.get(cat) for cat in categories if category_map.get(cat)]
            
            if not category_ids:
                return self.search_products(work_type, limit=limit)
            
            workflow = WorkflowBuilder()
            workflow.add_node("ProductListNode", "get_by_work_type", {
                "filter": {"category_id": {"$in": category_ids}},
                "limit": limit,
                "order_by": ["brand_id", "name"]
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            return results.get("get_by_work_type", [])
            
        except Exception as e:
            logger.error(f"Failed to get products for work type {work_type}: {e}")
            raise
    
    def create_work_recommendation(self, title: str, description: str, 
                                 category: str, priority: str = "medium",
                                 related_products: List[int] = None) -> bool:
        """Create work recommendation using DataFlow"""
        try:
            record = {
                'title': title,
                'description': description,
                'category': category,
                'priority': priority,
                'status': 'open',
                'related_products': related_products or [],
                'recommendation_source': 'manual',
                'created_at': datetime.now()
            }
            
            workflow = WorkflowBuilder()
            workflow.add_node("WorkRecommendationCreateNode", "create_recommendation", record)
            
            results, run_id = self.runtime.execute(workflow.build())
            return True
            
        except Exception as e:
            logger.error(f"Failed to create work recommendation: {e}")
            raise RuntimeError(f"Work recommendation creation failed: {str(e)}") from e
    
    def get_work_recommendations(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get work recommendations using DataFlow"""
        try:
            search_filter = {}
            if status:
                search_filter["status"] = status
                
            workflow = WorkflowBuilder()
            workflow.add_node("WorkRecommendationListNode", "get_recommendations", {
                "filter": search_filter,
                "limit": limit,
                "order_by": ["-created_at"]
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            return results.get("get_recommendations", [])
            
        except Exception as e:
            logger.error(f"Failed to get work recommendations: {e}")
            raise
    
    def create_quotation(self, client_name: str, project_title: str,
                        line_items: List[Dict], total_amount: float,
                        currency: str = "USD") -> bool:
        """Create quotation using DataFlow"""
        try:
            # Generate quotation number
            import uuid
            quotation_number = f"QUO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            record = {
                'quotation_number': quotation_number,
                'client_name': client_name,
                'project_title': project_title,
                'total_amount': total_amount,
                'currency': currency,
                'status': 'draft',
                'line_items': line_items,
                'valid_until': datetime.now().replace(day=datetime.now().day + 30),  # 30 days validity
                'created_at': datetime.now()
            }
            
            workflow = WorkflowBuilder()
            workflow.add_node("QuotationCreateNode", "create_quotation", record)
            
            results, run_id = self.runtime.execute(workflow.build())
            return True
            
        except Exception as e:
            logger.error(f"Failed to create quotation: {e}")
            raise RuntimeError(f"Quotation creation failed: {str(e)}") from e
    
    def get_quotations(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get quotations using DataFlow"""
        try:
            search_filter = {}
            if status:
                search_filter["status"] = status
            
            workflow = WorkflowBuilder()
            workflow.add_node("QuotationListNode", "get_quotations", {
                "filter": search_filter,
                "limit": limit,
                "order_by": ["-created_at"]
            })
            
            results, run_id = self.runtime.execute(workflow.build())
            return results.get("get_quotations", [])
            
        except Exception as e:
            logger.error(f"Failed to get quotations: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics using DataFlow aggregation"""
        try:
            stats = {}

            # Total products
            workflow = WorkflowBuilder()
            workflow.add_node("ProductListNode", "count_products", {
                "filter": {},
                "limit": 1
            })
            results, run_id = self.runtime.execute(workflow.build())
            # Note: Need to implement count aggregation in DataFlow
            # For now, return basic info

            stats['database_type'] = 'PostgreSQL'
            stats['dataflow_models'] = [
                'Category', 'Brand', 'Supplier', 'Product', 'ProductPricing',
                'ProductSpecification', 'ProductInventory', 'WorkRecommendation',
                'RFPDocument', 'Quotation', 'QuotationItem', 'Customer', 'ActivityLog'
            ]
            stats['total_models'] = 13
            stats['generated_nodes'] = 13 * 9  # Each model generates 9 nodes

            return stats

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {'error': str(e)}

    # =========================================================================
    # Neo4j Knowledge Graph Integration
    # =========================================================================

    def sync_products_to_knowledge_graph(self, limit: int = None) -> Dict[str, Any]:
        """
        Sync products from PostgreSQL to Neo4j knowledge graph

        Args:
            limit: Optional limit for testing (syncs all if None)

        Returns:
            Dictionary with sync statistics
        """
        try:
            from src.core.neo4j_knowledge_graph import get_knowledge_graph

            # Get knowledge graph instance
            kg = get_knowledge_graph()

            # Test connection
            if not kg.test_connection():
                logger.error("❌ Neo4j connection failed")
                return {
                    "status": "error",
                    "error": "Neo4j connection failed"
                }

            # Get all products from PostgreSQL
            logger.info("Fetching products from PostgreSQL...")
            workflow = WorkflowBuilder()
            workflow.add_node("ProductListNode", "get_all_products", {
                "filter": {"status": "active"},
                "limit": limit if limit else 10000,
                "order_by": ["id"]
            })

            results, run_id = self.runtime.execute(workflow.build())
            products = results.get("get_all_products", [])

            if not products:
                logger.warning("⚠️ No products found in PostgreSQL")
                return {
                    "status": "warning",
                    "message": "No products to sync",
                    "synced": 0
                }

            logger.info(f"Found {len(products)} products to sync")

            # Prepare product data for Neo4j
            neo4j_products = []
            for product in products:
                # Get category and brand names
                category_name = self._get_category_name(product.get('category_id'))
                brand_name = self._get_brand_name(product.get('brand_id'))

                neo4j_product = {
                    "id": product['id'],
                    "sku": product['sku'],
                    "name": product['name'],
                    "category": category_name or "Uncategorized",
                    "brand": brand_name or "Unknown",
                    "description": product.get('description', ''),
                    "keywords": product.get('keywords', '').split(',') if product.get('keywords') else []
                }
                neo4j_products.append(neo4j_product)

            # Bulk create in Neo4j
            logger.info("Syncing to Neo4j knowledge graph...")
            successful, failed = kg.bulk_create_products(neo4j_products)

            sync_result = {
                "status": "success",
                "total_products": len(products),
                "synced": successful,
                "failed": failed,
                "sync_percentage": round((successful / len(products)) * 100, 2) if products else 0
            }

            logger.info(f"✅ Sync complete: {successful}/{len(products)} products synced to Neo4j")
            return sync_result

        except ImportError:
            logger.error("❌ Neo4j knowledge graph module not available")
            return {
                "status": "error",
                "error": "Neo4j module not installed"
            }
        except Exception as e:
            logger.error(f"❌ Failed to sync products to knowledge graph: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _get_category_name(self, category_id: int) -> Optional[str]:
        """Get category name from ID"""
        if not category_id:
            return None
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("CategoryListNode", "get_category", {
                "filter": {"id": category_id},
                "limit": 1
            })
            results, run_id = self.runtime.execute(workflow.build())
            categories = results.get("get_category", [])
            return categories[0]['name'] if categories else None
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve category name for ID {category_id}: {str(e)}") from e

    def _get_brand_name(self, brand_id: int) -> Optional[str]:
        """Get brand name from ID"""
        if not brand_id:
            return None
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("BrandListNode", "get_brand", {
                "filter": {"id": brand_id},
                "limit": 1
            })
            results, run_id = self.runtime.execute(workflow.build())
            brands = results.get("get_brand", [])
            return brands[0]['name'] if brands else None
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve brand name for ID {brand_id}: {str(e)}") from e

    def get_knowledge_graph_recommendations(
        self,
        task_description: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get product recommendations from Neo4j knowledge graph based on task description

        Args:
            task_description: Description of the DIY task
            limit: Maximum number of recommendations

        Returns:
            List of recommended products with relationship context
        """
        try:
            from src.core.neo4j_knowledge_graph import get_knowledge_graph

            kg = get_knowledge_graph()

            # For initial implementation, use full-text search on product nodes
            # This will be enhanced with task-to-product relationships in Phase 3

            # Extract keywords from task description
            keywords = task_description.lower().split()

            # Search products by keywords (temporary until tasks are loaded)
            products = []
            for keyword in keywords[:5]:  # Limit to first 5 keywords
                search_results = self.search_products(keyword, limit=5)
                products.extend(search_results)

            # Remove duplicates and limit
            unique_products = []
            seen_ids = set()
            for product in products:
                if product['id'] not in seen_ids:
                    unique_products.append(product)
                    seen_ids.add(product['id'])
                if len(unique_products) >= limit:
                    break

            logger.info(
                f"Found {len(unique_products)} knowledge graph recommendations "
                f"for task: {task_description[:50]}..."
            )

            return unique_products

        except ImportError:
            logger.warning("⚠️ Neo4j knowledge graph not available, using PostgreSQL search")
            return self.search_products(task_description, limit=limit)
        except Exception as e:
            logger.error(f"❌ Knowledge graph recommendation failed: {e}")
            raise

    # =========================================================================
    # Product Classification Integration (Phase 2)
    # =========================================================================

    def classify_product(
        self,
        product_id: int,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Classify product with UNSPSC and ETIM codes

        Args:
            product_id: Product ID to classify
            use_cache: Whether to use Redis cache

        Returns:
            Classification result dictionary or None
        """
        try:
            from src.core.product_classifier import get_classifier

            # Get product details
            workflow = WorkflowBuilder()
            workflow.add_node("ProductListNode", "get_product", {
                "filter": {"id": product_id},
                "limit": 1
            })

            results, run_id = self.runtime.execute(workflow.build())
            products = results.get("get_product", [])

            if not products:
                logger.warning(f"Product {product_id} not found")
                return None

            product = products[0]

            # Get category and brand names for richer classification
            category_name = self._get_category_name(product.get('category_id'))
            brand_name = self._get_brand_name(product.get('brand_id'))

            # Classify with product classifier
            classifier = get_classifier()
            result = classifier.classify_product(
                product_id=product['id'],
                product_sku=product['sku'],
                product_name=product['name'],
                product_description=product.get('description', ''),
                product_category=category_name or '',
                use_cache=use_cache
            )

            # Store classification in database
            if result.unspsc_code or result.etim_class:
                self._save_product_classification(result)

            return {
                'product_id': result.product_id,
                'product_sku': result.product_sku,
                'product_name': result.product_name,
                'unspsc': {
                    'code': result.unspsc_code,
                    'title': result.unspsc_title,
                    'level': result.unspsc_level,
                    'confidence': result.unspsc_confidence,
                    'hierarchy': result.unspsc_hierarchy
                },
                'etim': {
                    'class': result.etim_class,
                    'description': result.etim_description,
                    'version': result.etim_version,
                    'confidence': result.etim_confidence,
                    'features': result.etim_features
                },
                'processing_time_ms': result.processing_time_ms,
                'cache_hit': result.cache_hit,
                'classification_date': result.classification_date.isoformat()
            }

        except ImportError:
            logger.error("Product classifier module not available")
            return None
        except Exception as e:
            logger.error(f"Failed to classify product {product_id}: {e}")
            raise RuntimeError(f"Product classification failed for product {product_id}: {str(e)}") from e

    def classify_products_batch(
        self,
        product_ids: List[int],
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Classify multiple products in batch

        Args:
            product_ids: List of product IDs to classify
            use_cache: Whether to use Redis cache

        Returns:
            List of classification result dictionaries
        """
        try:
            from src.core.product_classifier import get_classifier

            # Get products
            workflow = WorkflowBuilder()
            workflow.add_node("ProductListNode", "get_products", {
                "filter": {"id": {"$in": product_ids}},
                "limit": len(product_ids)
            })

            results, run_id = self.runtime.execute(workflow.build())
            products = results.get("get_products", [])

            if not products:
                logger.warning("No products found for batch classification")
                return []

            # Enrich with category and brand names
            enriched_products = []
            for product in products:
                category_name = self._get_category_name(product.get('category_id'))
                brand_name = self._get_brand_name(product.get('brand_id'))

                enriched_products.append({
                    'id': product['id'],
                    'sku': product['sku'],
                    'name': product['name'],
                    'description': product.get('description', ''),
                    'category': category_name or '',
                    'brand': brand_name or ''
                })

            # Classify batch
            classifier = get_classifier()
            classification_results = classifier.classify_products_batch(
                enriched_products,
                use_cache=use_cache
            )

            # Store classifications and format results
            formatted_results = []
            for result in classification_results:
                if result.unspsc_code or result.etim_class:
                    self._save_product_classification(result)

                formatted_results.append({
                    'product_id': result.product_id,
                    'product_sku': result.product_sku,
                    'product_name': result.product_name,
                    'unspsc': {
                        'code': result.unspsc_code,
                        'title': result.unspsc_title,
                        'confidence': result.unspsc_confidence
                    },
                    'etim': {
                        'class': result.etim_class,
                        'description': result.etim_description,
                        'confidence': result.etim_confidence
                    },
                    'processing_time_ms': result.processing_time_ms,
                    'cache_hit': result.cache_hit
                })

            return formatted_results

        except ImportError as e:
            logger.error(f"Product classifier module not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Batch classification failed: {e}")
            raise

    def _save_product_classification(self, result) -> bool:
        """
        Save classification result to database

        Args:
            result: ClassificationResult object

        Returns:
            True if successful, False otherwise
        """
        try:
            # Store classification in ProductClassification table
            classification_record = {
                'product_id': result.product_id,
                'unspsc_code': result.unspsc_code,
                'unspsc_title': result.unspsc_title,
                'unspsc_confidence': result.unspsc_confidence,
                'unspsc_hierarchy': result.unspsc_hierarchy,
                'etim_class': result.etim_class,
                'etim_description': result.etim_description,
                'etim_version': result.etim_version,
                'etim_confidence': result.etim_confidence,
                'etim_features': result.etim_features,
                'classification_date': result.classification_date,
                'classification_method': result.classification_method,
                'processing_time_ms': result.processing_time_ms
            }

            workflow = WorkflowBuilder()
            workflow.add_node(
                "ProductClassificationCreateNode",
                "save_classification",
                classification_record
            )

            self.runtime.execute(workflow.build())
            logger.debug(f"Saved classification for product {result.product_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save classification: {e}")
            raise RuntimeError(f"Failed to save product classification: {str(e)}") from e

    def get_products_by_unspsc(
        self,
        unspsc_code: str,
        level: str = "commodity",
        limit: int = 50
    ) -> List[Dict]:
        """
        Get products by UNSPSC classification code

        Args:
            unspsc_code: UNSPSC code (can be partial for higher levels)
            level: Classification level (segment, family, class, commodity)
            limit: Maximum number of results

        Returns:
            List of products matching the UNSPSC code
        """
        try:
            # Query products by UNSPSC code using pattern matching
            workflow = WorkflowBuilder()
            workflow.add_node("ProductClassificationListNode", "get_by_unspsc", {
                "filter": {"unspsc_code": {"$regex": f"^{unspsc_code}"}},
                "limit": limit,
                "order_by": ["-unspsc_confidence"]
            })

            results, run_id = self.runtime.execute(workflow.build())
            classifications = results.get("get_by_unspsc", [])

            # Get full product details
            product_ids = [c['product_id'] for c in classifications]
            if not product_ids:
                return []

            workflow = WorkflowBuilder()
            workflow.add_node("ProductListNode", "get_products", {
                "filter": {"id": {"$in": product_ids}},
                "limit": limit
            })

            results, run_id = self.runtime.execute(workflow.build())
            return results.get("get_products", [])

        except Exception as e:
            logger.error(f"Failed to get products by UNSPSC {unspsc_code}: {e}")
            raise

    def get_products_by_etim(
        self,
        etim_class: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get products by ETIM classification

        Args:
            etim_class: ETIM class code (e.g., "EC000001")
            limit: Maximum number of results

        Returns:
            List of products matching the ETIM class
        """
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("ProductClassificationListNode", "get_by_etim", {
                "filter": {"etim_class": etim_class},
                "limit": limit,
                "order_by": ["-etim_confidence"]
            })

            results, run_id = self.runtime.execute(workflow.build())
            classifications = results.get("get_by_etim", [])

            # Get full product details
            product_ids = [c['product_id'] for c in classifications]
            if not product_ids:
                return []

            workflow = WorkflowBuilder()
            workflow.add_node("ProductListNode", "get_products", {
                "filter": {"id": {"$in": product_ids}},
                "limit": limit
            })

            results, run_id = self.runtime.execute(workflow.build())
            return results.get("get_products", [])

        except Exception as e:
            logger.error(f"Failed to get products by ETIM {etim_class}: {e}")
            raise

    # =========================================================================
    # Multi-lingual Translation Support (Phase 5)
    # =========================================================================

    def translate_product(
        self,
        product_id: int,
        target_lang: str,
        source_lang: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Translate product name and description to target language

        Args:
            product_id: Product ID to translate
            target_lang: Target language code (e.g., 'zh', 'ms', 'ta')
            source_lang: Source language code (auto-detected if None)

        Returns:
            Dictionary with translated product data or None
        """
        try:
            from src.translation import get_translation_service

            # Get product details
            workflow = WorkflowBuilder()
            workflow.add_node("ProductListNode", "get_product", {
                "filter": {"id": product_id},
                "limit": 1
            })

            results, run_id = self.runtime.execute(workflow.build())
            products = results.get("get_product", [])

            if not products:
                logger.warning(f"Product {product_id} not found")
                return None

            product = products[0]

            # Translate product using translation service
            translator = get_translation_service()
            translation_result = translator.translate_product(
                product_name=product['name'],
                product_description=product.get('description', ''),
                target_lang=target_lang,
                source_lang=source_lang
            )

            return {
                'product_id': product['id'],
                'sku': product['sku'],
                'original': {
                    'name': product['name'],
                    'description': product.get('description', '')
                },
                'translated': {
                    'name': translation_result['name'].translated_text,
                    'description': translation_result['description'].translated_text
                },
                'translation_metadata': {
                    'source_language': translation_result['name'].source_language,
                    'target_language': target_lang,
                    'name_confidence': translation_result['name'].confidence,
                    'description_confidence': translation_result['description'].confidence,
                    'cache_hit': translation_result['name'].cache_hit,
                    'processing_time_ms': (
                        translation_result['name'].processing_time_ms +
                        translation_result['description'].processing_time_ms
                    )
                }
            }

        except ImportError:
            logger.error("Translation service not available")
            return None
        except Exception as e:
            logger.error(f"Failed to translate product {product_id}: {e}")
            raise RuntimeError(f"Product translation failed for product {product_id}: {str(e)}") from e

    def translate_description(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        context: str = 'product'
    ) -> Optional[Dict[str, Any]]:
        """
        Translate product description or text to target language

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code (auto-detected if None)
            context: Context for translation ('product', 'technical', etc.)

        Returns:
            Translation result dictionary or None
        """
        try:
            from src.translation import get_translation_service

            translator = get_translation_service()
            result = translator.translate(
                text=text,
                target_lang=target_lang,
                source_lang=source_lang,
                context=context,
                preserve_technical=True
            )

            return {
                'original_text': result.original_text,
                'translated_text': result.translated_text,
                'source_language': result.source_language,
                'target_language': result.target_language,
                'confidence': result.confidence,
                'translation_method': result.translation_method,
                'technical_terms_preserved': result.technical_terms_preserved,
                'cache_hit': result.cache_hit,
                'processing_time_ms': result.processing_time_ms
            }

        except ImportError:
            logger.error("Translation service not available")
            return None
        except Exception as e:
            logger.error(f"Failed to translate text: {e}")
            raise RuntimeError(f"Text translation failed: {str(e)}") from e

    def get_multilingual_products(
        self,
        query: str,
        target_lang: str,
        filters: Dict = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search products and return with translations

        Args:
            query: Search query
            target_lang: Target language for translation
            filters: Optional filters
            limit: Maximum results

        Returns:
            List of products with translations
        """
        try:
            from src.translation import get_translation_service

            # Search products
            products = self.search_products(query, filters, limit)

            if not products:
                return []

            # Translate each product
            translator = get_translation_service()
            multilingual_products = []

            for product in products:
                try:
                    translation_result = translator.translate_product(
                        product_name=product['name'],
                        product_description=product.get('description', ''),
                        target_lang=target_lang
                    )

                    multilingual_product = {
                        **product,
                        'translations': {
                            target_lang: {
                                'name': translation_result['name'].translated_text,
                                'description': translation_result['description'].translated_text
                            }
                        }
                    }
                    multilingual_products.append(multilingual_product)

                except Exception as e:
                    logger.warning(f"Failed to translate product {product.get('sku')}: {e}")
                    multilingual_products.append(product)

            return multilingual_products

        except ImportError as e:
            logger.error(f"Translation service not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Multilingual product search failed: {e}")
            raise

    def close(self):
        """Close connection pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("PostgreSQL connection pool closed")

# Global database instance
_db_instance = None

def get_database(database_url: str = None) -> PostgreSQLDatabase:
    """Get global PostgreSQL database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = PostgreSQLDatabase(database_url)
    return _db_instance

def close_database():
    """Close global database instance"""
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None