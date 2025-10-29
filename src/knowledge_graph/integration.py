"""
PostgreSQL to Neo4j Data Integration

This module handles the migration and synchronization of product data
from the existing PostgreSQL DataFlow system to the Neo4j knowledge graph.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import asyncpg
from dataclasses import asdict

from .database import Neo4jConnection, GraphDatabase
from .models import ProductNode, CategoryNode, BrandNode, ProjectNode, SemanticRelationship, RelationshipType, ConfidenceSource

logger = logging.getLogger(__name__)


class PostgreSQLIntegration:
    """
    Integration layer between PostgreSQL DataFlow and Neo4j Knowledge Graph.
    
    Handles data migration, synchronization, and bidirectional updates.
    """
    
    def __init__(
        self,
        postgres_url: str = None,
        neo4j_connection: Neo4jConnection = None,
        batch_size: int = 1000
    ):
        """
        Initialize PostgreSQL integration.
        
        Args:
            postgres_url: PostgreSQL connection URL
            neo4j_connection: Neo4j connection instance
            batch_size: Number of records to process in each batch
        """
        self.postgres_url = postgres_url or os.getenv(
            "POSTGRES_URL", 
            "postgresql://horme_user:horme_password_2024@localhost:5432/horme_database"
        )
        self.neo4j_conn = neo4j_connection or Neo4jConnection()
        self.graph_db = GraphDatabase(self.neo4j_conn)
        self.batch_size = batch_size
        
        # Connection pool for PostgreSQL
        self._pg_pool = None
        
    async def _get_pg_pool(self):
        """Get or create PostgreSQL connection pool"""
        if self._pg_pool is None:
            self._pg_pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
        return self._pg_pool
    
    async def close(self):
        """Close all database connections"""
        if self._pg_pool:
            await self._pg_pool.close()
        self.neo4j_conn.close()
    
    # ===========================================
    # DATA MIGRATION METHODS
    # ===========================================
    
    async def migrate_categories(self, force_refresh: bool = False) -> int:
        """
        Migrate category data from PostgreSQL to Neo4j.
        
        Args:
            force_refresh: If True, refresh all categories regardless of sync status
            
        Returns:
            Number of categories migrated
        """
        logger.info("Starting category migration...")
        
        pool = await self._get_pg_pool()
        
        # Build query with optional sync filter
        base_query = """
        SELECT category_id, name, slug, description, parent_id, level, path, 
               is_active, sort_order, created_at, updated_at
        FROM categories 
        WHERE is_active = true
        """
        
        if not force_refresh:
            # Only sync categories updated in last 24 hours or never synced
            sync_query = base_query + """
            AND (updated_at > NOW() - INTERVAL '24 hours' 
                 OR category_id NOT IN (
                     SELECT DISTINCT category_id 
                     FROM knowledge_graph_sync 
                     WHERE entity_type = 'category' AND synced_at > NOW() - INTERVAL '7 days'
                 ))
            """
        else:
            sync_query = base_query
        
        try:
            async with pool.acquire() as conn:
                # Fetch categories
                rows = await conn.fetch(sync_query)
                
                if not rows:
                    logger.info("No categories to migrate")
                    return 0
                
                # Convert to CategoryNode objects
                categories = []
                for row in rows:
                    category = CategoryNode(
                        category_id=row['category_id'],
                        name=row['name'],
                        slug=row['slug'],
                        description=row['description'],
                        parent_id=row['parent_id'],
                        level=row['level'] or 0,
                        path=row['path'],
                        is_active=row['is_active']
                    )
                    categories.append(category)
                
                # Bulk create in Neo4j
                migrated_count = 0
                for i in range(0, len(categories), self.batch_size):
                    batch = categories[i:i + self.batch_size]
                    batch_count = self.graph_db.bulk_create_nodes(batch)
                    migrated_count += batch_count
                    
                    # Update sync tracking
                    await self._update_sync_status(
                        conn, 
                        'category', 
                        [c.category_id for c in batch]
                    )
                
                # Create category hierarchy relationships
                await self._create_category_hierarchy(categories)
                
                logger.info(f"Migrated {migrated_count} categories")
                return migrated_count
                
        except Exception as e:
            logger.error(f"Category migration failed: {e}")
            return 0
    
    async def migrate_brands(self, force_refresh: bool = False) -> int:
        """
        Migrate brand data from PostgreSQL to Neo4j.
        
        Args:
            force_refresh: If True, refresh all brands regardless of sync status
            
        Returns:
            Number of brands migrated
        """
        logger.info("Starting brand migration...")
        
        pool = await self._get_pg_pool()
        
        base_query = """
        SELECT brand_id, name, slug, description, logo_url, website_url, 
               country, founded_year, parent_brand_id, is_active,
               created_at, updated_at
        FROM brands 
        WHERE is_active = true
        """
        
        if not force_refresh:
            sync_query = base_query + """
            AND (updated_at > NOW() - INTERVAL '24 hours' 
                 OR brand_id NOT IN (
                     SELECT DISTINCT entity_id::integer 
                     FROM knowledge_graph_sync 
                     WHERE entity_type = 'brand' AND synced_at > NOW() - INTERVAL '7 days'
                 ))
            """
        else:
            sync_query = base_query
        
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(sync_query)
                
                if not rows:
                    logger.info("No brands to migrate")
                    return 0
                
                # Convert to BrandNode objects
                brands = []
                for row in rows:
                    brand = BrandNode(
                        brand_id=row['brand_id'],
                        name=row['name'],
                        slug=row['slug'],
                        country=row['country'],
                        parent_brand_id=row['parent_brand_id'],
                        is_active=row['is_active'],
                        website_url=row['website_url']
                    )
                    brands.append(brand)
                
                # Bulk create in Neo4j
                migrated_count = 0
                for i in range(0, len(brands), self.batch_size):
                    batch = brands[i:i + self.batch_size]
                    batch_count = self.graph_db.bulk_create_nodes(batch)
                    migrated_count += batch_count
                    
                    # Update sync tracking
                    await self._update_sync_status(
                        conn, 
                        'brand', 
                        [b.brand_id for b in batch]
                    )
                
                # Create brand hierarchy relationships
                await self._create_brand_hierarchy(brands)
                
                logger.info(f"Migrated {migrated_count} brands")
                return migrated_count
                
        except Exception as e:
            logger.error(f"Brand migration failed: {e}")
            return 0
    
    async def migrate_products(self, force_refresh: bool = False, limit: int = None) -> int:
        """
        Migrate product data from PostgreSQL to Neo4j.
        
        Args:
            force_refresh: If True, refresh all products regardless of sync status
            limit: Maximum number of products to migrate (for testing)
            
        Returns:
            Number of products migrated
        """
        logger.info("Starting product migration...")
        
        pool = await self._get_pg_pool()
        
        # Complex query to get product data with related information
        base_query = """
        SELECT p.product_id, p.sku, p.name, p.slug, p.model_number,
               p.description, p.long_description, p.price, p.currency,
               p.availability, p.is_published, p.status,
               p.weight, p.length, p.width, p.height, p.color, p.material,
               p.specifications, p.features, p.keywords,
               p.stock_quantity, p.rating_average, p.rating_count,
               p.created_at, p.updated_at,
               c.name as category_name, c.category_id,
               b.name as brand_name, b.brand_id
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN brands b ON p.brand_id = b.brand_id
        WHERE p.is_published = true AND p.status = 'active'
        """
        
        if not force_refresh:
            sync_query = base_query + """
            AND (p.updated_at > NOW() - INTERVAL '24 hours' 
                 OR p.product_id NOT IN (
                     SELECT DISTINCT entity_id::integer 
                     FROM knowledge_graph_sync 
                     WHERE entity_type = 'product' AND synced_at > NOW() - INTERVAL '7 days'
                 ))
            """
        else:
            sync_query = base_query
        
        if limit:
            sync_query += f" LIMIT {limit}"
        
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(sync_query)
                
                if not rows:
                    logger.info("No products to migrate")
                    return 0
                
                logger.info(f"Migrating {len(rows)} products...")
                
                # Convert to ProductNode objects
                products = []
                for row in rows:
                    # Handle dimensions
                    dimensions = None
                    if row['length'] or row['width'] or row['height']:
                        dimensions = {
                            'length': row['length'],
                            'width': row['width'], 
                            'height': row['height']
                        }
                    
                    product = ProductNode(
                        product_id=row['product_id'],
                        sku=row['sku'],
                        name=row['name'],
                        slug=row['slug'],
                        description=row['description'],
                        long_description=row['long_description'],
                        brand_name=row['brand_name'],
                        brand_id=row['brand_id'],
                        category_name=row['category_name'],
                        category_id=row['category_id'],
                        price=float(row['price']) if row['price'] else None,
                        currency=row['currency'] or 'USD',
                        availability=row['availability'] or 'unknown',
                        is_published=row['is_published'],
                        specifications=row['specifications'],
                        features=row['features'] or [],
                        keywords=row['keywords'] or [],
                        dimensions=dimensions,
                        weight=float(row['weight']) if row['weight'] else None,
                        material=row['material'],
                        color=row['color'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        last_sync_from_postgres=datetime.utcnow()
                    )
                    products.append(product)
                
                # Bulk create in Neo4j  
                migrated_count = 0
                for i in range(0, len(products), self.batch_size):
                    batch = products[i:i + self.batch_size]
                    batch_count = self.graph_db.bulk_create_nodes(batch)
                    migrated_count += batch_count
                    
                    # Update sync tracking
                    await self._update_sync_status(
                        conn, 
                        'product', 
                        [p.product_id for p in batch]
                    )
                    
                    logger.info(f"Migrated batch: {i + len(batch)}/{len(products)} products")
                
                # Create product-category and product-brand relationships
                await self._create_product_relationships(products)
                
                logger.info(f"Successfully migrated {migrated_count} products")
                return migrated_count
                
        except Exception as e:
            logger.error(f"Product migration failed: {e}")
            return 0
    
    async def migrate_all(self, force_refresh: bool = False) -> Dict[str, int]:
        """
        Migrate all data from PostgreSQL to Neo4j.
        
        Args:
            force_refresh: If True, refresh all data regardless of sync status
            
        Returns:
            Dictionary with migration counts by entity type
        """
        logger.info("Starting full data migration...")
        
        results = {}
        
        try:
            # Migrate in dependency order
            results['categories'] = await self.migrate_categories(force_refresh)
            results['brands'] = await self.migrate_brands(force_refresh)
            results['products'] = await self.migrate_products(force_refresh)
            
            # Initialize basic product relationships
            await self.infer_basic_relationships()
            
            logger.info(f"Migration completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Full migration failed: {e}")
            return results
    
    # ===========================================
    # RELATIONSHIP CREATION
    # ===========================================
    
    async def _create_category_hierarchy(self, categories: List[CategoryNode]):
        """Create parent-child relationships between categories"""
        logger.info("Creating category hierarchy relationships...")
        
        relationships = []
        for category in categories:
            if category.parent_id:
                rel = SemanticRelationship(
                    from_product_id=category.category_id,
                    to_product_id=category.parent_id,
                    relationship_type=RelationshipType.PART_OF_KIT,  # Reusing for hierarchy
                    confidence=1.0,
                    source=ConfidenceSource.MANUFACTURER_SPEC,
                    notes="Category hierarchy from PostgreSQL"
                )
                relationships.append(rel)
        
        # Create relationships in Neo4j using Cypher (more efficient for hierarchies)
        if relationships:
            query = """
            UNWIND $relationships as rel
            MATCH (child:Category {category_id: rel.child_id})
            MATCH (parent:Category {category_id: rel.parent_id})  
            MERGE (child)-[:PARENT_CATEGORY {
                confidence: 1.0,
                source: 'manufacturer_spec',
                created_at: datetime()
            }]->(parent)
            """
            
            rel_data = [
                {"child_id": r.from_product_id, "parent_id": r.to_product_id}
                for r in relationships
            ]
            
            with self.neo4j_conn.session() as session:
                session.run(query, {"relationships": rel_data})
            
            logger.info(f"Created {len(relationships)} category hierarchy relationships")
    
    async def _create_brand_hierarchy(self, brands: List[BrandNode]):
        """Create parent-child relationships between brands"""
        logger.info("Creating brand hierarchy relationships...")
        
        relationships = []
        for brand in brands:
            if brand.parent_brand_id:
                query = """
                MATCH (child:Brand {brand_id: $child_id})
                MATCH (parent:Brand {brand_id: $parent_id})
                MERGE (child)-[:PARENT_BRAND {
                    confidence: 1.0,
                    source: 'manufacturer_spec',
                    created_at: datetime()
                }]->(parent)
                """
                
                with self.neo4j_conn.session() as session:
                    session.run(query, {
                        "child_id": brand.brand_id,
                        "parent_id": brand.parent_brand_id
                    })
                    relationships.append(brand)
        
        logger.info(f"Created {len(relationships)} brand hierarchy relationships")
    
    async def _create_product_relationships(self, products: List[ProductNode]):
        """Create basic product relationships (category, brand)"""
        logger.info("Creating product-category and product-brand relationships...")
        
        # Create product -> category relationships
        category_rels = []
        brand_rels = []
        
        for product in products:
            if product.category_id:
                category_rels.append({
                    "product_id": product.product_id,
                    "category_id": product.category_id
                })
            
            if product.brand_id:
                brand_rels.append({
                    "product_id": product.product_id,
                    "brand_id": product.brand_id
                })
        
        # Batch create category relationships
        if category_rels:
            query = """
            UNWIND $relationships as rel
            MATCH (p:Product {product_id: rel.product_id})
            MATCH (c:Category {category_id: rel.category_id})
            MERGE (p)-[:BELONGS_TO_CATEGORY {
                confidence: 1.0,
                source: 'manufacturer_spec',
                created_at: datetime()
            }]->(c)
            """
            
            with self.neo4j_conn.session() as session:
                session.run(query, {"relationships": category_rels})
            
            logger.info(f"Created {len(category_rels)} product-category relationships")
        
        # Batch create brand relationships
        if brand_rels:
            query = """
            UNWIND $relationships as rel
            MATCH (p:Product {product_id: rel.product_id})
            MATCH (b:Brand {brand_id: rel.brand_id})
            MERGE (p)-[:MANUFACTURED_BY {
                confidence: 1.0,
                source: 'manufacturer_spec', 
                created_at: datetime()
            }]->(b)
            """
            
            with self.neo4j_conn.session() as session:
                session.run(query, {"relationships": brand_rels})
            
            logger.info(f"Created {len(brand_rels)} product-brand relationships")
    
    # ===========================================
    # BASIC RELATIONSHIP INFERENCE
    # ===========================================
    
    async def infer_basic_relationships(self):
        """Infer basic relationships based on product data"""
        logger.info("Starting basic relationship inference...")
        
        # Infer brand ecosystem relationships
        await self._infer_brand_ecosystem_relationships()
        
        # Infer category-based similarity
        await self._infer_category_similarity()
        
        # Infer specification-based compatibility (basic version)
        await self._infer_spec_compatibility()
    
    async def _infer_brand_ecosystem_relationships(self):
        """Infer relationships within brand ecosystems"""
        query = """
        MATCH (p1:Product)-[:MANUFACTURED_BY]->(b:Brand)<-[:MANUFACTURED_BY]-(p2:Product)
        WHERE p1.product_id < p2.product_id  // Avoid duplicates
        AND p1.brand_name = p2.brand_name
        MERGE (p1)-[:SAME_BRAND_ECOSYSTEM {
            confidence: 0.8,
            source: 'ai_inference',
            compatibility_type: 'brand_ecosystem',
            created_at: datetime(),
            notes: 'Same brand ecosystem - potential compatibility'
        }]->(p2)
        """
        
        with self.neo4j_conn.session() as session:
            result = session.run(query)
            summary = result.consume()
            logger.info(f"Created {summary.counters.relationships_created} brand ecosystem relationships")
    
    async def _infer_category_similarity(self):
        """Infer similarity relationships between products in same category"""
        query = """
        MATCH (p1:Product)-[:BELONGS_TO_CATEGORY]->(c:Category)<-[:BELONGS_TO_CATEGORY]-(p2:Product)
        WHERE p1.product_id < p2.product_id  // Avoid duplicates
        AND p1.category_name = p2.category_name
        MERGE (p1)-[:SIMILAR_FUNCTION {
            confidence: 0.6,
            source: 'ai_inference',
            compatibility_type: 'category_similarity',
            created_at: datetime(),
            notes: 'Same category - similar function'
        }]->(p2)
        """
        
        with self.neo4j_conn.session() as session:
            result = session.run(query)
            summary = result.consume()
            logger.info(f"Created {summary.counters.relationships_created} category similarity relationships")
    
    async def _infer_spec_compatibility(self):
        """Infer compatibility based on specifications (basic rules)"""
        # Example: Tools with same voltage are potentially compatible
        query = """
        MATCH (p1:Product), (p2:Product)
        WHERE p1.product_id < p2.product_id
        AND p1.specifications IS NOT NULL 
        AND p2.specifications IS NOT NULL
        AND p1.specifications.voltage = p2.specifications.voltage
        AND p1.specifications.voltage IS NOT NULL
        MERGE (p1)-[:COMPATIBLE_WITH {
            confidence: 0.7,
            source: 'ai_inference',
            compatibility_type: 'voltage_compatibility',
            created_at: datetime(),
            notes: 'Same voltage specification'
        }]->(p2)
        """
        
        with self.neo4j_conn.session() as session:
            result = session.run(query)
            summary = result.consume()
            logger.info(f"Created {summary.counters.relationships_created} specification-based compatibility relationships")
    
    # ===========================================
    # SYNC TRACKING
    # ===========================================
    
    async def _update_sync_status(self, conn, entity_type: str, entity_ids: List[int]):
        """Update sync tracking table"""
        try:
            # Create sync tracking table if it doesn't exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_graph_sync (
                    id SERIAL PRIMARY KEY,
                    entity_type VARCHAR(50) NOT NULL,
                    entity_id VARCHAR(100) NOT NULL,
                    synced_at TIMESTAMP DEFAULT NOW(),
                    sync_version INTEGER DEFAULT 1,
                    UNIQUE(entity_type, entity_id)
                )
            """)
            
            # Insert or update sync records
            for entity_id in entity_ids:
                await conn.execute("""
                    INSERT INTO knowledge_graph_sync (entity_type, entity_id, synced_at)
                    VALUES ($1, $2, NOW())
                    ON CONFLICT (entity_type, entity_id) 
                    DO UPDATE SET synced_at = NOW(), sync_version = knowledge_graph_sync.sync_version + 1
                """, entity_type, str(entity_id))
                
        except Exception as e:
            logger.warning(f"Failed to update sync status: {e}")
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization status"""
        try:
            pool = await self._get_pg_pool()
            async with pool.acquire() as conn:
                # Get sync counts by entity type
                sync_counts = await conn.fetch("""
                    SELECT entity_type, COUNT(*) as synced_count,
                           MAX(synced_at) as last_sync
                    FROM knowledge_graph_sync
                    GROUP BY entity_type
                """)
                
                # Get total counts from PostgreSQL
                total_counts = await conn.fetch("""
                    SELECT 'product' as entity_type, COUNT(*) as total_count
                    FROM products WHERE is_published = true AND status = 'active'
                    UNION ALL
                    SELECT 'category' as entity_type, COUNT(*) as total_count
                    FROM categories WHERE is_active = true
                    UNION ALL
                    SELECT 'brand' as entity_type, COUNT(*) as total_count
                    FROM brands WHERE is_active = true
                """)
                
                # Combine results
                status = {}
                total_dict = {row['entity_type']: row['total_count'] for row in total_counts}
                
                for row in sync_counts:
                    entity_type = row['entity_type']
                    status[entity_type] = {
                        'synced': row['synced_count'],
                        'total': total_dict.get(entity_type, 0),
                        'last_sync': row['last_sync'],
                        'sync_percentage': round(
                            (row['synced_count'] / total_dict.get(entity_type, 1)) * 100, 2
                        )
                    }
                
                # Add Neo4j stats
                neo4j_stats = self.graph_db.get_database_stats()
                status['neo4j_stats'] = neo4j_stats
                
                return status
                
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {}


# Export main class
__all__ = ["PostgreSQLIntegration"]